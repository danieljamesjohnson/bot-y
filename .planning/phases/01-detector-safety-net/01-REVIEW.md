---
status: findings
phase: 01-detector-safety-net
reviewed: 2026-08-02T17:42:09Z
depth: standard
files_reviewed: 18
files_reviewed_list:
  - boty/cli.py
  - boty/config.py
  - boty/fetch.py
  - boty/fixtures.py
  - boty/models.py
  - boty/monitor.py
  - boty/notify.py
  - boty/parse.py
  - boty/retailers.py
  - boty/status.py
  - scripts/control_check.py
  - scripts/mutation_check.py
  - tests/conftest.py
  - tests/test_monitor.py
  - tests/test_parse.py
  - tests/test_retailers.py
  - Makefile
  - pyproject.toml
findings:
  critical: 3
  warning: 8
  info: 6
  total: 17
critical: 3
warning: 8
info: 6
---

# Phase 1: Code Review Report

**Reviewed:** 2026-08-02T17:42:09Z
**Depth:** standard
**Files Reviewed:** 18
**Status:** issues_found

## Summary

The four areas flagged for targeted scrutiny largely hold up, and I want to say
so precisely, because three of them are the phase's own safety guarantees:

- **`Makefile` — no defect found.** I did not trust the manual test; I built a
  throwaway checkout with a stub `$(PYTHON)` and forced each stage to fail in
  turn. `verify` exits non-zero when stage 1 fails, when stage 5 fails, and
  exits 0 only when all five pass. `verify-offline` correctly propagates
  `CONTROL_FLAGS=--offline` through two levels of recursive make. No pipelines,
  no `-` prefixes, no `;`-chained recipes. The exit-code contract is sound.
- **`scripts/mutation_check.py` — no defect found in its failure modes.** It
  never touches the working tree (it mutates a temp copy), it removes the
  sandbox in a `finally` on every path, it requires a passing baseline, it
  requires `import boty` to resolve inside the sandbox, it treats only pytest
  exit 1 as "caught" and aborts on 2/3/4/5, and `apply_mutation` raises rather
  than skipping when an anchor has drifted. A mutation that failed to apply
  would be reported SURVIVED (fail-closed), not CAUGHT. I ran it: 3/3 caught,
  zero sandboxes left in `/tmp`.
- **`scripts/control_check.py` — the connectivity probe cannot misclassify in
  the dangerous direction.** A captive portal completes the TCP handshake, so
  it reads as *online* and the controls then fail (safe). A DNS-only failure
  reads as online because the probe uses raw IPs, and the controls then fail
  (safe). The residual risk is the opposite direction, covered in WR-05.

The defects that matter are elsewhere, and they are all in the class this
project says it exists to prevent — a monitor that looks healthy while it is
not:

- **CR-01** is the worst. `run_once` never records `out_of_stock` for a product
  watch, so after the *first* restock alert every subsequent restock is
  silently swallowed. I reproduced it: in-stock → out-of-stock → in-stock
  produces exactly one alert instead of two. Thirty-six tests pass over this.
- **CR-02** shows the offline guarantee is bypassable. `boty.fetch.get`'s
  blanket `except Exception` catches conftest's `AssertionError` and converts a
  live-network attempt into `Availability.UNKNOWN`. I wrote a test that "forgot"
  to monkeypatch `retailers.get` and it passed green while asserting UNKNOWN.
- **CR-03** writes a Best Buy API key into the served `status.json`.

Also worth stating plainly: the Walmart fixtures are genuine 483 KB live
captures with accurate sidecars, and the "reads only the primary product"
regression test is meaningful — the fixture really does carry 10
`availabilityStatus` nodes. That part of the work is good.

---

## Critical Issues

### CR-01: `run_once` never records OUT_OF_STOCK, so every restock after the first is silently missed

**File:** `boty/monitor.py:113-122`
**Issue:**
`state.transitioned_to_stock(r)` is invoked as the *last* term of an `and`
chain inside a list comprehension, so Python short-circuits and never calls it
when `r.alertable` is False:

```python
alerts = [
    r for r in results
    if not r.watch.control and r.alertable and state.transitioned_to_stock(r)
]
for r in results:
    if r.watch.control:
        state.transitioned_to_stock(r)   # only controls get the fallback
```

`transitioned_to_stock` is the only thing that writes `state.seen`. A
non-control watch reading OUT_OF_STOCK is not alertable, so its state is never
written — the remembered value stays `"in_stock"` forever, and the next genuine
restock compares `previous != "in_stock"` and returns False.

**Failure scenario (reproduced):**

```
cycle 0: in_stock      alerts=['goplusplus']  state={'gamestop:goplusplus': 'in_stock'}
cycle 1: out_of_stock  alerts=[]              state={'gamestop:goplusplus': 'in_stock'}  <- not recorded
cycle 2: in_stock      alerts=[]              state={'gamestop:goplusplus': 'in_stock'}  <- MISSED DROP
```

This is the failure the whole project is built to avoid, and it survives the
new suite: `test_run_once_alerts_on_products_only_and_records_controls` only
ever feeds IN_STOCK, and `test_run_once_does_not_alert_above_the_price_ceiling`
runs a single cycle. The state file on disk right now
(`state.json`) is a live instance of this: any watch that has ever alerted is
now pinned at `in_stock` until it is hand-edited.

**Fix:** record state for every result unconditionally, then derive alerts from
the recorded transition. Remove the side effect from the comprehension.

```python
def run_once(watches, checker, state):
    results = [checker(w) for w in watches]
    for r in results:
        log.info(...)

    health = assess_health(results)

    # One pass, no short-circuiting: every result updates the memory, and the
    # transition is computed for all of them. `alertable` and `control` filter
    # what we NOTIFY about, never what we REMEMBER.
    transitions = {id(r): state.transitioned_to_stock(r) for r in results}
    alerts = [
        r for r in results
        if not r.watch.control and r.alertable and transitions[id(r)]
    ]
    state.save()
    return results, health, alerts
```

Add the regression test that would have caught it:

```python
def test_restock_after_a_sellout_alerts_again(tmp_path: Path) -> None:
    """in_stock -> out_of_stock -> in_stock must alert TWICE, not once."""
    watch = Watch(name="goplusplus", retailer="gamestop", target="https://x/1", max_price=80)
    state = State.load(tmp_path / "state.json")
    fired = []
    for av in (Availability.IN_STOCK, Availability.OUT_OF_STOCK, Availability.IN_STOCK):
        _, _, alerts = run_once([watch], lambda w, av=av: Result(w, av, price=54.99), state)
        fired.append(len(alerts))
    assert fired == [1, 0, 1]
```

---

### CR-02: the autouse network guard is swallowed by `fetch.get` and downgraded to UNKNOWN

**File:** `tests/conftest.py:38-44` (with `boty/fetch.py:85-86`)
**Issue:**
The guard raises `AssertionError`, but every request in this codebase goes
through `boty.fetch.get`, which wraps the call in a blanket handler:

```python
except Exception as exc:          # boty/fetch.py:85
    raise FetchError(f"{type(exc).__name__}: {exc}") from exc
```

`AssertionError` is an `Exception`, so the guard's loud failure becomes a
`FetchError`, which `check_html` then catches and turns into
`Availability.UNKNOWN`. The guard's docstring — "Any live request is a loud,
immediate failure" — is false for the only code path that makes requests.
`test_the_network_guard_actually_fires` documents the swallowing
(`pytest.raises(FetchError)`) rather than closing it.

**Failure scenario (reproduced):** I added a test that omits the
`monkeypatch.setattr(retailers, "get", ...)` a Phase 2 adapter test would need:

```python
def test_forgot_to_patch():
    result = retailers.check_html(Watch(name="x", retailer="gamestop", target="https://www.gamestop.com/x"))
    assert result.availability is Availability.UNKNOWN
# RESULT: Availability.UNKNOWN | fetch failed: AssertionError: test attempted a live network request
# 1 passed in 0.62s
```

It passes. `assert ... is Availability.UNKNOWN` is the single most common
assertion in `tests/test_retailers.py` (three tests use it), so this is the
most likely shape a future adapter test will take. On a machine where the guard
is not active — a `pytest` run outside conftest's scope, or if `curl_cffi`
renames `requests` — that same test makes a real request to GameStop and still
passes. The 0.62 s runtime is `fetch.get`'s `time.sleep(random.uniform(0.4,
1.6))`, which also runs during the accidental call.

Secondary gap: the guard only patches `curl_cffi.requests`. `boty.notify`
reaches the network through apprise (`requests`/`urllib3`) and
`scripts/control_check.have_connectivity` opens a raw `socket.create_connection`
— neither is blocked, so the first test to touch either will silently go live.

**Fix:** raise something `except Exception` cannot catch, and block the other
transports.

```python
class _NetworkBlocked(BaseException):
    """BaseException on purpose: boty.fetch.get wraps `except Exception`, so an
    Exception-derived guard is caught and downgraded to UNKNOWN — the test then
    passes while asserting on a verdict the guard itself manufactured."""


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*args: object, **kwargs: object) -> None:
        raise _NetworkBlocked(_MESSAGE)

    for name in ("get", "post", "request", "head", "put", "delete", "Session"):
        monkeypatch.setattr(curl_cffi.requests, name, _blocked, raising=False)
    # Anything that bypasses curl_cffi entirely (apprise -> requests,
    # control_check -> socket) must fail here too.
    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setattr(socket.socket, "connect", _blocked)
```

and update `test_the_network_guard_actually_fires` to assert the *new*
contract, which is the point of the change:

```python
def test_the_network_guard_is_not_downgraded_to_a_verdict() -> None:
    """The guard must escape fetch.get's `except Exception`, not become UNKNOWN."""
    from boty import retailers
    with pytest.raises(BaseException, match="test attempted a live network request"):
        retailers.check_html(Watch(name="x", retailer="gamestop", target="https://example.invalid/"))
```

---

### CR-03: the Best Buy API key is written into `Result.url` and served in `status.json`

**File:** `boty/retailers.py:105-119` (leaks via `boty/status.py:41`)
**Issue:**
`check_bestbuy_api` builds the request URL with the key interpolated
(`?apiKey={api_key}`) and, on every error path, returns that full URL as
`Result.url`:

```python
url = f"https://api.bestbuy.com/v1/products(sku={watch.target})?apiKey={api_key}&format=json&..."
...
return Result(watch, Availability.UNKNOWN, detail=f"api error: {exc}", url=url)   # :113
return Result(watch, Availability.UNKNOWN, detail=f"bad api json: {exc}", url=url) # :115
return Result(watch, Availability.UNKNOWN, detail=f"sku ... not found", url=url)   # :119
```

Only the success path (`:128`) substitutes the clean public product URL.
`boty/status.py:41` copies `r.url` verbatim into `served/boty/status.json`,
which is the file the dashboard serves over HTTP through the Mission Control
`/tools/boty` proxy. `detail` can carry it too: `FetchError` is formatted as
`f"{type(exc).__name__}: {exc}"` and curl error strings routinely include the
requested URL.

This violates the project constraint that credentials live only in
`~/.config/boty/env` at mode 600.

**Failure scenario (reproduced):** with `BESTBUY_API_KEY` set and Best Buy
returning HTTP 403 (which REQ-04 says is its normal behaviour), `status.json`
contains:

```json
{
  "availability": "unknown",
  "detail": "api error: HTTP 403",
  "url": "https://api.bestbuy.com/v1/products(sku=6577129)?apiKey=SUPERSECRETKEY123&format=json&show=..."
}
```

**Fix:** never let the credentialed URL into a `Result`. Pass the key as a
parameter and keep a redacted public URL for reporting.

```python
def check_bestbuy_api(watch: Watch, api_key: str) -> Result:
    product_url = f"https://www.bestbuy.com/site/-/{watch.target}.p"
    api_url = (
        f"https://api.bestbuy.com/v1/products(sku={watch.target})"
        f"?apiKey={api_key}&format=json&show=sku,name,salePrice,onlineAvailability"
    )

    def _redact(text: str) -> str:
        return text.replace(api_key, "***") if api_key else text

    try:
        data = get(api_url).json
    except (Blocked, FetchError) as exc:
        return Result(watch, Availability.UNKNOWN, detail=_redact(f"api error: {exc}"), url=product_url)
    except ValueError as exc:
        return Result(watch, Availability.UNKNOWN, detail=_redact(f"bad api json: {exc}"), url=product_url)
    ...
```

Every `Result` from this function should carry `product_url`, never `api_url`.

---

## Warnings

### WR-01: the price ceiling fails open when the price cannot be read

**File:** `boty/models.py:63-64`
**Issue:**

```python
if self.watch.max_price is None or self.price is None:
    return True
```

An IN_STOCK result whose price could not be extracted is treated as alertable
even when a ceiling is configured. That is the opposite of this codebase's own
rule for unknown data — an unreadable availability is UNKNOWN, but an unreadable
price is "cheap enough". `send_restock` even has a `"price unknown"` branch
(`boty/notify.py:51`), so the alert goes out with no price at all.

**Failure scenario:** Walmart reshapes `priceInfo.currentPrice` (it has already
been reshaped once — hence `_dig`). `nextdata_offers` returns
`Offer(available=True, price=None, seller=...)`. If `first_party_only` is off,
or if the reseller offer omits `sellerName` (see WR-02), the $229.99 flip
listing alerts against an $80 ceiling. Verified:
`Result(watch(max_price=80), IN_STOCK, price=None).alertable` → `True`.

REQ-02 requires the ceiling to *independently* suppress a marketplace listing;
`test_walmart_reseller_rejected_by_price_ceiling_alone` only covers the
price-present case, so this hole is untested.

**Fix:** a ceiling that cannot be evaluated must not authorise an alert.

```python
@property
def alertable(self) -> bool:
    if self.availability is not Availability.IN_STOCK:
        return False
    if self.watch.max_price is None:
        return True
    # A ceiling was configured and we could not read a price. "I could not
    # tell" must not resolve to "cheap enough" — that is the same conflation
    # as reporting out-of-stock for a page we failed to parse.
    if self.price is None:
        return False
    return self.price <= self.watch.max_price
```

Add `test_unpriced_in_stock_offer_does_not_pass_the_ceiling`.

---

### WR-02: an offer with no seller attribution is treated as first-party, even on a marketplace

**File:** `boty/retailers.py:38-41`
**Issue:**

```python
named = [o for o in offers if o.seller and o.seller.strip().lower() in allowed]
# A page with no seller attribution at all (single-seller retailers
# like GameStop) is implicitly first-party.
candidates = named or [o for o in offers if o.seller is None]
```

The fallback is right for a single-seller retailer, but it is applied
unconditionally — including for `walmart` and `target`, which are in
`FIRST_PARTY` precisely *because* they are marketplaces. On a marketplace, "no
seller recorded" means "I do not know who is selling this", which under this
project's own rules is UNKNOWN territory, not an implicit first-party pass.

**Failure scenario (reproduced):** `nextdata_offers` sets
`seller=product.get("sellerName")`, which is `None` whenever Walmart's
hydration payload omits that key. `_pick([Offer(available=True, price=229.99,
seller=None)], "walmart", first_party_only=True)` returns the offer rather than
`None` — the reseller listing passes defence one. Combined with WR-01 (missing
price) it passes both defences and alerts.

**Fix:** only fall back to unattributed offers for retailers not known to be
marketplaces, and make that explicit rather than incidental.

```python
#: Retailers where a third party can hold the buy box. On these, an offer with
#: no seller recorded is "unknown seller", not "the retailer" — the fallback
#: below must not apply.
MARKETPLACES = {"walmart", "target", "amazon", "bestbuy"}

if first_party_only:
    allowed = FIRST_PARTY.get(retailer, set())
    named = [o for o in offers if o.seller and o.seller.strip().lower() in allowed]
    unattributed = [] if retailer in MARKETPLACES else [o for o in offers if o.seller is None]
    candidates = named or unattributed
```

---

### WR-03: an unconfigured retailer key produces a confident OUT_OF_STOCK

**File:** `boty/retailers.py:37` and `boty/retailers.py:76-82`
**Issue:**
`allowed = FIRST_PARTY.get(retailer, set())` returns an empty set for any
retailer key not in the dict. `named` is then always empty, `candidates` falls
back to unattributed offers only, and if the page names its seller (as most
schema.org markup does) `_pick` returns `None`. `check_html` maps that to:

```python
return Result(watch, Availability.OUT_OF_STOCK,
              detail=f"{len(offers)} offer(s) via {source}, none first-party", ...)
```

The truth in that case is "this retailer has no first-party allow-list
configured", which is a config gap, not a stock fact. `FIRST_PARTY` currently
covers four keys; REQUIREMENTS targets seven retailers, so three of the Phase 2
additions land straight into this path.

**Failure scenario (reproduced):** a Pokémon Center page with one
`InStock` offer from `seller.name == "Pokémon Center"` and
`retailer="pokemoncenter"` yields
`Availability.OUT_OF_STOCK | 1 offer(s) via ld+json, none first-party`. A
control product would flag it, but the product watch reports a confidently
wrong out-of-stock in the meantime — the exact conflation `Availability.UNKNOWN`
exists to prevent.

**Fix:** distinguish "filtered out a known non-first-party seller" from "no
allow-list for this retailer".

```python
offer = _pick(offers, watch.retailer, first_party_only)
if offer is None:
    if first_party_only and watch.retailer not in FIRST_PARTY:
        return Result(
            watch, Availability.UNKNOWN,
            detail=(f"{len(offers)} offer(s) via {source}, but no first-party seller "
                    f"list is configured for '{watch.retailer}' — cannot tell whose they are"),
            url=watch.target,
        )
    return Result(watch, Availability.OUT_OF_STOCK,
                  detail=f"{len(offers)} offer(s) via {source}, none first-party", url=watch.target)
```

---

### WR-04: `control_check` passes green when a configured retailer has no control at all

**File:** `scripts/control_check.py:104-116`
**Issue:**
The script only fails when there are **zero** control watches across the whole
config. A retailer with product watches and no control is invisible to it:

```python
controls = [w for w in cfg.watches if w.control]
if not controls:      # only the all-or-nothing case
    ... return 2
```

`boty.monitor.assess_health` already implements the right rule ("a retailer with
no control watch is reported unhealthy", `boty/monitor.py:75-76`), and the
acceptance criteria say "A retailer with no control watch is surfaced as
unhealthy" — but `make verify`, the gate everything downstream trusts, never
consults it.

**Failure scenario (reproduced):** a config with a `target` product watch and a
`gamestop` control gives:

```
control check: PASS — 1/1 controls in stock
control_check exit code (target has NO control): 0
```

`make verify` is green while the `target` detector has never been verified by
anything. This is the exact gap REQ-06 exists to close, and Phase 2 adds three
adapters through this door.

**Fix:** fail on unverified retailers, using the existing rule rather than a
second implementation of it.

```python
configured = {w.retailer for w in cfg.watches}
verified = {w.retailer for w in cfg.watches if w.control}
unverified = sorted(configured - verified)
if unverified:
    print(
        "control check: FAIL — no control watch for: " + ", ".join(unverified) + "\n"
        "  An unverified detector is treated as a broken one: nothing here can tell\n"
        "  you whether these retailers still parse. Add `control: true` to a watch.",
        file=sys.stderr,
    )
    return 2
```

---

### WR-05: an offline machine yields an unqualified "VERIFY: PASS"

**File:** `scripts/control_check.py:262-266` and `Makefile:68-75`
**Issue:**
The skip-when-offline policy is deliberate and I am not disputing it. The defect
is that the *verdict* does not carry the caveat. `control_check` prints
"SKIPPED" to stdout and returns 0; `verify` then prints `VERIFY: PASS` and exits
0, identical in every machine-readable respect to a run where the live controls
actually passed. Phase success criteria are stated as "`make verify` exits 0",
so a run that verified nothing about any retailer is indistinguishable from a
fully green one.

The probe itself is sound in the dangerous direction (a captive portal completes
the TCP handshake and therefore reads as *online*; a DNS-only failure reads as
online because `_PROBE_TARGETS` are raw IPs — both correctly proceed to a real
FAIL). The residual misclassification is the reverse: a host with no IPv4 route,
or an egress policy that permits 443 only to allow-listed destinations, cannot
reach `1.1.1.1:443` or `8.8.8.8:443` while reaching walmart.com fine. That host
skips a live check that would have failed.

**Fix:** give the skip its own exit code and let `verify` propagate it into the
verdict, so the green is honest.

```python
# scripts/control_check.py
SKIPPED = 3   # not a pass and not a failure: nothing was learned

if not have_connectivity():
    print("control check: SKIPPED — no outbound connectivity from this machine.", file=sys.stderr)
    ...
    return SKIPPED
```

```make
controls: check-venv
	@$(PYTHON) scripts/control_check.py $(CONTROL_FLAGS); \
	  rc=$$?; case $$rc in 0|3) exit $$rc ;; *) exit $$rc ;; esac

verify:
	...
	@$(MAKE_Q) controls; rc=$$?; \
	  case $$rc in \
	    0) ;; \
	    3) echo "VERIFY: live controls SKIPPED" > .verify-skipped ;; \
	    *) echo "VERIFY: FAIL (live controls)"; exit 1 ;; \
	  esac
	@$(MAKE_Q) mutation || { echo "VERIFY: FAIL (mutation check)"; exit 1; }
	@if [ -f .verify-skipped ]; then rm -f .verify-skipped; \
	   echo "VERIFY: PASS (OFFLINE — live controls were NOT run)"; \
	 else echo "VERIFY: PASS"; fi
```

The mechanism matters less than the property: the final line must say when the
only check that can detect a retailer change did not run.

---

### WR-06: a failed notification permanently loses the alert

**File:** `boty/cli.py:149` and `boty/cli.py:155`
**Issue:**
`run_once` commits `state.seen` and calls `state.save()` *before* the caller
tries to deliver. `send_restock` returns a bool that is discarded:

```python
if alerts:
    send_restock(cfg.notify_urls, alerts)     # return value ignored
```

Alerts are edge-triggered, so once the transition is recorded there is no second
chance.

**Failure scenario:** the GO Plus + restocks at 02:00. `run_once` records
`in_stock` and returns one alert. Telegram is rate-limiting, or
`BOTY_NOTIFY_URL` was never set (in which case `notify_urls` is `[]` after the
`if u` filter at `boty/config.py:65` and `send_restock` returns False on line
43 without logging anything). Next cycle, `previous == "in_stock"` → no alert.
The drop is missed with no error anywhere, and `status.json` shows a healthy
monitor. `send_health_warning` has the same shape: `warned` is updated on
line 156 regardless of whether the warning was delivered.

**Fix:** roll the memory back when delivery fails, so the next cycle retries.

```python
if alerts:
    if not send_restock(cfg.notify_urls, alerts):
        logging.error("restock alert NOT delivered — rolling state back so the next cycle retries")
        for r in alerts:
            state.seen.pop(r.watch.key, None)
        state.save()
```

and refuse to start silently with no notifier configured:

```python
if not cfg.notify_urls:
    print("no notify URLs configured — `watch` would run forever and tell nobody", file=sys.stderr)
    return 2
```

---

### WR-07: config values are neither validated nor coerced

**File:** `boty/config.py:27`, `boty/config.py:58`, `boty/config.py:68`
**Issue:** three distinct holes in one loader:

1. `max_price=entry.get("max_price")` is not coerced, while `target` is
   (`str(entry["target"])`). YAML `max_price: "80"` gives a `str`, and
   `Result.alertable` then evaluates `float <= str` → `TypeError`.
2. `interval_seconds=int(settings.get("interval_seconds", 300))` accepts `0` or
   a negative value. `time.sleep(0 * random.uniform(...))` is 0, producing an
   uncapped request loop against live retailers — a direct violation of the
   "never sub-minute" non-functional requirement.
3. `_expand` substitutes a missing `${VAR}` with `""` and says nothing.
   `bestbuy_api_key` silently becomes empty (falls back to the scrape path that
   REQ-04 documents as refused at the connection layer), and
   `notify: [${BOTY_NOTIFY_URL}]` silently becomes `[]` — see WR-06.

**Failure scenario:** a typo'd `max_price: "80"` makes `alertable` raise. In
`boty check` that propagates and the command dies; in `boty watch` it is caught
by the blanket handler (WR-08), so the service stays "running" while every
cycle aborts, `status.json` is never rewritten, and no notification is sent.

**Fix:**

```python
def _price(value: Any, where: str) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{where}: max_price must be a number, got {value!r}") from exc

...
max_price=_price(entry.get("max_price"), f"watch {entry.get('name')!r}"),

interval = int(settings.get("interval_seconds", 300))
if interval < 60:
    raise ValueError(f"interval_seconds must be >= 60 (polite polling), got {interval}")
```

and make an unresolved `${VAR}` visible:

```python
def _sub(m: re.Match[str]) -> str:
    name = m.group(1)
    if name not in os.environ:
        log.warning("config references ${%s}, which is not set — substituting empty", name)
    return os.environ.get(name, "")
```

---

### WR-08: the watch loop swallows every exception, so a permanently broken monitor looks alive

**File:** `boty/cli.py:157-158`
**Issue:**

```python
except Exception:
    logging.exception("check cycle failed; continuing")
```

Under systemd this is the failure mode the project was built to eliminate:
the unit stays `active (running)`, the process never exits non-zero, no health
warning is pushed (the notify call is inside the `try`), and `status.json` keeps
serving whatever it last held — a stale green dashboard. A config error (WR-07),
a parser `AttributeError`, or a disk-full `state.save()` all produce this.

**Fix:** tolerate transient failures, but treat a persistent one as a fault and
say so out loud.

```python
consecutive_failures = 0
while True:
    try:
        ...
        consecutive_failures = 0
    except Exception:
        consecutive_failures += 1
        logging.exception("check cycle failed (%d in a row)", consecutive_failures)
        if consecutive_failures == 3:
            send_health_warning(cfg.notify_urls, [Health(
                retailer="(all)", ok=False,
                reason="three consecutive check cycles raised — the monitor is running but not monitoring",
            )])
        if consecutive_failures >= 10:
            logging.error("giving up after %d consecutive failures", consecutive_failures)
            return 1   # let systemd restart or mark the unit failed
```

---

## Info

### IN-01: unused module logger

**File:** `boty/retailers.py:22`
**Issue:** `log = logging.getLogger(__name__)` is declared and never used
anywhere in the module.
**Fix:** remove it, or use it — a `log.debug` on the `_pick` outcome would be
genuinely useful when diagnosing a wrong seller verdict.

### IN-02: the test module's stated None-vs-`[]` rationale does not match the caller

**File:** `tests/test_parse.py:5-9`
**Issue:** the docstring says "The caller branches differently on each, so
collapsing them would turn a page whose shape changed into a confident
verdict." `check_html` does not branch differently — `boty/retailers.py:59`
uses `if not offers:`, which is true for both `None` and `[]`. Both end at
UNKNOWN, so nothing is wrong today, but the comment misstates the contract and
would mislead someone deciding whether the distinction can be dropped.
**Fix:** either soften the docstring to "the extractors preserve the
distinction so a future caller can act on it", or make `check_html` act on it.

### IN-03: `@type` as a list is not recognised

**File:** `boty/parse.py:72`
**Issue:** `if node.get("@type") != "Product": continue` misses valid
schema.org markup such as `"@type": ["Product", "ProductModel"]`. Fails safe
(`saw_product` stays False → `None` → UNKNOWN), so it costs coverage rather
than correctness — but it will read as a mysterious UNKNOWN on a Phase 2
retailer.
**Fix:**

```python
types = node.get("@type")
types = types if isinstance(types, list) else [types]
if "Product" not in types:
    continue
```

### IN-04: mutation set does not cover the price ceiling

**File:** `scripts/mutation_check.py:83-105`
**Issue:** M3 covers the seller filter, but nothing mutates
`Result.alertable`. The module docstring frames the two flipper defences as
independent, and REQ-02 requires them to be tested independently — so the
ceiling deserves its own mutation. I confirmed the suite *would* catch it
(`test_walmart_reseller_rejected_by_price_ceiling_alone` and
`test_run_once_does_not_alert_above_the_price_ceiling` both assert on it); this
is a coverage suggestion, not a defect.
**Fix:**

```python
Mutation(
    ident="M4",
    target="boty/models.py",
    search="return self.price <= self.watch.max_price",
    replace="return True",
    breaks="removes the price ceiling — a $229.99 flip alerts against an $80 cap",
),
```

### IN-05: two small robustness gaps in `mutation_check`

**File:** `scripts/mutation_check.py:117-125` and `scripts/mutation_check.py:166-168`
**Issue:** (a) `build_sandbox` raises `HarnessError` after `mkdtemp` when a
required path is missing, leaking the temp directory; (b) `_failed_tests`
depends on pytest's `FAILED ...` short-summary lines, which exist only because
`-ra` is in the copied `pyproject.toml` — if that option is ever removed the
report degrades to `0 test(s) failed` while still (correctly) returning True.
Neither affects the verdict.
**Fix:** wrap the copy loop in `try/except` with `shutil.rmtree(tmp,
ignore_errors=True)`; add `-rf` to the pytest argv in `run_suite` so the
summary lines are requested explicitly rather than inherited.

### IN-06: fixture path components are not sanitised

**File:** `boty/fixtures.py:61` and `boty/fixtures.py:66`
**Issue:** `FIXTURE_ROOT / retailer / f"{name}.html"` accepts `..` segments and
absolute paths from `boty capture-fixture <retailer> <name> <url>`, so
`boty capture-fixture ../../somewhere x <url>` writes outside the fixture tree.
Low severity — the CLI is local and the operator is the only caller — but it is
a write primitive driven by argv.
**Fix:**

```python
def _segment(value: str, label: str) -> str:
    if not value or "/" in value or "\\" in value or value.startswith("."):
        raise ValueError(f"invalid {label}: {value!r} — must be a single path segment")
    return value

def html_path(retailer: str, name: str) -> Path:
    return FIXTURE_ROOT / _segment(retailer, "retailer") / f"{_segment(name, 'name')}.html"
```

---

_Reviewed: 2026-08-02T17:42:09Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
