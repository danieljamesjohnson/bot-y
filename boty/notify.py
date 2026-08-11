"""Notifications, via Apprise.

Apprise speaks Telegram, ntfy, Discord, Slack, email and ~100 others through
one URL syntax, so bot-y does not implement any of them:

    tgram://<bot-token>/<chat-id>
    ntfy://<topic>
    discord://<webhook-id>/<webhook-token>

Tokens come from the environment or the config file, never from source.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from .models import Health, Result, established_shipping

log = logging.getLogger(__name__)

#: The one spelling of a field nobody read, in one constant, for the reason
#: `monitor.CAUSE_UNKNOWN` records: a property stated three ways cannot be
#: checked mechanically at all, and three paraphrases drift — which is how the
#: two withdrawn sentences in `monitor.py` came to be wrong in the first place.
#: `tests/test_alert_text.py` counts occurrences of THIS value rather than
#: matching prose.
FIELD_UNKNOWN = "unknown"

#: `store '00000'` / `store "00000"` — the shape `retailers._verdict_from_html`'s
#: mismatch guard writes. It renders both numbers with `!r`, and `repr` switches
#: to double quotes when the value contains a single one, so both delimiters are
#: matched rather than the one that happens to be usual.
#:
#: Deliberately keyed on the CARRIER and not on "any run of digits". This body
#: also carries SKUs, HTTP statuses, prices and refusal counts, all of which are
#: the diagnosis somebody is being paged to read; a blanket digit filter would
#: buy the redaction by making the alert useless, which is how a redaction gets
#: removed six months later.
_STORE_NUM_RE = re.compile(r"store (['\"])(?:(?!\1).)*\1")


def _redact_store_numbers(text: str) -> str:
    """Strip store numbers out of text on its way to a third-party transport.

    A store number is a geolocator: it resolves publicly to one street address.
    `config/products.yaml` refuses to hold one even as a commented example,
    `config._store_id`'s docstring says why, and `3bd1663` force-rewrote 170
    commits of this repo's history to remove exactly this class of value. Then
    the mismatch guard's `detail` — which names BOTH the answering store and the
    pinned one — reached `Health.failing_controls` and was joined into the push
    body unredacted. The documented transports include `ntfy://<topic>`, which
    is world-readable unless auth is configured, plus `discord://` and
    `tgram://` webhooks.

    THE CUT IS HERE AND NOT UPSTREAM, on purpose. `Result.detail` stays fully
    diagnostic for the surfaces that are ours — the terminal, journald and the
    gitignored `status.json` behind the tailnet — because the operator does need
    to know which store answered. What leaves the machine is the FACT that the
    store disagreed, which is the actionable half; the digits are read off the
    dashboard.

    This is the module's own existing standard, not a new one:
    `retailers._redact_host_paths` exists so a home directory cannot reach a
    `Result`, and `check_bestbuy_api` redacts its key out of exception text. The
    omission here was inconsistent with that, not with an absent rule.

    NOT A DIAGNOSIS, so `send_health_warning`'s standing prohibition is intact:
    this removes a value, it does not add a sentence, and it cannot make the
    alert claim anything `assess_health` did not.
    """
    return _STORE_NUM_RE.sub("store <redacted>", text)


def _client(urls: list[str]) -> Any | None:
    """An Apprise instance, or None if apprise is missing.

    Typed `Any` because apprise ships no stubs — see the ignore_missing_imports
    override in pyproject.toml.
    """
    try:
        import apprise
    except ImportError:  # pragma: no cover
        log.error("apprise not installed — run: pip install apprise")
        return None
    client = apprise.Apprise()
    for url in urls:
        if not client.add(url):
            log.error("apprise rejected notification url: %s", url.split("://")[0] + "://…")
    return client


def _field(value: float | None) -> str:
    """A two-decimal dollar figure, or the one word for "nobody read this".

    ONE FORMATTER FOR BOTH FIELDS, so price and shipping cannot drift into
    different shapes. That is the whole content of the format Dan asked for:
    two fields, each showing its own actual state, in the same shape either way.
    """
    return f"${value:.2f}" if value is not None else FIELD_UNKNOWN


def send_restock(urls: list[str], results: list[Result]) -> bool:
    """Alert that something is buyable: the two fields, and a direct link.

    THE BODY CARRIES `price:` AND `shipping:` AS TWO SEPARATE FIELDS, in the
    shape Dan asked for on 2026-08-11 — *"Instead of 'unverified', why don't you
    say price: <price> shipping: <unknown>"* — and in the same shape whether or
    not shipping resolved. This is the mitigation for the hole his other
    decision of that date reopened: where no shipping cost could be read the
    alert now goes out, so the unread cost has to be VISIBLE at the moment
    somebody decides to click, rather than explained afterwards.

    NO DELIVERED TOTAL IS STATED, in either case, and that is not an omission.
    You cannot add a number to `unknown`, so where shipping is unknown there is
    nothing to total and nothing is claimed; and where it is known, both addends
    are already on the screen. A total that appeared in one case and vanished in
    the other would be exactly the special-casing this format avoids.

    THE SHIPPING FIGURE IS READ THROUGH `models.established_shipping`, NEVER OFF
    `r.shipping`. A negative cost is one the code has already refused to trust —
    `delivered_total` is `None` for it — and printing `$-5.00` would put a
    figure on a phone that no decision here would accept. Reading
    `delivered_total is None` instead would be wrong the other way: a reading
    with an unreadable price and a perfectly good $6.99 shipping cost would
    report `shipping: unknown` about a number that WAS measured. Three consumers
    ask one question; the predicate is the answer.

    THIS FUNCTION STILL COMPOSES NO DIAGNOSIS OF ITS OWN, the standing
    prohibition `send_health_warning` records. Rendering a field and its actual
    state subtracts a claim rather than adding one — the same standard
    `_redact_store_numbers` meets — and it cannot make this body assert
    something the reading did not.

    THE `"price unknown"` PROSE THIS USED TO WRITE IS WITHDRAWN in favour of the
    field vocabulary. `models.Result.alertable`'s comment cited that exact
    string as the reason an unreadable price must not clear a ceiling; it was
    rewritten in the same commit, and the refusal it argued for is still there.

    A TRANSPORT THAT COLLAPSES RUNS OF WHITESPACE will render the two fields one
    space apart. That is still both fields, still labelled, still legible — the
    shape survives collapsing, which is why the separator carries no meaning of
    its own.
    """
    if not urls or not results:
        return False
    client = _client(urls)
    if client is None:
        return False

    lines: list[str] = []
    for r in results:
        lines.append(
            f"{r.watch.name} at {r.watch.retailer}\n"
            f"price: {_field(r.price)}   shipping: {_field(established_shipping(r.shipping))}\n"
            f"{r.url}"
        )
    body = "\n\n".join(lines)
    title = f"IN STOCK: {results[0].watch.name}" if len(results) == 1 else f"IN STOCK: {len(results)} items"
    log.info("sending restock alert: %s", title)
    return bool(client.notify(title=title, body=body))


def send_health_warning(urls: list[str], unhealthy: list[Health]) -> bool:
    """Alert that one or more retailers are no longer verified.

    Deliberately as loud as a restock alert. A monitor you wrongly believe is
    working is worse than one you know is down.

    THIS FUNCTION COMPOSES NO DIAGNOSIS OF ITS OWN, and must not start. The body
    is `h.reason` plus `h.failing_controls` — `monitor.assess_health` is the one
    place that decides what a failure may be said to mean, and a second opinion
    written here would be unreachable by the gate that checks it. The one
    transformation applied is `_redact_store_numbers`, which SUBTRACTS a
    geolocator and adds nothing: it cannot make this body claim a cause, so the
    prohibition above is intact. It used to say "verbatim", and that word is
    withdrawn rather than quietly falsified — see that function's docstring.
    Until 2026-08-10 the exception was the hardcoded title, `"bot-y: detector
    problem (N retailer(s))"`, which asserted a problem with the detector over a
    body that might be saying the detector was never reached — the same defect as
    the two withdrawn sentences in `monitor.py`, on the one surface a phone
    actually shows. Withdrawn under REQ-15. What `ok=False` establishes is stated
    by `assess_health`'s own docstring — "not because anything is known to be
    broken, but because nothing is known at all" — so the measured word is
    UNVERIFIED. The count stays, because the count is measured.
    """
    if not urls or not unhealthy:
        return False
    client = _client(urls)
    if client is None:
        return False

    lines: list[str] = []
    for h in unhealthy:
        # BOTH joins go through the filter. `reason` carries no store number
        # today and `failing_controls` does, but which of the two holds it is a
        # fact about `assess_health`'s current prose — the thing this file is
        # least entitled to assume, and the thing most likely to be edited.
        lines.append(f"[{h.retailer}] {_redact_store_numbers(h.reason)}")
        lines.extend(f"  • {_redact_store_numbers(c)}" for c in h.failing_controls)
    log.warning("sending health warning for: %s", ", ".join(h.retailer for h in unhealthy))
    return bool(
        client.notify(
            title=f"bot-y: {len(unhealthy)} retailer(s) unverified",
            body="\n".join(lines),
        )
    )
