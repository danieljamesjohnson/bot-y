#!/usr/bin/env python3
"""Live control-product health, reduced to an exit code.

This is the one check in `make verify` that touches the network, deliberately.
Fixtures prove the code still parses what it used to parse; only a live control
proves the *retailer* has not changed underneath us. Neither substitutes for the
other, and a green test suite says nothing at all about whether bot-y still
works against walmart.com today.

A control is a product chosen because it is always in stock — a grocery staple,
a console that never sells out. So a control reading anything other than
IN_STOCK does not mean the market moved. It means the DETECTOR is suspect.

WHAT THIS DELIBERATELY DOES NOT DO
----------------------------------
It does not call `monitor.run_once`. That function unconditionally calls
`state.save()`, which would rewrite `state.json` with only the control keys and
discard the remembered state of the real products — producing a spurious
duplicate alert on the next real restock, or racing the live `boty.service`
mid-cycle. This script calls the checker directly, per watch, and writes
nothing: not `state.json`, not the status file.

It *does* build that checker with `boty.cli._make_checker`, the same function
`boty watch` uses. A control check that routed requests differently from the
running monitor would prove something about a code path nobody runs.

OFFLINE BEHAVIOUR — a deliberate decision
-----------------------------------------
A check that fails because someone's wifi dropped gets ignored within a week,
and an ignored check is worse than no check. But a check that shrugs off a
retailer refusing us would hide the exact failure it exists to catch. So the
two cases are separated:

- **No connectivity at all** (pre-flight probe to neutral hosts fails): the
  live check is SKIPPED. We learned nothing, and pretending otherwise in either
  direction is a lie.
- **Connectivity present, but a control does not read IN_STOCK** — including a
  fetch failure or a bot wall from the retailer: FAIL. Being blocked by Walmart
  is not an infrastructure hiccup, it is the monitor not working.

`--offline` forces the skip unconditionally, for CI, which has no business
hitting live retailers.

A skip has its OWN exit code (`SKIPPED`, 3) rather than reusing 0. It is not a
failure — nothing was discovered to be wrong — but it is not a pass either, and
returning 0 made the two indistinguishable to a machine: `make verify` printed
"VERIFY: PASS" and exited 0 for a run that verified nothing about any retailer,
while phase success criteria are written as "`make verify` exits 0". The
Makefile translates 3 into a qualified verdict; it stays green, and it says why.
"""

from __future__ import annotations

import argparse
import socket
import sys
import time
from pathlib import Path

# Run from a checkout without installing: make the repo root importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from boty import fixtures  # noqa: E402
from boty.cli import _make_checker  # noqa: E402
from boty.config import Config  # noqa: E402
from boty.models import Availability, Result, Watch  # noqa: E402

#: A fixture older than this is worth a look. It is a warning, never a failure —
#: see `report_fixture_staleness`.
STALE_AFTER_DAYS = 90

#: Exit code for "the live check did not run". Deliberately not 0: nothing was
#: learned, and a caller that cannot tell that apart from a real pass will
#: report a green it has not earned. Not 1 or 2 either — those mean a control
#: failed and the config is wrong respectively, and both are real findings.
SKIPPED = 3

#: Neutral hosts for the connectivity pre-flight. Raw IPs so a broken resolver
#: is caught too, and two providers so one being down is not read as "offline".
_PROBE_TARGETS = (("1.1.1.1", 443), ("8.8.8.8", 443))

#: Details produced by a transport-level failure rather than a parse failure.
#: These are the ones worth one retry: retailers rate-limit intermittently.
_TRANSPORT_PREFIXES = ("fetch failed", "blocked", "api error")


def have_connectivity(timeout: float = 3.0) -> bool:
    """True if this machine can open an outbound TCP connection at all.

    Deliberately does not touch a retailer: the question here is "is the
    network up", and answering it with a request to walmart.com would conflate
    "no internet" with "Walmart blocked us", which are the two cases this whole
    script exists to keep apart.
    """
    for host, port in _PROBE_TARGETS:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            continue
    return False


def _is_transport_failure(result: Result) -> bool:
    return result.detail.lower().startswith(_TRANSPORT_PREFIXES)


def _format(result: Result) -> str:
    price = f"${result.price:.2f}" if result.price is not None else "—"
    return (
        f"  {result.availability.value:<13} {result.watch.retailer:<9} "
        f"{result.watch.name[:34]:<34} {price:>9}  {result.detail[:70]}"
    )


def check_controls(config_path: str, retries: int = 1) -> int:
    """Check every control watch live. Returns a process exit code."""
    cfg = Config.load(config_path)
    controls: list[Watch] = [w for w in cfg.watches if w.control]

    if not controls:
        print(
            f"control check: no control watches in {config_path}.\n"
            "  Every retailer needs at least one product known to be in stock, "
            "or a broken\n  detector is indistinguishable from a drought. "
            "Add `control: true` to a watch.",
            file=sys.stderr,
        )
        return 2

    # Per-retailer, not all-or-nothing. `boty.monitor.assess_health` already
    # implements this rule — "a retailer with no control watch is reported
    # unhealthy" — but this gate never consulted it, so a retailer with product
    # watches and no control was simply invisible: `make verify` went green
    # while that detector had never been verified by anything at all.
    #
    # Checked before any request, because the answer does not depend on what
    # the retailers say today.
    configured = {w.retailer for w in cfg.watches}
    verified = {w.retailer for w in cfg.watches if w.control}
    unverified = sorted(configured - verified)
    if unverified:
        print(
            "control check: FAIL — no control watch for: " + ", ".join(unverified) + "\n"
            "  An unverified detector is treated as a broken one: nothing here can tell\n"
            "  you whether these retailers still parse, so a silent regression in one of\n"
            "  them would look exactly like a drought. Add `control: true` to a watch.",
            file=sys.stderr,
        )
        return 2

    checker = _make_checker(cfg)
    print(f"control check: {len(controls)} control(s), live")

    results: list[Result] = []
    for watch in controls:
        result = checker(watch)
        # One retry, and only for transport failures. A control that parsed
        # cleanly and said OUT_OF_STOCK will say it again; retrying that would
        # just be a slower way to get the same true answer.
        attempts = retries
        while result.availability is Availability.UNKNOWN and _is_transport_failure(result) and attempts > 0:
            attempts -= 1
            print(f"    retrying {watch.retailer}/{watch.name}: {result.detail[:60]}")
            time.sleep(3)
            result = checker(watch)
        results.append(result)
        print(_format(result))

    failing = [r for r in results if r.availability is not Availability.IN_STOCK]
    if not failing:
        print(f"control check: PASS — {len(results)}/{len(results)} controls in stock")
        return 0

    # Order matters when make pipes this: stdout is block-buffered to a pipe
    # while stderr is not, so without this flush the explanation below appears
    # *above* the per-control lines it is explaining.
    sys.stdout.flush()
    print("", file=sys.stderr)
    print(
        f"control check: FAIL — {len(failing)}/{len(results)} control(s) not reading IN_STOCK",
        file=sys.stderr,
    )
    for r in failing:
        print(f"    {r.watch.retailer}/{r.watch.name}: {r.availability.value} — {r.detail}", file=sys.stderr)
    print(
        "\n  This is a statement about the DETECTOR, not about the market.\n"
        "  A control is chosen precisely because it is always in stock — a grocery\n"
        "  staple, a console that never sells out. If one reads OUT_OF_STOCK the\n"
        "  extractor has stopped matching; if it reads UNKNOWN the page shape changed\n"
        "  or the retailer is turning us away. Either way, real restocks are being\n"
        "  missed silently right now.\n"
        "\n  Next: open the URL above in a browser, then re-capture the fixture with\n"
        "  `boty capture-fixture <retailer> <name> <url> --note '<stock state>'` and\n"
        "  see which assertions in tests/ change.",
        file=sys.stderr,
    )
    return 1


def report_fixture_staleness(max_age_days: int = STALE_AFTER_DAYS) -> int:
    """Warn about old or unlabelled fixtures. Always returns 0.

    This warns and does not fail, on purpose. A stale fixture is a prompt to
    re-capture and see whether the expected values changed — and if they did,
    that is a real signal about the retailer rather than a chore. Failing the
    build on age would train people to re-capture blindly on a deadline, which
    converts the signal into noise and leaves the suite asserting against
    whatever the page happens to say today.

    Missing and unparseable sidecars are reported too. An unlabelled fixture is
    a wall of HTML with no record of what stock state it represented, which is
    not much better than no fixture at all.
    """
    pairs = fixtures.list_fixtures()
    if not pairs:
        print(f"fixtures: WARNING — no fixtures found under {fixtures.FIXTURE_ROOT}")
        return 0

    print(f"fixtures: {len(pairs)} fixture(s) under {fixtures.FIXTURE_ROOT}")
    warnings = 0

    for retailer, name in pairs:
        meta = fixtures.metadata(retailer, name)
        age = fixtures.age_days(retailer, name)

        if meta is None:
            sidecar = fixtures.meta_path(retailer, name)
            why = "sidecar missing" if not sidecar.exists() else "sidecar unreadable or not JSON"
            print(
                f"  WARNING  {retailer}/{name}: {why} ({sidecar.name}) —\n"
                "           no record of what stock state this page represented"
            )
            warnings += 1
            continue

        if age is None:
            print(f"  WARNING  {retailer}/{name}: sidecar has no usable captured_at — age unknown")
            warnings += 1
            continue

        if age > max_age_days:
            print(
                f"  WARNING  {retailer}/{name}: captured {age:.0f} days ago "
                f"(over {max_age_days}) — re-capture and see whether the expected values moved"
            )
            warnings += 1
            continue

        note = str(meta.get("note") or "").strip()
        if not note:
            print(f"  WARNING  {retailer}/{name}: no capture note — the stock state it represents is unrecorded")
            warnings += 1
            continue

        print(f"  ok       {retailer}/{name}: {age:.0f}d — {note[:60]}")

    if warnings:
        print(f"fixtures: {warnings} warning(s) — not a failure, but worth a look")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="control_check",
        description="Live control-product health as an exit code.",
    )
    ap.add_argument("-c", "--config", default="config/products.yaml")
    ap.add_argument(
        "--offline",
        action="store_true",
        help="skip the live check entirely and exit 0 (for CI, which should not hit retailers)",
    )
    ap.add_argument(
        "--fixtures",
        action="store_true",
        help="report stale or unlabelled fixtures instead; warns, never fails",
    )
    ap.add_argument(
        "--max-age-days",
        type=int,
        default=STALE_AFTER_DAYS,
        help=f"fixture age that triggers a warning (default {STALE_AFTER_DAYS})",
    )
    args = ap.parse_args(argv)

    if args.fixtures:
        return report_fixture_staleness(args.max_age_days)

    if args.offline:
        print("control check: SKIPPED (--offline) — no live retailer request made.")
        print("  Nothing here says the retailers still work. Run `make controls` on a")
        print("  networked machine before trusting a green run.")
        return SKIPPED

    if not have_connectivity():
        print("control check: SKIPPED — no outbound connectivity from this machine.")
        print("  This is not a pass. The live controls are the only check that can tell")
        print("  you a retailer changed its page; nothing was learned about them here.")
        return SKIPPED

    return check_controls(args.config)


if __name__ == "__main__":
    raise SystemExit(main())
