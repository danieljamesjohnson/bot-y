"""Command line entry point.

    boty check           -- one pass, print a table, exit (good for cron and for eyeballing)
    boty watch           -- loop forever, notify on transitions (good for systemd)
    boty capture-fixture -- freeze a live retailer page as an offline test fixture
"""

from __future__ import annotations

import argparse
import logging
import random
import sys
import time
from collections.abc import Callable
from pathlib import Path

from .config import Config
from .models import Availability, Extraction, Health, Result, Watch
from .monitor import State, run_once
from .notify import send_health_warning, send_restock
from .pacing import Pacer
from .retailers import (
    check_amazon,
    check_bestbuy_api,
    check_bestbuy_browser,
    check_html,
    check_target_browser,
)
from .status import write as write_status

log = logging.getLogger(__name__)

SYMBOL = {
    Availability.IN_STOCK: "\033[32m●\033[0m",
    Availability.OUT_OF_STOCK: "\033[90m○\033[0m",
    Availability.UNKNOWN: "\033[33m?\033[0m",
}


def _make_checker(cfg: Config) -> Callable[[Watch], Result]:
    """The one place a watch is matched to a transport.

    `scripts/control_check.py` deliberately builds its checker with this same
    function rather than its own: a gate that routed requests differently from
    the running monitor would prove something about a code path nobody runs.
    So this stays one function with one `if`, and there is no registry to fall
    out of sync with it.

    Target has one rung and no fallback at all, which is the opposite case and
    worth stating next to Best Buy's. Its pages ship no structured data, so
    there is nothing for `check_html` to read and no credential that would
    change that — the browser is not an upgrade or a workaround here, it is the
    only transport, and every reading it produces is degraded.

    Best Buy has two rungs and the fallback direction is the interesting part.
    With a key, the official API wins — sanctioned, more reliable, not degraded.
    Without one, the browser reads the page anyway, flagged degraded, and Best
    Buy still works. That ordering is what makes `BESTBUY_API_KEY` an upgrade
    rather than a requirement, which matters because the key needs manual
    approval and rejects free email domains: gating a retailer on it would mean
    a fresh clone of this repo simply cannot watch Best Buy.
    """

    def check(watch: Watch) -> Result:
        if watch.retailer == "bestbuy":
            if cfg.bestbuy_api_key:
                return check_bestbuy_api(watch, cfg.bestbuy_api_key)
            return check_bestbuy_browser(watch, first_party_only=cfg.first_party_only)
        if watch.retailer == "amazon":
            # The same transport `check_html` uses and a different reader, so
            # this arm exists only to opt Amazon into the DOM fallback. Amazon
            # serves its /dp/ page to impersonated HTTP and publishes no
            # structured stock data in it, so `check_html` would read the page
            # perfectly and say UNKNOWN forever — Target's problem at a cheaper
            # rung.
            return check_amazon(watch, first_party_only=cfg.first_party_only)
        if watch.retailer == "target":
            # No credentialed alternative to fall back to, unlike Best Buy: this
            # is the only path Target has. Its page carries no structured data at
            # any rung, so `check_html` would read it perfectly and say UNKNOWN
            # forever.
            return check_target_browser(watch, first_party_only=cfg.first_party_only)
        return check_html(watch, first_party_only=cfg.first_party_only)

    return check


def _store_tag(r: Result) -> str | None:
    """The store, in one tag, or `None` for a watch that has neither.

    Separate from `_report`'s comprehension because that comprehension is
    `(label, bool)` pairs and a store is not a bool — the tag's TEXT depends on
    which of the two values is present, not merely on whether one is.

    Four forms, and the distinction each one buys:

    - `[store X]` — the pin and the page agree. An ordinary label.
    - `[store X, unpinned]` — the page answered and nobody asked for a store, so
      the reading is about whichever location Walmart chose today.
    - `[store ?, pinned X]` — a pin exists and the page did not say. `?` rather
      than a blank, because "the page did not tell us" is a fact worth printing.
    - `[store Y != pinned X]` — they disagree. This is the 2026-08-09 case: the
      daemon read the milk control out of stock at one price while live reads
      minutes later read in stock at another, and nothing on the line could say
      that two different stores had answered.

    Nothing here is a verdict. `SYMBOL` is untouched and still three-membered.
    """
    answered, pinned = r.store, r.watch.store_id
    if answered is None and pinned is None:
        return None
    if answered is None:
        return f"[store ?, pinned {pinned}]"
    if pinned is None:
        return f"[store {answered}, unpinned]"
    if answered != pinned:
        return f"[store {answered} != pinned {pinned}]"
    return f"[store {answered}]"


def _report(results: list[Result], health: list[Health]) -> None:
    for r in results:
        price = f"${r.price:>8.2f}" if r.price is not None else " " * 9
        # Composed rather than chosen: a browser-read control is both things at
        # once, and either fact alone would mislead. `SYMBOL` is deliberately
        # untouched — it is indexed unconditionally below, so it must only ever
        # be keyed by `Availability`, which still has exactly three members.
        #
        # `[degraded]` says discount this reading; `[dom]` says why. They are
        # separate tags because `degraded` now has two disjuncts and a reader
        # looking at one line has no other way to tell which one fired.
        tags = [
            t
            for t, on in (
                ("[control]", r.watch.control),
                ("[degraded]", r.degraded),
                ("[dom]", r.extraction is Extraction.DOM),
            )
            if on
        ]
        # Appended rather than folded into the comprehension above: that one
        # switches a fixed label on a bool, and the store tag's text varies.
        store_tag = _store_tag(r)
        if store_tag is not None:
            tags.append(store_tag)
        tag = f" {' '.join(tags)}" if tags else ""
        print(f"  {SYMBOL[r.availability]} {r.watch.retailer:<9} {r.watch.name[:30]:<30}{price}  {r.detail[:56]}{tag}")

    for h in health:
        if not h.ok:
            print(f"\n  \033[33m! {h.retailer}: {h.reason}\033[0m")
            for c in h.failing_controls:
                print(f"      {c}")


def _capture_fixture(args: argparse.Namespace) -> int:
    """Freeze one live page as a fixture, or refuse and say why.

    A blocked fetch must never become a file on disk: a CAPTCHA interstitial
    saved under a product's name would make the whole test suite assert against
    a bot wall while looking perfectly green.
    """
    from .fetch import Blocked, FetchError
    from .fixtures import capture, meta_path

    try:
        path = capture(args.retailer, args.name, args.url, note=args.note, browser=args.browser)
    except Blocked as exc:
        print(f"blocked: {exc}", file=sys.stderr)
        print("refusing to save a challenge page as a fixture", file=sys.stderr)
        return 1
    except FetchError as exc:
        print(f"fetch failed: {exc}", file=sys.stderr)
        return 1

    print(f"wrote {path} ({path.stat().st_size:,} bytes)")
    print(f"      {meta_path(args.retailer, args.name)}")
    if not args.note:
        print(
            "warning: no --note recorded — a future reader cannot tell what "
            "stock state this page represented",
            file=sys.stderr,
        )
    return 0


#: Consecutive failed cycles before the monitor reports itself broken. Low,
#: because the thing being reported is "nothing is being checked at all".
FAILURES_BEFORE_WARNING = 3

#: Consecutive failed cycles before it stops and exits non-zero. A persistent
#: fault is not something to log forever: the exit code is the only signal a
#: supervisor can act on.
FAILURES_BEFORE_GIVING_UP = 10


def _warn_monitor_is_stuck(cfg: Config, failures: int) -> None:
    """Announce that the loop itself is failing, best-effort.

    Wrapped, because whatever broke the cycle may well have broken
    notification too — and raising from inside the failure handler would
    replace a diagnosable exit with a stack trace from the wrong place.

    THIS ONE STILL PUSHES UNDER THE 2026-08-12 RULE, and it is the one place in
    this file that says so with a stated reason rather than by default. It is
    not an `assess_health` arm and does not reach `watch_cycle`'s filter, so the
    `action` below is not decoration: it is the argument for the send, written
    where somebody auditing the rule will look for it.

    WHY IT SURVIVES THE RULE THAT SILENCED THE OTHERS. A control that stops
    verifying is a thing the operator cannot fix; a loop that has raised three
    times running is a thing only he can, and while it lasts NOTHING reaches him
    — including the restock alert this project exists to send, with a green
    status page over it. The other states are noise because they interrupt for
    no decision; this one is the absence of the channel itself.

    IT IS RARE BY CONSTRUCTION, which is why it is not the noise Dan is
    describing: three consecutive raising cycles, once per episode
    (`test_the_stuck_warning_is_sent_once_not_every_cycle`), not once per poll.
    """
    try:
        send_health_warning(
            cfg.notify_urls,
            [
                Health(
                    retailer="(all)",
                    ok=False,
                    reason=(
                        f"{failures} consecutive check cycles raised — the monitor is "
                        f"running but not monitoring, and the status page is stale"
                    ),
                    action=(
                        "restart boty.service and read the log — nothing is being "
                        "checked and no restock can reach you until it runs again"
                    ),
                )
            ],
        )
    except Exception:
        log.exception("could not send the stuck-monitor warning either")


#: `REFUSALS_BEFORE_PAGING = 5` AND `_refusal_is_entrenched` STOOD HERE UNTIL
#: 2026-08-12, and they are deleted rather than left unreferenced.
#:
#: They answered "when does a refusal deserve a human", and REQ-16's answer was
#: "once it has outlasted the backoff": at five consecutive refusals the interval
#: has already been stretched by 2**N and the retailer is still saying no, which
#: is no longer a rate-limit story. That reasoning is still correct about
#: REACHABILITY and it is no longer a reason to push, because it never named
#: anything to do. Dan cannot make a retailer answer at five refusals any more
#: than at one, and the entrenchment he was being woken for changed only how
#: certain we were of a fact he has no move against.
#:
#: The backoff itself is untouched — `pacing.Pacer` still counts refusals,
#: stretches the interval and persists both — so the response the monitor CAN
#: take by itself is unchanged. What went is the page on top of it.
#:
#: Deleted and not merely unused: a helper named "deserves a human" sitting in
#: the file whose rule is that almost nothing does is a comment that will be
#: believed. `pacing.MAX_PERSISTED_REFUSALS` used to be bound to the constant by
#: a test; that test now binds it to the backoff cap it actually protects.


def watch_cycle(
    cfg: Config,
    checker: Callable[[Watch], Result],
    state: State,
    warned: set[str],
    pacer: Pacer | None = None,
    now: float = 0.0,
) -> set[str]:
    """One poll: check every watch, publish the status, send what is due.

    Extracted from the `while True` below so the loop's behaviour can be tested
    at all. A cycle is the only unit here that has a beginning and an end; the
    loop itself does not terminate, and a bug that only shows up across cycles
    (see `tests/test_restock_replay.py`) cannot be pinned through a function
    that never returns.

    `warned` is which retailers have already been warned about in the current
    failure episode, and the new set is returned rather than mutated so the
    caller holds exactly one copy of that memory. An episode ends when a
    retailer is CHECKED and found no longer pageable — never merely because the
    pacer skipped it, which is a cycle in which we learned nothing about it. See
    the comment at `still_unhealthy` below; that distinction is the difference
    between REQ-16's "pushed once" and "pushed once per check past the cap".
    """
    # monotonic, not time.time(): an NTP correction mid-pass would otherwise
    # publish a negative duration into a file served over HTTP.
    started = time.monotonic()
    results, health, alerts = run_once(
        cfg.watches, checker, state, pacer=pacer, now=now
    )
    # Retailers that exist in the config but were not asked this cycle. Named
    # explicitly so the status page shows six retailers with two paced, rather
    # than four retailers and a silent gap.
    paced = (
        {
            r: pacer.skipped_reason(r, now)
            for r in sorted({w.retailer for w in cfg.watches} - {x.watch.retailer for x in results})
        }
        if pacer is not None
        else None
    )
    write_status(
        cfg.status_path,
        results,
        health,
        duration_seconds=time.monotonic() - started,
        paced=paced,
    )

    # Alerts are edge-triggered, and `run_once` has already committed the
    # transition to `state.seen` and saved it. So a send that does not arrive
    # is not a retry — it is a drop nothing will ever mention again: the next
    # cycle sees the same in-stock reading, finds it already remembered, and
    # stays quiet while the status page shows green. Un-remembering the
    # transition is what converts a lost alert into one more attempt.
    if alerts and not send_restock(cfg.notify_urls, alerts):
        log.error(
            "restock alert NOT delivered for %s — rolling the remembered state "
            "back so the next cycle tries again",
            ", ".join(r.watch.key for r in alerts),
        )
        for r in alerts:
            state.seen.pop(r.watch.key, None)
        state.save()

    # Warn once per retailer per failure episode, not every cycle — and only
    # about a state that names something a person can DO.
    #
    # THE FILTER IS A POSITIVE TEST AND NOT A LIST OF EXCEPTIONS, which is the
    # decision here rather than an implementation of one. Dan, 2026-08-12, the
    # second time he raised it: *"im still getting annoying messages. we need to
    # never hit the user unless its something they can buy or actually do"*. The
    # obvious shape — keep paging everything except the cases we have learned are
    # useless — is exactly what produced that sentence twice. It was `refused`
    # after 2026-08-04's 20 notifications in 24 hours, and it was still loud on
    # 2026-08-12 at 16:49:58 for an Amazon control that did not read IN_STOCK,
    # because a blocklist only ever knows about the noise somebody has already
    # been woken by. Every arm added after it is loud by default.
    #
    # So the default is silence and a push costs a stated reason: `Health.action`
    # is empty unless `assess_health` deliberately fills it, and today exactly one
    # arm can — the store-pin gap, whose remedy is a value only the operator can
    # set. A health arm written next year says nothing until somebody writes down
    # what to do about it, and that is a property of this line rather than of
    # anybody's memory.
    #
    # NOTHING HERE STOPS NOTICING. `unhealthy` is untouched, `write_status` above
    # has already published every state in full, and the loop below records each
    # one it is not pushing. REQ-16's "recording and notifying stay separate" is
    # what makes that a whole answer rather than half of one.
    #
    # WHAT THIS OVERRULES, SAID PLAINLY: REQ-16's second and third clauses — "a
    # refusal that outlasts the cap is pushed once" and "a detector producing a
    # wrong verdict is pushed immediately". Both are now recorded and not pushed.
    # Dan's rule is later and is about the same channel, and the requirement's
    # text is left as it stood at close rather than edited under it.
    unhealthy = [h for h in health if not h.ok]
    pageable = [h for h in unhealthy if h.action]
    for h in unhealthy:
        if not h.action:
            log.info(
                "%s unhealthy, recorded and not pushed — nothing here is a human action: %s",
                h.retailer,
                h.reason,
            )
    fresh = [h for h in pageable if h.retailer not in warned]
    # A retailer the PACER SKIPPED this cycle keeps its memory. `health` is
    # derived from `results`, and `run_once` returns no result at all for a
    # retailer that was not due — deliberately, because a synthetic reading for
    # a question nobody asked is the bug one level up. But that means an
    # un-carried `warned` treats "not checked" as "recovered", and the moment a
    # retailer is entrenched enough to page is exactly the moment the backoff
    # starts skipping it: measured 2026-08-10, the memory survived precisely one
    # cycle and the next paced-out cycle erased it, so a retailer past the cap
    # was re-paged on every subsequent check — 2 pages in 120 cycles, climbing
    # to one every six hours forever at the cap. REQ-16 says such a refusal is
    # pushed ONCE. Only a retailer that was actually CHECKED and is no longer
    # pageable has shown us anything that ends its episode.
    checked = {r.watch.retailer for r in results}
    still_unhealthy = {h.retailer for h in pageable} | (warned - checked)
    if fresh and not send_health_warning(cfg.notify_urls, fresh):
        # Same defect, same fix: marking a retailer as warned on the strength
        # of an attempt rather than a delivery means a broken detector gets
        # reported once, into the void, and never again.
        log.error(
            "detector health warning NOT delivered for %s — will retry next cycle",
            ", ".join(h.retailer for h in fresh),
        )
        return still_unhealthy - {h.retailer for h in fresh}
    return still_unhealthy


def watch_loop(
    cfg: Config,
    checker: Callable[[Watch], Result],
    state: State,
    *,
    cycles: int | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    """Poll forever. `cycles` and `sleep` exist so tests can bound and observe it.

    `cycles=None` is the production behaviour — run until killed. Passing a
    number runs exactly that many polls and returns, which is what lets the
    tests assert on what a *sequence* of cycles does.
    """
    # One pacer for the life of the loop: the backoff is memory, and a pacer
    # rebuilt each cycle would forget every refusal and hammer at full rate.
    #
    # That memory now has to survive the PROCESS as well, and it is loaded once,
    # into this same one pacer, for the same reason — a second construction site
    # is exactly what the invariant above forbids, which is why `load` is an
    # instance method and not a `State`-style classmethod.
    pacer = Pacer(
        default_interval=cfg.interval_seconds,
        overrides=dict(cfg.retailer_intervals),
        state_path=cfg.pacer_state_path,
    )
    # `warned` is restored rather than started empty, and it has to be assigned
    # HERE rather than above, because the pacer it reads through does not exist
    # until the line above. An empty `warned` on a fresh process is precisely how
    # REQ-16's "pushed once" became "pushed once per process".
    warned = pacer.load()
    consecutive_failures = 0
    completed = 0
    # The pacer's clock. Advanced by the delay we ASK for rather than read from
    # time.monotonic(), which is both accurate in production (sleep really does
    # pass that long) and deterministic under a fake sleep in tests — where a
    # wall clock would stay frozen and make every retailer look never-due.
    scheduled_now = 0.0
    while cycles is None or completed < cycles:
        try:
            warned = watch_cycle(cfg, checker, state, warned, pacer=pacer, now=scheduled_now)
            consecutive_failures = 0
        except Exception:
            # Tolerating a transient failure is right — a timeout should not
            # take the service down. Tolerating a permanent one is the exact
            # failure this project exists to eliminate: under systemd the unit
            # stays `active (running)`, the process never exits non-zero, the
            # health-warning call is itself inside this `try` so it never runs,
            # and status.json goes on serving whatever it last held. A stale
            # green dashboard over a monitor that has not checked anything in
            # a week. So: count them, say so out loud, and eventually stop
            # pretending.
            consecutive_failures += 1
            log.exception("check cycle failed (%d in a row); continuing", consecutive_failures)
            if consecutive_failures == FAILURES_BEFORE_WARNING:
                _warn_monitor_is_stuck(cfg, consecutive_failures)
            if consecutive_failures >= FAILURES_BEFORE_GIVING_UP:
                log.error(
                    "giving up after %d consecutive failed cycles — exiting non-zero so "
                    "the supervisor can restart this or mark it failed",
                    consecutive_failures,
                )
                return 1
        finally:
            # ONE WRITE PER CYCLE, not one per `record`. `monitor.run_once` is
            # the precedent — it saves state once at the end of a pass rather
            # than on each mutation — and a cycle is the only unit here with a
            # beginning and an end. Committing `refusals` and `warned` together
            # means the persisted pair can never describe two different cycles.
            #
            # `finally`, not the end of the `try`. The handler above exists
            # because a cycle that raises must not take the service down; a
            # cycle that raises AFTER a refusal was recorded must not lose that
            # refusal either, or the backoff silently shallows every time
            # something goes wrong — which is the moment politeness matters
            # most. It also covers the `return 1` give-up path.
            #
            # `watch_cycle`'s signature is untouched, so its rollback semantics
            # still hold: when a health send fails it returns a REDUCED `warned`,
            # and the reduced set is what reaches disk. An undelivered warning is
            # not remembered as delivered on disk any more than it is in memory.
            pacer.save(warned)

        completed += 1
        # Jitter so we do not hammer on a fixed cadence, which is itself a signal.
        delay = cfg.interval_seconds * random.uniform(0.85, 1.15)
        sleep(delay)
        scheduled_now += delay
    return 0


def _add_shared(p: argparse.ArgumentParser) -> None:
    p.add_argument("-c", "--config", default="config/products.yaml")
    p.add_argument("-v", "--verbose", action="store_true")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="boty", description="Restock monitor that tells you when it breaks.")
    sub = ap.add_subparsers(dest="command", required=True)

    _add_shared(sub.add_parser("check", help="one pass, print a table, exit"))
    _add_shared(sub.add_parser("watch", help="loop forever, notify on transitions"))

    cap = sub.add_parser(
        "capture-fixture",
        help="save a live retailer page as an offline test fixture",
        description=(
            "Fetch a live product page and freeze it under tests/fixtures/ with "
            "capture metadata. Needs no config file."
        ),
    )
    cap.add_argument("retailer", help="retailer key, e.g. gamestop")
    cap.add_argument("name", help="fixture name, e.g. goplusplus")
    cap.add_argument("url", help="product URL to capture")
    cap.add_argument(
        "--note",
        default="",
        help="what stock state this page represented at capture time",
    )
    cap.add_argument(
        "--browser",
        action="store_true",
        help=(
            "capture through a real browser (rung 3) instead of impersonated HTTP. "
            "For retailers that refuse rung 1 outright — without this they could "
            "never be frozen as fixtures at all, so the retailers most in need of "
            "offline regression tests would be the only ones without them. "
            "Needs the optional extra: pip install -e '.[browser]'"
        ),
    )
    cap.add_argument("-v", "--verbose", action="store_true")

    args = ap.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)-7s %(message)s",
    )

    # Capturing a fixture is a standalone tool: it takes a URL directly and has
    # nothing to say about watches, so it must not require a config file.
    if args.command == "capture-fixture":
        return _capture_fixture(args)

    # The default for `-c/--config` is `config/products.yaml`, a REPO-RELATIVE
    # path, and `[tool.setuptools.packages.find] include = ["boty*"]` means
    # `config/` is deliberately not packaged. So on a plain `pip install bot-y`
    # the first command README teaches used to reach `Config.load` with a path
    # that does not exist and die with an uncaught
    # `FileNotFoundError: [Errno 2] No such file or directory:
    # 'config/products.yaml'` — a stack trace naming a directory inside a git
    # checkout, printed to someone who has no checkout. Measured 2026-08-04
    # against a wheel installed into a clean venv and run from /tmp. `make
    # verify` could never have found it: it runs from the repo root, where that
    # path resolves.
    #
    # THE FIX IS NOT TO PACKAGE A DEFAULT CONFIG, and that was considered.
    # `config/products.yaml` is user-supplied by design: which products are
    # watched, at what price, and which control products prove the detector
    # still works are the operator's decisions. Shipping this file would publish
    # this maintainer's own watch list, control choices and pacing overrides to
    # every installer, while teaching a new user that those watches are the
    # tool's rather than their own.
    #
    # The guard sits here rather than inside `Config.load` on purpose: `load`
    # receiving a path that does not exist is a legitimate programming error for
    # every other caller, and swallowing it in the loader would hide it from the
    # tests that use it.
    if not Path(args.config).is_file():
        print(
            f"no config file at {args.config!r} — there is nothing to watch.\n"
            "This package ships no default config on purpose: the products, the price "
            "ceilings and the control products are yours to choose, not this "
            "maintainer's to publish.\n"
            "Copy the example from "
            "https://github.com/danieljamesjohnson/bot-y (config/products.yaml) and point "
            "`-c`/`--config` at your copy.",
            file=sys.stderr,
        )
        return 2

    cfg = Config.load(args.config)
    if not cfg.watches:
        print("no watches configured", file=sys.stderr)
        return 2

    checker = _make_checker(cfg)
    state = State.load(cfg.state_path)

    if args.command == "check":
        # Timed around `run_once` rather than around the process: interpreter
        # startup and config load are not what REQ-08's budget is about, and a
        # number that drifts with Python's import time is not a measurement of
        # retailers. `monotonic` for the reason in `boty.status.write`.
        started = time.monotonic()
        results, health, alerts = run_once(cfg.watches, checker, state)
        elapsed = time.monotonic() - started
        _report(results, health)
        write_status(cfg.status_path, results, health, duration_seconds=elapsed)
        if alerts:
            print(f"\n  {len(alerts)} alertable transition(s)")
        # The human surface for REQ-08's two-minute budget; `duration_seconds`
        # in the status file is the machine one. Both are cheap, and a budget
        # whose only reading lives in a served file is one nobody looks at
        # while watching a pass run.
        retailers = len({w.retailer for w in cfg.watches})
        print(
            f"\n  {len(cfg.watches)} watch{'es' if len(cfg.watches) != 1 else ''} across "
            f"{retailers} retailer{'s' if retailers != 1 else ''} in {elapsed:.1f}s"
        )
        return 0

    # `watch` exists only to notify. With no URLs configured `send_restock`
    # returns False on its first line without logging anything, so the loop
    # would poll forever, find the restock, and tell nobody — outwardly
    # identical to a working monitor. This is easy to arrive at by accident:
    # `notify: [${BOTY_NOTIFY_URL}]` with the variable unset expands to an
    # empty string, which `Config.load` filters out.
    if not cfg.notify_urls:
        print(
            "no notify URLs configured — `watch` would run forever and tell nobody.\n"
            "Set one in the config's `notify:` list (or via ${BOTY_NOTIFY_URL}), "
            "or use `boty check` if you meant to look at this by hand.",
            file=sys.stderr,
        )
        return 2

    print(f"watching {len(cfg.watches)} product(s) every ~{cfg.interval_seconds}s. ctrl-c to stop.")
    return watch_loop(cfg, checker, state)


if __name__ == "__main__":
    raise SystemExit(main())
