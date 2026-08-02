# Phase 2: Five Retailers Green — Pattern Map

**Mapped:** 2026-08-02
**Files analysed:** 12 (new or modified)
**Analogs found:** 9 exact/strong / 12 — 3 have **no precedent in this codebase**

The codebase is small and single-package: there is no `controllers/`,
`services/` layering to mine. The two real analogs are the **GameStop path**
(schema.org `ld+json`, single first-party offer, no seller node) and the
**Walmart path** (`__NEXT_DATA__` hydration, seller-aware, marketplace). Almost
everything Phase 2 adds is a variation on one of those two, with three genuine
exceptions called out at the bottom.

---

## File Classification

| New/Modified file | Role | Data flow | Closest analog | Match |
|---|---|---|---|---|
| `boty/parse.py` (new extractor fn, if PC/Nintendo are not schema.org) | parser/utility | transform (HTML→Offer) | `nextdata_offers` (`boty/parse.py:109-143`) | exact |
| `boty/parse.py` (IN-03 `@type` list fix) | parser/utility | transform | `ldjson_offers` (`:60-91`) | exact (in-place) |
| `boty/retailers.py` — `FIRST_PARTY` + `MARKETPLACES` entries | config/dispatch | — | `boty/retailers.py:25-39` | exact |
| `boty/retailers.py` — Pokémon Center via `check_html` | checker | request-response | GameStop path (no new code likely) | exact |
| `boty/retailers.py` — Nintendo via `check_html` | checker | request-response | GameStop path | exact |
| `boty/retailers.py` — `check_bestbuy_browser` | checker | request-response (browser) | `check_bestbuy_api` (`:137-189`) for *shape* only | **weak — no browser precedent** |
| `boty/models.py` — DEGRADED flag | model | — | `Watch.control` / `Health.ok` | **none — new design** |
| `boty/cli.py` — `_make_checker` dispatch + `_report` degraded marker | dispatch/CLI | — | `boty/cli.py:33-52` | exact |
| `boty/status.py` — degraded in payload | serializer | — | `boty/status.py:21-47` | exact |
| `config/products.yaml` — 3 products + 3 controls | config | — | existing control block (`:39-55`) | exact |
| `tests/test_parse.py` + `tests/test_retailers.py` additions | test | — | existing tests, both files | exact |
| `tests/fixtures/{bestbuy,pokemoncenter,nintendo}/` | fixture data | file I/O | `tests/fixtures/gamestop/` via `boty capture-fixture` | exact |
| `README.md` retailer status table | docs | — | `README.md:58-66` | exact |
| `scripts/mutation_check.py` — new mutation for DEGRADED (optional) | test harness | — | `MUTATIONS` M4/M5 (`:126-139`) | exact |
| `pyproject.toml` — `browser` extra | config | — | `[project.optional-dependencies] dev` | exact |

---

## Pattern Assignments

### 1. Registering a retailer — `boty/retailers.py`

**There is no adapter class and no registry.** A "retailer" is three things:

1. A **string key** on `Watch.retailer`, straight out of YAML (`boty/config.py:113-120`
   does `retailer=entry["retailer"]`, no validation, no enum). Adding
   `retailer: pokemoncenter` to `config/products.yaml` is the entire registration.
2. An entry in `FIRST_PARTY` (`boty/retailers.py:25-30`) — and, if the site has a
   marketplace, in `MARKETPLACES` (`:39`).
3. Optionally, a branch in `boty/cli.py:_make_checker` if it needs a checker
   other than `check_html`.

The dispatch seam is exactly this, and it is the *only* one:

```python
# boty/cli.py:33-39
def _make_checker(cfg: Config) -> Callable[[Watch], Result]:
    def check(watch: Watch) -> Result:
        if watch.retailer == "bestbuy" and cfg.bestbuy_api_key:
            return check_bestbuy_api(watch, cfg.bestbuy_api_key)
        return check_html(watch, first_party_only=cfg.first_party_only)
    return check
```

**Convention to copy for Best Buy:** extend this one function, do not invent a
registry. The decided behaviour ("prefer the API when `BESTBUY_API_KEY` is set,
else the browser rung, flagged DEGRADED") is a third arm of the same `if`:

```python
if watch.retailer == "bestbuy":
    if cfg.bestbuy_api_key:
        return check_bestbuy_api(watch, cfg.bestbuy_api_key)
    return check_bestbuy_browser(watch)
```

**Load-bearing:** `scripts/control_check.py:152` builds its checker with this
same `_make_checker`, deliberately (`:22-26` docstring: "A control check that
routed requests differently from the running monitor would prove something
about a code path nobody runs"). So any new dispatch must go here and nowhere
else, or `make verify`'s live control stage tests a different code path than
production.

**Contract a new checker must satisfy** (`boty/retailers.py:1-12` docstring):
takes a `Watch`, returns a `Result`; when it cannot determine stock state it
returns `Availability.UNKNOWN` with a non-empty `detail`; it never returns
`OUT_OF_STOCK` to mean "I got lost".

**Pokémon Center and Nintendo probably need NO new checker at all.** If their
pages carry schema.org `Product` markup, `check_html` already handles them once
`FIRST_PARTY["pokemoncenter"]` / `FIRST_PARTY["nintendo"]` exist. Note that
`tests/test_retailers.py:203-231` already asserts the *current* behaviour for
`pokemoncenter`: an unconfigured key yields UNKNOWN. Adding the allow-list entry
is what flips it to a real verdict, and that test will need updating or a
sibling added.

---

### 2. Where a third extraction strategy slots in — `boty/parse.py`

The fallback chain is a literal two-step in `check_html`:

```python
# boty/retailers.py:71-75
offers = parse.ldjson_offers(page.text)
source = "ld+json"
if not offers:
    offers = parse.nextdata_offers(page.text)
    source = "__NEXT_DATA__"
```

A third strategy appends another `if not offers:` block with its own `source`
label. `source` is a plain string that ends up in `Result.detail`
(`:132`, `f"{source}: {offer.raw_availability} from {seller}"`), which is what
the tests assert on and what the status page shows.

**Every extractor obeys the same signature and the same three-valued return**
(`boty/parse.py:1-11`, and `tests/test_parse.py:4-11`):

```python
def <name>_offers(html: str) -> list[Offer] | None:
```

- `None` = "no structured data of this kind here, try the next strategy"
- `[]` = "there is a product here and it has no offers"
- `[Offer, ...]` = a reading

Collapsing `None` and `[]` is explicitly called out as the bug that turns a
reshaped page into a confident verdict. Note `check_html` currently tests
`if not offers:` — which treats `[]` and `None` the same at the call site
(this is IN-02 in `01-REVIEW.md`); do not "fix" it incidentally.

**The `ldjson_offers` pattern** (`:60-91`) — regex out every `application/ld+json`
block, `json.loads` each, `continue` past `JSONDecodeError` so one broken block
does not take the page down, walk with `_iter_nodes` (handles node / list /
`@graph`), and track `saw_product` separately from `found` so the None-vs-`[]`
distinction survives.

**The `nextdata_offers` pattern** (`:94-143`) — the important convention is
`_WALMART_PRODUCT_PATH`, an **explicit dotted path** to the primary product node
plus a `_dig` walk, with this rationale at `:94-97`:

> Addressed explicitly rather than by searching, because a product page also
> embeds recommendations, bundles and "customers also bought" — all with their
> own availabilityStatus. A generic walk happily reports a $12 screen protector
> as your restock.

**Copy this for any new hydration-blob extractor** (Pokémon Center is a
Salesforce/Next-ish SPA; Nintendo's store is a Next.js app — both are candidates
for a `__NEXT_DATA__` payload at a *different* path than Walmart's). If a new
retailer uses `__NEXT_DATA__` with a different product path, do **not**
generalise `nextdata_offers` into a searcher — add a second named path constant
and a second function, or parameterise the path. `tests/test_parse.py:124-135`
pins the one-offer-only behaviour as a regression.

**IN-03 fix belongs here** (`01-REVIEW.md:718-733`). `boty/parse.py:72` is
`if node.get("@type") != "Product": continue`, which misses
`"@type": ["Product", "ProductModel"]` and would present as an unexplained
UNKNOWN on exactly these first-party sites. The review supplies the fix
verbatim:

```python
types = node.get("@type")
types = types if isinstance(types, list) else [types]
if "Product" not in types:
    continue
```

---

### 3. First-party filtering and the price ceiling — the Phase 1 hardening

Both defences are already implemented and **a new adapter honours them by doing
nothing special** — as long as it routes through `check_html` and returns a
`Result` carrying a real `price`.

**`_pick`** (`boty/retailers.py:42-59`) is the seller filter. The hardened part
(WR-02):

```python
allowed = FIRST_PARTY.get(retailer, set())
named = [o for o in offers if o.seller and o.seller.strip().lower() in allowed]
unattributed = [] if retailer in MARKETPLACES else [o for o in offers if o.seller is None]
candidates = named or unattributed
```

So `seller=None` is first-party **only** off a marketplace. Pokémon Center and
Nintendo are single-seller — put them in `FIRST_PARTY`, leave them out of
`MARKETPLACES`, and the `seller=None` fallback covers pages with no seller node
(the GameStop shape). Best Buy is already in both (`:29`, `:39`).

**The two UNKNOWN escape hatches in `check_html`** (`:90-118`) are what Phase 2
must not regress:

- **WR-03** (`:90-105`): a retailer with no `FIRST_PARTY` entry returns UNKNOWN,
  not OUT_OF_STOCK. Comment names Phase 2 explicitly: "REQUIREMENTS targets
  three more retailers that arrive through this door." Once you add allow-list
  entries the new retailers stop using this door — verify the WR-03 test
  (`tests/test_retailers.py:203`) still exercises a genuinely-unconfigured key.
- **WR-02** (`:106-118`): a marketplace offer with `seller is None` is UNKNOWN.

**The price ceiling** lives entirely in `Result.alertable`
(`boty/models.py:58-75`), not in any adapter:

```python
if self.availability is not Availability.IN_STOCK: return False
if self.watch.max_price is None: return True
if self.price is None: return False      # WR-01 hardening
return self.price <= self.watch.max_price
```

**The obligation this puts on a new adapter:** if it can read availability but
not price, an in-stock reading with a configured `max_price` is now
**silently non-alertable**. That is correct, but it means a browser-rung Best Buy
adapter that scrapes availability and skips price will never alert on a watch
that has a ceiling. Extract the price. `check_bestbuy_api:186` shows the
convention — `price=p.get("salePrice")` straight onto the Result.

---

### 4. Test pattern

**Two files, two levels, and they do not overlap:**

| File | Tests | Network |
|---|---|---|
| `tests/test_parse.py` | extractors against frozen HTML — pure functions, no monkeypatching at all | never reached |
| `tests/test_retailers.py` | `check_html` / `check_*` verdicts — monkeypatches `retailers.get` | monkeypatched |

**Fixture loading** — `tests/conftest.py:72-97`: one named pytest fixture per
saved page, each a one-line `load(retailer, name)` with a docstring stating what
stock state the page represents:

```python
@pytest.fixture
def walmart_milk() -> str:
    """Walmart milk control: IN_STOCK at $2.42, sold by Walmart.com."""
    return load("walmart", "milk-control")
```

Copy exactly. Naming convention on disk: `<retailer>/<product>.html` for the
product and `<retailer>/<thing>-control.html` for the control
(`gamestop/ps5-control`, `walmart/milk-control`). Fixtures are produced with
`boty capture-fixture <retailer> <name> <url> --note '<stock state>'` — the
`--note` is not optional in practice: `report_fixture_staleness`
(`scripts/control_check.py:250-252`) warns on a missing note and the CLI warns
at capture time (`boty/cli.py:77-83`).

**Serving HTML to a checker** — `tests/test_retailers.py:33-46`:

```python
def _serve(monkeypatch: pytest.MonkeyPatch, html: str, url: str = GAMESTOP_URL) -> None:
    def _get(target: str, **kwargs: object) -> Page:
        return Page(url=target, status=200, text=html)
    monkeypatch.setattr(retailers, "get", _get)

def _raise(monkeypatch: pytest.MonkeyPatch, exc: Exception) -> None:
    def _get(target: str, **kwargs: object) -> Page:
        raise exc
    monkeypatch.setattr(retailers, "get", _get)
```

Note `monkeypatch.setattr(retailers, "get", ...)` — patching the *imported name
in `retailers`*, not `fetch.get`. A browser-rung adapter that does not go through
`fetch.get` needs its own seam of the same shape (see §6 below).

**Synthetic-payload builders** for cases no fixture covers —
`tests/test_retailers.py:49-57` (`_nextdata(**product)`, `_ldjson(**offer)`) and
`tests/test_parse.py:24-29` (`_ldjson_page`). Build one per new payload shape
rather than hand-writing HTML strings in each test.

**The test set a new adapter owes**, mirroring what GameStop and Walmart have:

1. product page reads the expected availability + price (fixture-backed)
2. control page reads IN_STOCK and is alertable (fixture-backed)
3. unparseable page → UNKNOWN, explicitly `is not Availability.OUT_OF_STOCK`
   (`test_unparseable_page_is_unknown_not_out_of_stock:258`) — the suite's most
   important assertion, restated per adapter
4. `Blocked` → UNKNOWN with `"blocked"` in detail (`:283`)
5. `FetchError` → UNKNOWN with `"fetch failed"` in detail (`:295`)
6. extractor-level: `None` on no blob, `None` on malformed JSON, `None` on
   missing product node, `""` → `None` (`tests/test_parse.py:146-161`)

**The network guard** — `tests/conftest.py:26-69`. Autouse, patches
`curl_cffi.requests.{get,post,request,head,put,delete,Session}` **and**
`socket.create_connection` / `socket.socket.connect` / `connect_ex`, raising a
`BaseException` subclass so `fetch.get`'s `except Exception` cannot downgrade it
to UNKNOWN. `tests/test_retailers.py:392-411` is labelled in its own docstring
as "the shape a Phase 2 adapter test will have".

**This is a live hazard for the browser rung.** `nodriver` drives Chrome over a
CDP websocket in a subprocess — it does not use `curl_cffi`, and it may not use
`socket.create_connection` either (asyncio uses `loop.create_connection` →
`sock_connect`, and it spawns a real browser process). Per 02-CONTEXT: "If a
test needs a transport the guard does not yet patch, **extend the guard** rather
than working around it." Extend `no_network` to also block the browser launch
entry point.

---

### 5. Declaring a control product — `config/products.yaml`

Three distinct kinds of watch already exist in the file; copy the right one.

**Product watch** (`:29-37`) — has `max_price`, no `control`:

```yaml
  - name: Pokémon GO Plus +
    retailer: gamestop
    target: https://www.gamestop.com/.../20003961.html
    max_price: 80          # MSRP is $54.99; anything near $140 is a flip
```

**Control watch** (`:43-55`) — `control: true`, **no `max_price`** (a ceiling on
a control is meaningless and `test_gamestop_control_is_in_stock_and_alertable`
depends on its absence):

```yaml
  - name: CONTROL — Great Value whole milk
    retailer: walmart
    target: https://www.walmart.com/ip/.../10450114
    control: true
```

Naming convention: `CONTROL — <product>`. Selection rule, stated at `:49-51`:
first-party, restocked routinely, never subject to a marketplace buy-box fight.
"Do not use a console here" — on a marketplace, an out-of-stock reading would be
*correct* and you would chase a phantom bug. For Pokémon Center / Nintendo /
Best Buy pick an evergreen first-party staple.

**Transition watch** (`:57-95`) — `TRANSITION — <product>`, deliberately **not**
`control: true` and deliberately **no `max_price`**. The rationale block at
`:67-81` is the thing to preserve: they are *expected* to read OUT_OF_STOCK, and
both `control_check.py` and `assess_health()` filter on `control`, so a watch
without it cannot fail the gate whatever it reads. The comment at `:79-81` says
GameStop is the only current source; if a Phase 2 retailer publishes flappy
first-party stock, it can supply one too — but that is optional and must not
gate `make verify`.

**Every configured retailer needs at least one control or `make verify` fails.**
`scripts/control_check.py:139-150` computes `configured - verified` before making
any request and returns exit 2 with the list. This is by design (WR-04): adding
an adapter without a control breaks the build.

**Config plumbing for a new setting** — if the browser rung needs a knob, copy
`bestbuy_api_key` end to end: `${VAR}` in the YAML `settings:` block
(`config/products.yaml:20`), `_expand` handles the substitution and warns on
unset (`boty/config.py:33-59`), and a field on `Config` read in
`Config.load` (`:99`, `:126`). Numeric settings must go through a `_price`/
`_interval`-style coercion (`:62-92`) — the WR-07 lesson is that an
un-coerced YAML value survives to runtime and kills the cycle.

---

### 6. DEGRADED — **no analog exists**

`boty/models.py` has exactly three dataclasses and one enum. There is **no
degraded, no confidence, no method/rung concept anywhere in the codebase.** This
is new design, not pattern-following. Say so to the planner.

What *does* exist, as the nearest structural precedents:

- **`Availability`** (`models.py:20-24`) — a 3-valued enum. DEGRADED is
  explicitly **not** a fourth member: it is orthogonal to what the stock reading
  says. Adding it to `Availability` would break `assess_health`
  (`monitor.py:78`, `is not Availability.IN_STOCK`), `SYMBOL`
  (`cli.py:26-30`, a dict indexed unconditionally at `:46` — a missing key is a
  `KeyError` mid-report), and `transitioned_to_stock`.
- **`Watch.control: bool = False`** (`models.py:40`) — a boolean flag with a
  default, threaded through `config.py:120`, `monitor.py:74`, `status.py:42`,
  `cli.py:45`. This is the **shape** to copy if the flag is a property of the
  *watch/retailer*.
- **`Result.detail: str`** (`models.py:55`) and **`Result.url`** — free-form
  evidence copied verbatim into `status.json` (`status.py:41-42`).
- **`Health(retailer, ok, reason, failing_controls)`** (`models.py:78-85`) —
  per-retailer, derived, `ok: bool`. A per-*retailer* DEGRADED is most natural
  here, but `assess_health` currently constructs `Health` from results alone and
  has no notion of which method produced them.

**The design question the planner must answer:** DEGRADED is a property of the
*reading method actually used*, which is only known inside the checker. That
argues for a field on `Result` (`degraded: bool = False`, or better
`method: str` / `Rung` enum with degradation derived from it), set by
`check_bestbuy_browser` and left default everywhere else — then surfaced by:

- `boty/status.py:34-46` — add a key to the per-watch dict (the payload is a
  flat literal; adding a key is mechanical)
- `boty/cli.py:42-52` — `_report` already appends `tag = " [control]" if …`;
  a `[degraded]` tag follows the same one-line pattern
- `boty/monitor.py:61-93` — if `Health` should carry it, aggregate over the
  group's results
- `README.md:58-66` — a third column or a status-cell marker

Adding a field to a frozen dataclass with a default is backward-compatible for
every existing construction site (`retailers.py` builds `Result` positionally
for `watch`/`availability` and by keyword thereafter), so this is a low-blast-
radius change **provided** the new field has a default.

**Add a mutation for it.** `scripts/mutation_check.py:126-139` (M4/M5) was added
precisely because the gate could not see the layer where the worst bug lived. If
DEGRADED is load-bearing for trust, a mutation that clears the flag and expects
the suite to go red belongs alongside them. Same `Mutation(ident, target,
search, replace, breaks)` shape; `search` must be an exact source substring
(`apply_mutation:226-239` raises if the anchor is not found or the substitution
is a no-op).

---

### 7. The support matrix — `README.md:58-66`

```markdown
## Retailer status

| Retailer | Method | Status |
|---|---|---|
| GameStop | `curl_cffi` + schema.org JSON-LD | ✅ Working |
| Walmart | `curl_cffi` + `__NEXT_DATA__`, seller-aware | ✅ Working |
| Best Buy | Official API (free key) | ⚠️ Needs a key — … |
```

Convention: **Method** names the transport and the extraction strategy together;
**Status** is an emoji plus a plain-English clause explaining any caveat. Phase 2
adds Nintendo, promotes Pokémon Center from 🚧 Planned, and rewrites the Best Buy
row (the current text says the API is the only sane path; the phase decision is
that the browser rung is now the *primary* path and the API is the upgrade). The
"escalation rung" the phase wants recorded fits naturally as an added column or
inside the Method cell — the CONTEXT leaves rendering to discretion.

Also update `README.md:123` — "The 36 offline tests still pass" is a hardcoded
count that will drift.

---

## Shared Patterns

### Never guess — UNKNOWN with a reason
**Source:** `boty/retailers.py:1-12` (docstring), `:77-86`, `:90-118`
**Apply to:** every new checker and extractor.
Every failure path returns `Availability.UNKNOWN` with a non-empty `detail`
naming the cause. `test_bestbuy_api_key_never_reaches_the_result:352` asserts
`result.detail, "a UNKNOWN verdict must still say why"`.

### Secrets never reach a Result
**Source:** `boty/retailers.py:137-189` (CR-03 fix)
**Apply to:** any adapter that handles a credential.
Two rules, both mechanical: (a) `Result.url` is always the **public product
URL**, computed up front and used on every return path — never the credentialed
API URL; (b) anything derived from an exception goes through a local `_redact`,
because curl error strings echo the URL they were given.

```python
product_url = f"https://www.bestbuy.com/site/-/{watch.target}.p"
def _redact(text: str) -> str:
    return text.replace(api_key, "***") if api_key else text
...
return Result(watch, Availability.UNKNOWN, detail=_redact(f"api error: {exc}"), url=product_url)
```

The reason is `boty/status.py:38-43`, which copies `url` and `detail` verbatim
into a file served over HTTP.

### `watch.target` is polymorphic
**Source:** `boty/models.py:31-34` — "Product URL, or a retailer-specific id
(Best Buy SKU, Target TCIN)." `config.py:118` coerces with `str()` so a numeric
SKU in YAML does not arrive as an int. A new adapter may take either; document
which in the `Watch` comment and in `config/products.yaml`.

### Full type annotations
**Source:** `pyproject.toml [tool.mypy]` — `files = ["boty", "scripts"]` with
`disallow_untyped_defs`. `make types` runs bare `mypy`. Every new def, including
test helpers under `boty`/`scripts`, must be annotated. (Tests are not in
`files`, but the existing test modules annotate anyway — follow suit.)

### Optional heavyweight dependency
**Source:** `pyproject.toml [project.optional-dependencies] dev`
**Apply to:** `nodriver`. The stated rationale for `dev` — "Kept out of the
runtime deps so a deployed monitor does not pull a test framework onto the box"
— is exactly the CONTEXT constraint for the browser driver. Add a `browser`
extra, and have `check_bestbuy_browser` import `nodriver` **inside the function**
and return UNKNOWN with an actionable detail (`pip install 'bot-y[browser]'`) on
`ImportError`. The lazy-import precedent is `boty/fixtures.py:82` (`from . import
fetch` inside `capture()`, so importing the module cannot reach the network) and
`boty/cli.py:62`.

---

## No Analog Found

| Thing | Why there is no precedent |
|---|---|
| **Browser-rung fetching (`nodriver`)** | Every fetch in the codebase goes through `boty/fetch.py:get` — one synchronous `curl_cffi.requests.get` returning a frozen `Page`. `boty/fetch.py:1-14` argues *against* browsers ("a headless browser is not automatically better: it fixes the JavaScript fingerprint while leaving the TLS one untouched"). There is no async code anywhere, no subprocess management, no browser lifecycle, no timeout/cleanup pattern to copy, and no `Blocked`-detection equivalent for a rendered DOM (`BLOCK_PHRASES` at `fetch.py:34-41` scans response text — reusable in principle against rendered HTML, which is the one piece that does transfer). The `Page` dataclass (`fetch.py:52-64`) is the right *return* type to preserve so a browser fetch can feed `parse.ldjson_offers` unchanged — that is the seam worth designing for. |
| **A DEGRADED concept** | Nothing in `models.py`, `status.py`, `monitor.py` or `cli.py` represents reading quality, method, or rung. See §6 — genuinely new design. |
| **Testing a browser adapter offline** | `conftest.py`'s guard covers `curl_cffi` and raw sockets only. A `nodriver` adapter needs both a new monkeypatch seam (the analog is `monkeypatch.setattr(retailers, "get", _get)` — so the browser fetch should be a single module-level function in `retailers` or a new module, patchable by name) and an extension to `no_network`. |

---

## Metadata

**Search scope:** `boty/`, `tests/`, `scripts/`, `config/`, `Makefile`,
`pyproject.toml`, `README.md`
**Files scanned:** 15
**Extraction date:** 2026-08-02
