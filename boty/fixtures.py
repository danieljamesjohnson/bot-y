"""Frozen copies of real retailer pages, and the tooling to capture them.

A test that hits a live retailer is not a test. It fails when the site is slow,
it hammers someone else's servers, it cannot run in CI, and — worst — it goes
red for reasons that have nothing to do with the change under review. So the
extraction layer is tested against saved HTML instead.

The division of labour matters and is easy to get wrong:

- **Fixtures** catch *code* regressions. Did a change to the parser break an
  extractor that used to work? Offline, deterministic, frozen on purpose.
- **Live control products** catch *reality*. Did the retailer change its page?

Neither substitutes for the other. Green fixtures say nothing at all about
whether a retailer still works, which is why every fixture carries the date it
was captured and a note describing the stock state it represented. A reader six
months from now needs to be able to tell whether the snapshot still means
anything.

Importing this module must never be able to reach the network: `boty.fetch` is
imported lazily inside `capture()` so that tests, which only ever call `load()`,
have no path to an outbound request.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_PACKAGE_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PACKAGE_DIR.parent


def _default_root() -> Path:
    """Where fixtures live.

    Anchored to the repo rather than the working directory: pytest and `make`
    can both be invoked from a subdirectory, and a cwd-relative path would make
    `load()` succeed or fail depending on where you happened to be standing.
    Falls back to the plain relative path when the package is installed outside
    a checkout (no repo to anchor to), and is overridable for tooling.
    """
    override = os.environ.get("BOTY_FIXTURE_ROOT")
    if override:
        return Path(override)
    if (_REPO_ROOT / "pyproject.toml").is_file():
        return _REPO_ROOT / "tests" / "fixtures"
    return Path("tests/fixtures")


#: Root of the fixture tree: ``<root>/<retailer>/<name>.html`` plus a
#: ``.json`` sidecar of capture metadata alongside each one.
FIXTURE_ROOT: Path = _default_root()


def html_path(retailer: str, name: str) -> Path:
    """Path to a fixture's saved HTML, whether or not it exists."""
    return FIXTURE_ROOT / retailer / f"{name}.html"


def meta_path(retailer: str, name: str) -> Path:
    """Path to a fixture's capture-metadata sidecar."""
    return FIXTURE_ROOT / retailer / f"{name}.json"


def capture(retailer: str, name: str, url: str, note: str = "", browser: bool = False) -> Path:
    """Fetch `url` live and freeze it as a fixture. Returns the HTML path.

    `note` records what stock state the page represented at capture time — a
    fixture without one is a wall of HTML nobody can interpret later.

    `browser=True` captures through rung 3 (a real browser) instead of rung 1
    (impersonated HTTP). Without it, a retailer that refuses rung 1 outright
    could never be frozen as a fixture at all — which would mean the retailers
    that most need offline regression tests are exactly the ones that cannot
    have them. Note that a rung-3 capture is a snapshot of *rendered* DOM, so
    the sidecar's byte count will not match what curl would have seen.

    `Blocked` and `FetchError` propagate deliberately, on both paths. A capture
    that swallowed them would write a CAPTCHA interstitial to disk under a
    product's name and poison every test that reads it, which is the exact
    silent failure this project exists to prevent.
    """
    # Imported here, not at module scope, so that merely importing this module
    # (as the test suite does) cannot reach the network. `boty.browser` is lazy
    # for a second reason too: it is behind an optional extra, so a contributor
    # without `bot-y[browser]` must still be able to import this module.
    if browser:
        from . import browser as browser_transport

        page = browser_transport.fetch_rendered(url)
    else:
        from . import fetch

        page = fetch.get(url)

    target = html_path(retailer, name)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page.text, encoding="utf-8")

    meta = {
        "url": url,
        "retailer": retailer,
        "name": name,
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "status": page.status,
        "bytes": len(page.text.encode("utf-8")),
        "note": note,
        # Which rung of the escalation ladder produced this. A rendered capture
        # is a different artefact from an HTTP one — its `status` is always 200
        # because a browser has no response code to report — and a reader six
        # months from now cannot tell them apart by looking at the HTML.
        "transport": "browser" if browser else "http",
    }
    meta_path(retailer, name).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    return target


def load(retailer: str, name: str) -> str:
    """Return a fixture's HTML. No network, ever."""
    path = html_path(retailer, name)
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"no fixture at {path} — capture it with: "
            f"boty capture-fixture {retailer} {name} <url> --note '<stock state>'"
        ) from exc


def metadata(retailer: str, name: str) -> dict[str, Any] | None:
    """Return a fixture's capture metadata, or None if missing/unreadable."""
    try:
        raw = meta_path(retailer, name).read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return loaded if isinstance(loaded, dict) else None


def age_days(retailer: str, name: str) -> float | None:
    """Days since capture, or None if that cannot be established.

    None means "unknown", not "fresh" — callers should treat it as a reason to
    look, the same way an unparseable page is UNKNOWN rather than out-of-stock.
    """
    meta = metadata(retailer, name)
    if not meta:
        return None
    stamp = meta.get("captured_at")
    if not isinstance(stamp, str):
        return None
    try:
        captured = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    if captured.tzinfo is None:
        captured = captured.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - captured).total_seconds() / 86400.0


def list_fixtures() -> list[tuple[str, str]]:
    """Every (retailer, name) pair on disk, sorted."""
    return sorted((p.parent.name, p.stem) for p in FIXTURE_ROOT.glob("*/*.html"))
