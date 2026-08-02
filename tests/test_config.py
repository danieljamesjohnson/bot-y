"""Config loading: a bad file must fail at load, loudly, not at 02:00 quietly.

Editing YAML is the whole interface of this tool — "adding a product is editing
a file" is the thing it does better than the projects it replaces. That makes
the loader a trust boundary rather than plumbing. Every hole here has the same
shape: a plausible typo produces a config that loads fine and a monitor that is
broken in a way nothing reports.

- `max_price: "80"` (quoted, which YAML keeps as a string) makes `alertable`
  evaluate `float <= str` and raise, every cycle, from inside the watch loop's
  handler. The unit stays `active (running)` and nothing is ever checked.
- `interval_seconds: 0` makes the jittered sleep zero and turns a polite
  5-minute poll into an uncapped request loop against live retailers.
- An unset `${VAR}` expands to an empty string in silence, which is how a
  monitor ends up with no notifier at all (WR-06) or with the Best Buy path
  quietly degraded.

Each is caught at load, where there is a human present to read the message.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from boty.config import Config

_WATCH = "watches:\n  - name: thing\n    retailer: gamestop\n    target: https://x/1\n"


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "products.yaml"
    path.write_text(text, encoding="utf-8")
    return path


# --------------------------------------------------------------------------
# max_price must be a number
# --------------------------------------------------------------------------


def test_a_quoted_price_is_coerced_rather_than_left_as_a_string(tmp_path: Path) -> None:
    """`target` was coerced with str() and `max_price` was not — an easy miss.

    YAML keeps `max_price: "80"` as a string, and nothing downstream looks at
    the type until `alertable` compares a float against it.
    """
    cfg = Config.load(_write(tmp_path, _WATCH + '    max_price: "80"\n'))

    assert cfg.watches[0].max_price == 80.0
    assert isinstance(cfg.watches[0].max_price, float)


def test_a_price_that_is_not_a_number_is_refused_by_name(tmp_path: Path) -> None:
    """The error has to name the watch, or the operator is hunting blind."""
    with pytest.raises(ValueError, match="max_price"):
        Config.load(_write(tmp_path, _WATCH + "    max_price: cheap\n"))

    with pytest.raises(ValueError, match="thing"):
        Config.load(_write(tmp_path, _WATCH + "    max_price: cheap\n"))


def test_no_price_ceiling_stays_none(tmp_path: Path) -> None:
    """Omitting max_price is legal and means "no ceiling", not "zero"."""
    assert Config.load(_write(tmp_path, _WATCH)).watches[0].max_price is None


# --------------------------------------------------------------------------
# the polling interval must stay polite
# --------------------------------------------------------------------------


def test_a_sub_minute_interval_is_refused(tmp_path: Path) -> None:
    """"Never sub-minute" is a stated non-functional requirement.

    It is also self-protective: hammering a retailer is what gets an IP
    blocked, and a blocked IP takes every detector down at once.
    """
    with pytest.raises(ValueError, match="interval_seconds"):
        Config.load(_write(tmp_path, "settings:\n  interval_seconds: 30\n" + _WATCH))


def test_a_zero_interval_is_refused(tmp_path: Path) -> None:
    """`time.sleep(0 * random.uniform(...))` is 0 — an uncapped request loop."""
    with pytest.raises(ValueError, match="interval_seconds"):
        Config.load(_write(tmp_path, "settings:\n  interval_seconds: 0\n" + _WATCH))


def test_a_negative_interval_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="interval_seconds"):
        Config.load(_write(tmp_path, "settings:\n  interval_seconds: -1\n" + _WATCH))


def test_the_documented_interval_is_accepted(tmp_path: Path) -> None:
    """The shipped config uses 300. The guard must not move the goalposts."""
    cfg = Config.load(_write(tmp_path, "settings:\n  interval_seconds: 300\n" + _WATCH))
    assert cfg.interval_seconds == 300


# --------------------------------------------------------------------------
# an unresolved ${VAR} must be visible
# --------------------------------------------------------------------------


def test_an_unset_variable_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Substituting empty in silence is how a monitor ends up notifying nobody.

    Not an error: an unset ${BESTBUY_API_KEY} is a legitimate state — the key
    is optional and the retailer falls back. But it must be *sayable*, because
    the same silence covers an unset ${BOTY_NOTIFY_URL}, which is not benign.
    """
    monkeypatch.delenv("BOTY_NOTIFY_URL", raising=False)

    with caplog.at_level(logging.WARNING, logger="boty.config"):
        cfg = Config.load(_write(tmp_path, "notify:\n  - ${BOTY_NOTIFY_URL}\n" + _WATCH))

    assert cfg.notify_urls == []
    assert "BOTY_NOTIFY_URL" in caplog.text


def test_a_set_variable_is_substituted_without_complaint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("BOTY_NOTIFY_URL", "tgram://token/chat")

    with caplog.at_level(logging.WARNING, logger="boty.config"):
        cfg = Config.load(_write(tmp_path, "notify:\n  - ${BOTY_NOTIFY_URL}\n" + _WATCH))

    assert cfg.notify_urls == ["tgram://token/chat"]
    assert "BOTY_NOTIFY_URL" not in caplog.text


def test_the_warning_never_prints_the_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """These variables hold bot tokens and API keys. Name them, never echo them."""
    monkeypatch.setenv("BESTBUY_API_KEY", "SUPERSECRETKEY123")

    with caplog.at_level(logging.WARNING, logger="boty.config"):
        Config.load(
            _write(tmp_path, "settings:\n  bestbuy_api_key: ${BESTBUY_API_KEY}\n" + _WATCH)
        )

    assert "SUPERSECRETKEY123" not in caplog.text


# --------------------------------------------------------------------------
# the real config must survive all of the above
# --------------------------------------------------------------------------


def test_the_shipped_config_still_loads() -> None:
    """Validation that rejects the repo's own config is a broken gate."""
    cfg = Config.load(Path(__file__).resolve().parent.parent / "config" / "products.yaml")

    assert cfg.watches, "the shipped config must still produce watches"
    assert cfg.interval_seconds >= 60
    assert all(
        w.max_price is None or isinstance(w.max_price, float) for w in cfg.watches
    )
