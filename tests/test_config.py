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
# store_id: a per-watch pin with NO default
# --------------------------------------------------------------------------
#
# Every store value in this file comes from this repo's redaction vocabulary —
# `0` and `00000` — and that is a rule, not a coincidence. `config/products.yaml`
# and this file are both tracked and public, and a store number is a geolocator
# that resolves to one street address. Measured 2026-08-10: a four-digit store
# number written into a tracked test file as a JSON `storeId` or `store` value
# trips the identity guard — this comment paragraph tripped it on its own first
# draft, which is the gate working — while `store_id: "0"` and
# `store_id: "00000"` are clean under the new config-key rule as well as the old
# ones, because `value.strip("0.- ")` drops them. If a test here ever trips the
# guard, change the literal. NEVER add a value to the guard's allow-list, which
# is the mutation `test_the_allow_list_cannot_absorb_a_real_value` exists to
# catch.


def test_an_unquoted_store_id_is_refused_because_yaml_has_already_changed_it(
    tmp_path: Path,
) -> None:
    """REVERSED 2026-08-10 by 05-REVIEW WR-03. This test used to assert the opposite.

    It read `test_a_yaml_integer_store_id_is_coerced_to_a_string`, and its
    argument was right as far as it went: the store this phase compares against
    is read out of Walmart's own JSON, where it is a string, so an `int` from the
    config against a `str` from the page is a never-match with no exception and
    no log line. `str()` fixed that.

    What it missed is that PyYAML has already finished with the value before
    `_store_id` is called. Measured 2026-08-10, described rather than quoted
    because the identity gate's config-key rule catches its own examples:

        a leading zero      ->  resolved as OCTAL, so the digits change
        an underscore       ->  a digit separator, silently dropped
        a colon             ->  resolved as sexagesimal

    The failure is in the safe direction — the
    pin never matches, so the reading is UNKNOWN — but it is silent, and the
    diagnosis it produces is actively misleading: the alert says the watch pins
    one number for a file that plainly says another, and nothing anywhere shows
    the transformation. The old docstring made exactly this argument for the
    `str()` coercion and then stopped one step short of the value YAML mangled
    on the way in.

    So the coercion's goal is kept and its method is replaced: refusing a
    non-string forces the quoted form, which makes the YAML resolver irrelevant.
    It also cannot be reached by anyone following the documentation — the shipped
    config says `store_id: ${WALMART_STORE_ID}` and `${VAR}` substitution always
    produces a `str` — and a literal store number in a tracked file is the leak
    class the identity gate refuses anyway.
    """
    with pytest.raises(ValueError, match="quoted"):
        Config.load(_write(tmp_path, _WATCH + "    store_id: 0\n"))


def test_the_refusal_names_octal_because_that_is_the_case_nobody_would_guess(
    tmp_path: Path,
) -> None:
    """A message that says "must be quoted" without saying why gets worked around.

    The leading-zero case is the one that silently changes the value rather than
    merely its type, so it is the one the message spells out.
    """
    with pytest.raises(ValueError, match="OCTAL"):
        Config.load(_write(tmp_path, _WATCH + "    store_id: 0\n"))


def test_the_documented_forms_are_unaffected(tmp_path: Path) -> None:
    """The positive half: the refusal must not reach the way people are told to write it.

    `${WALMART_STORE_ID}` substitutes to a `str` before any `Watch` is built, and
    a quoted literal is a `str` by construction. If either of these raised, the
    only way to keep a working config would be to weaken the check.
    """
    monkeypatched = _write(tmp_path, _WATCH + '    store_id: "00000"\n')
    assert Config.load(monkeypatched).watches[0].store_id == "00000"


def test_a_quoted_store_id_is_the_same_string(tmp_path: Path) -> None:
    """Both YAML spellings have to land on the same value, or the pin is a coin flip."""
    cfg = Config.load(_write(tmp_path, _WATCH + '    store_id: "00000"\n'))

    assert cfg.watches[0].store_id == "00000"


def test_no_store_pin_loads_and_is_none(tmp_path: Path) -> None:
    """An absent pin LOADS. It does not raise, and that split is deliberate.

    `_price` and `_interval` refuse the whole file; `_sub` logs and continues.
    This needs the second, because refusing would take down five healthy
    retailers over one Walmart watch — and the phase criterion for an unpinned
    store is UNKNOWN plus a health message, which needs a daemon that is still
    running to deliver it.

    `None` is a third state beside "your store" and "someone else's store", and
    it must not collapse into either.
    """
    cfg = Config.load(_write(tmp_path, _WATCH))

    assert cfg.watches[0].store_id is None


def test_an_unset_store_variable_loads_unpinned_rather_than_raising(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The shipped config says `store_id: ${WALMART_STORE_ID}`.

    The real number lives in the daemon's mode-600 EnvironmentFile, outside this
    public repo. Unset, `_sub` expands it to empty and says which name it was —
    and the watch is then unpinned, which degrades to UNKNOWN. That is the
    behaviour REQ-14 asks for anyway, which is what makes the indirection safe
    rather than merely convenient.
    """
    monkeypatch.delenv("WALMART_STORE_ID", raising=False)

    with caplog.at_level(logging.WARNING, logger="boty.config"):
        cfg = Config.load(_write(tmp_path, _WATCH + "    store_id: ${WALMART_STORE_ID}\n"))

    assert cfg.watches[0].store_id is None
    assert "WALMART_STORE_ID" in caplog.text


def test_a_set_store_variable_pins_the_watch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("WALMART_STORE_ID", "00000")

    cfg = Config.load(_write(tmp_path, _WATCH + "    store_id: ${WALMART_STORE_ID}\n"))

    assert cfg.watches[0].store_id == "00000"


def test_a_boolean_store_id_is_refused_by_name(tmp_path: Path) -> None:
    """`store_id: true` is a typo, exactly as `max_price: true` is.

    `bool` is an `int` subclass, so `str(True)` would sail through as the
    perfectly plausible pin `"True"` and never match anything. An ABSENCE is a
    legitimate state; a TYPO is a mistake, and the two get opposite treatment
    here on `_price`'s precedent.
    """
    with pytest.raises(ValueError, match="store_id"):
        Config.load(_write(tmp_path, _WATCH + "    store_id: true\n"))

    with pytest.raises(ValueError, match="thing"):
        Config.load(_write(tmp_path, _WATCH + "    store_id: true\n"))


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


def test_a_retailer_override_below_the_global_interval_is_refused(tmp_path: Path) -> None:
    """An override is for asking LESS often. Below the global it is unkeepable.

    `_retailer_intervals`' own docstring stated the intent — *"A per-retailer
    override is for asking LESS often"* — and held the value only to
    `MIN_INTERVAL_SECONDS`. `watch_loop` sleeps `interval_seconds *
    uniform(0.85, 1.15)` per CYCLE, so no retailer can be polled more often than
    roughly the global interval however small its override.

    Measured on the tree before this guard existed:

        config accepted: interval_seconds=3600, retailer_intervals={'gamestop': 900}
        published cadence for gamestop: 900
        real gap between polls: >= ~3060 s

    A published threshold the schedule can never satisfy, and it fails in the
    direction that paints the rendering wrong: `status.write` publishes 900 as
    `current_interval_seconds`, so every GameStop row on the dashboard and in
    `boty check` renders `warn`/stale permanently while the monitor is reading
    that watch as often as it possibly can. The phase's stated invariant is that
    the displayed cadence and the interval actually used to schedule cannot
    drift; here they drift by 3.4x on a config the loader accepted in silence.
    """
    with pytest.raises(ValueError, match="retailer_intervals"):
        Config.load(
            _write(
                tmp_path,
                "settings:\n  interval_seconds: 3600\n"
                "  retailer_intervals:\n    gamestop: 900\n" + _WATCH,
            )
        )


def test_a_retailer_override_at_or_above_the_global_interval_is_accepted(
    tmp_path: Path,
) -> None:
    """The shipped config's own two overrides, and the boundary between them.

    `config/products.yaml` carries `amazon: 1800` and `gamestop: 900` against a
    global 300, so a guard that moved the goalposts would refuse the file this
    project ships. EQUAL is accepted deliberately: an override equal to the
    global asks exactly as often as the loop can manage, which is keepable — the
    refusal is only for a cadence the schedule cannot reach.
    """
    cfg = Config.load(
        _write(
            tmp_path,
            "settings:\n  interval_seconds: 300\n"
            "  retailer_intervals:\n    amazon: 1800\n    gamestop: 900\n"
            "    walmart: 300\n" + _WATCH,
        )
    )
    assert cfg.retailer_intervals == {"amazon": 1800, "gamestop": 900, "walmart": 300}


# --------------------------------------------------------------------------
# where the runtime files land
# --------------------------------------------------------------------------


def test_the_pacer_state_path_has_a_default(tmp_path: Path) -> None:
    """A setting nobody has to set. The daemon must persist its backoff anyway.

    Every deployment that predates this key has no line for it, and a monitor
    that silently stopped remembering its backoff because a setting was absent
    would be the in-memory regression rebuilt as a config default.
    """
    cfg = Config.load(_write(tmp_path, _WATCH))

    assert cfg.pacer_state_path == Path("pacer-state.json")


def test_the_pacer_state_path_can_be_set(tmp_path: Path) -> None:
    cfg = Config.load(
        _write(tmp_path, f"settings:\n  pacer_state_path: {tmp_path / 'p.json'}\n" + _WATCH)
    )

    assert cfg.pacer_state_path == tmp_path / "p.json"


def test_the_state_paths_are_three_separate_files(tmp_path: Path) -> None:
    """`state.json` was rejected as a home for this, and the reason is structural.

    ONE OF THE TWO REASONS WAS OVERTAKEN ON 2026-08-13 and the decision was not.
    This docstring used to read: *"Its whole document is `State.seen`
    (`monitor.py` parses the entire file as that map), so a second top-level key
    there is a schema change with a migration behind it."* REQ-21 gave that
    document a reading time per entry, so it is a map of entries rather than the
    `seen` map, and the migration that objection warned about has since been done
    per entry. Half-spent, exactly as `config.py`'s comment now records it.

    The surviving reason is decisive on its own: `run_once` saves `state.json`
    BEFORE delivery is attempted, which is exactly the wrong moment to commit a
    paging memory whose only job is to be rolled back when a delivery fails.

    The assertion below is unchanged — three paths are still three paths.
    """
    cfg = Config.load(_write(tmp_path, _WATCH))

    assert len({cfg.state_path, cfg.status_path, cfg.pacer_state_path}) == 3


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
    # A store pin is a string or it is absent — never an int, never "". The
    # shipped file substitutes ${WALMART_STORE_ID}, which is unset in CI and in
    # a fresh clone, so this passes both pinned and unpinned by construction.
    assert all(
        w.store_id is None or (isinstance(w.store_id, str) and w.store_id)
        for w in cfg.watches
    )


_GITIGNORE = Path(__file__).resolve().parent.parent / ".gitignore"


@pytest.mark.skipif(
    not _GITIGNORE.is_file(),
    reason=(
        "no .gitignore here, so this is the mutation sandbox — which deliberately "
        "does not copy one (scripts/mutation_check.py's _IGNORE comment argues the "
        "rejection at length). This rule is about THIS repository's tracked surface, "
        "which a copy genuinely has nothing to say about, so it skips on "
        "tests/test_identity_check.py's `needs_repo` precedent rather than being "
        "bought green by widening SANDBOX_CONTENTS."
    ),
)
def test_the_default_pacer_state_file_is_gitignored() -> None:
    """A new basename inherits nothing from the `state.json` line (T-05-16).

    `.gitignore` matches basenames literally, so `state.json` does not cover
    `pacer-state.json`: without its own line the first `boty watch` on a
    developer's machine offers the file for commit. Not a leak — it holds
    retailer names already public in this same config and integers — but an
    untracked runtime artifact sitting in `git status` is how an unrelated
    change gets committed by accident beside it.
    """
    root = Path(__file__).resolve().parent.parent
    ignored = _GITIGNORE.read_text(encoding="utf-8").splitlines()
    default = Config.load(root / "config" / "products.yaml").pacer_state_path

    assert default.name in [line.strip() for line in ignored], (
        f"{default.name} has no .gitignore line of its own"
    )


# --------------------------------------------------------------------------
# retailer: is a key the whole system branches on, so it is validated
# --------------------------------------------------------------------------


def test_a_capitalised_retailer_is_refused_rather_than_silently_unguarded(
    tmp_path: Path,
) -> None:
    """One capital letter used to switch off both of the store guards.

    Every consumer compares this string case-sensitively — `_make_checker`'s
    `== "bestbuy" / "amazon" / "target"`, `retailers.MARKETPLACES`, and
    `watch.retailer in models.STORE_SCOPED`. An unrecognised value falls through
    `_make_checker` to `check_html`, which is the CORRECT transport for Walmart,
    so `retailer: Walmart` reaches Walmart's real page, parses it perfectly, and
    skips the store guard and `_is_store_gap` together.

    Measured 2026-08-10 against `tests/fixtures/walmart/milk-control.html` and
    the tree at bb6d418:

        first_party_only=True   walmart  -> unknown    price=None
        first_party_only=True   Walmart  -> unknown    price=None
        first_party_only=False  walmart  -> unknown    price=None
        first_party_only=False  Walmart  -> in_stock   price=2.42

    A price and an availability from a store nobody pinned, published as a
    verdict, with the dashboard green — the exact 2026-08-09 failure the phase
    exists to prevent, reachable by a plausible YAML typo that nothing warned
    about. (With the shipped `first_party_only: true` the same typo reads
    UNKNOWN instead — but only because `Walmart` is absent from `FIRST_PARTY`
    too, which is luck rather than a guard, and the message it produces sends
    the reader to debug a seller list.)

    REFUSED and not normalised, deliberately. Lower-casing would also close the
    hole, and it would do it by accepting a spelling that no longer matches
    anything the code says — a config file and a code constant agreeing only
    after a transformation nobody can see. This project's whole value is that a
    reading you cannot trust must not look like one you can, and the same
    applies to the file that produces it. The error names the exact spelling to
    write.
    """
    with pytest.raises(ValueError, match="retailer"):
        Config.load(
            _write(tmp_path, "watches:\n  - name: thing\n    retailer: Walmart\n    target: https://x/1\n")
        )


@pytest.mark.parametrize("spelling", ["Walmart", "WALMART", "walmart ", " walmart", "GameStop"])
def test_every_case_and_whitespace_variant_is_refused(tmp_path: Path, spelling: str) -> None:
    """The class, not the one instance.

    `GameStop` is here because it is how the retailer writes its own name, so it
    is the spelling an operator copying from the site would type; the trailing
    and leading space forms are what a hand-edited YAML file grows.
    """
    with pytest.raises(ValueError):
        Config.load(
            _write(
                tmp_path,
                f'watches:\n  - name: thing\n    retailer: "{spelling}"\n    target: https://x/1\n',
            )
        )


def test_the_error_names_the_spelling_to_write_instead(tmp_path: Path) -> None:
    """A refusal that does not say what to write instead is a puzzle, not a message."""
    with pytest.raises(ValueError, match="'walmart'"):
        Config.load(
            _write(tmp_path, "watches:\n  - name: thing\n    retailer: Walmart\n    target: https://x/1\n")
        )


def test_a_retailer_this_build_cannot_check_loads_but_says_so_loudly(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """The residual, recorded so the gate is not trusted past it.

    `walmrt` is not a miscased `walmart` — it is a name this build has no
    adapter and no seller list for. Measured 2026-08-10, it is dangerous in
    exactly the same way as `Walmart` when `first_party_only: false`:

        first_party_only=True   walmrt   -> unknown    price=None
        first_party_only=False  walmrt   -> in_stock   price=2.42

    It is nonetheless LOADED, and that is a constraint rather than an oversight.
    `scripts/evidence_check.py` has two rules that require such a watch to be
    constructible: rule 1 catches a retailer configured but outside the
    ROADMAP's Retailer Scope table, and its own test case is a `microcenter`
    watch with no adapter at all; rule 5 catches a retailer configured while the
    evidence file still records it REFUSED, and its test case is
    `pokemoncenter`, whose docstring says a blanket ban would make "the outcome
    this whole phase is walking towards — a refused retailer re-probed, reached,
    and shipped — unrepresentable". Refusing the file would unrepresent both.

    So the loader follows `_sub`'s idiom: not an error, because it is a
    legitimate state, but it must be VISIBLE. Closing the residual properly
    means either accepting that unrepresentation or moving the no-seller-list
    escape hatch so it also runs when `first_party_only` is false — a decision
    with two gates on the other side of it, not a tidy-up.
    """
    with caplog.at_level(logging.ERROR):
        cfg = Config.load(
            _write(tmp_path, "watches:\n  - name: thing\n    retailer: walmrt\n    target: https://x/1\n")
        )

    assert cfg.watches[0].retailer == "walmrt", "the name must reach the Watch unchanged"
    assert "walmrt" in caplog.text
    assert "no adapter" in caplog.text


def test_the_shipped_config_names_only_retailers_this_build_knows() -> None:
    """The positive half, and it is not decoration.

    A validator can meet every test above by refusing everything. This is the
    file the daemon actually loads, and it carries `nintendo` on two watches —
    which is exactly the retailer 05-REVIEW's suggested `KNOWN_RETAILERS` left
    out. Taking that set verbatim would have refused the shipped config at
    startup.
    """
    root = Path(__file__).resolve().parent.parent
    cfg = Config.load(root / "config" / "products.yaml")

    assert {w.retailer for w in cfg.watches} == {
        "gamestop",
        "walmart",
        "nintendo",
        "bestbuy",
        "target",
        "amazon",
    }


def test_the_known_retailer_set_is_exactly_the_one_with_seller_lists() -> None:
    """One definition, two readers — `STORE_SCOPED`'s own argument, applied here.

    A retailer in `KNOWN_RETAILERS` with no `FIRST_PARTY` entry loads fine and
    then reads UNKNOWN forever on `_verdict_from_html`'s no-seller-list escape
    hatch, which is a permanent health warning from a config the loader called
    valid. A retailer in `FIRST_PARTY` and not here cannot be configured at all,
    so its seller list is dead code. Neither is a state anybody would choose;
    both are what a set maintained in two places drifts into.
    """
    from boty.models import KNOWN_RETAILERS, STORE_SCOPED
    from boty.retailers import FIRST_PARTY, MARKETPLACES

    assert set(FIRST_PARTY) == KNOWN_RETAILERS
    assert STORE_SCOPED <= KNOWN_RETAILERS
    assert MARKETPLACES <= KNOWN_RETAILERS


def test_both_walmart_watches_carry_a_store_pin_key() -> None:
    """CONTEXT is explicit that REQ-14 applies to the PRODUCT watch, not only the control.

    Asserted against the file's text rather than against the loaded `Watch`,
    because the loaded value is `None` whenever `WALMART_STORE_ID` is unset —
    which is the normal state of a fresh clone and of CI. The key being present
    is the decision; the value being set is the operator's setup step.
    """
    body = (Path(__file__).resolve().parent.parent / "config" / "products.yaml").read_text(
        encoding="utf-8"
    )
    walmart_blocks = [b for b in body.split("- name:") if "retailer: walmart" in b]

    assert len(walmart_blocks) == 2, "expected exactly two Walmart watches"
    for block in walmart_blocks:
        assert "store_id: ${WALMART_STORE_ID}" in block, (
            "a Walmart watch has no store pin. An unpinned Walmart reading is a "
            "statement about an arbitrary store, which is the bug this phase exists "
            "for — and the product watch counts, not only the control."
        )
