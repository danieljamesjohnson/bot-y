# Phase 5: A Reading Means Something - Pattern Map

**Mapped:** 2026-08-10
**Files analyzed:** 12 (all MODIFIED — this phase creates no new module)
**Analogs found:** 12 / 12

Every surface this phase touches already exists, and every one of them has a
precedent *in this repo's own history* for exactly the change being made. Phase
3.1 added `Rung`, then `Extraction`, then widened `Result.degraded` — three
worked examples of "add an axis to `Result`, thread it through `status.write`,
render it on the dashboard, pin it with a mutation." Store identity is the
fourth pass down that same groove. The planner should copy that groove rather
than invent one.

## File Classification

| Modified file | Role | Data flow | Closest analog | Match |
|---|---|---|---|---|
| `boty/models.py` — `Result.store` (+ `Watch.store_id`) | model | transform | `Result.extraction` / `Rung`, same file lines 63-104, 137-144 | exact (self-analog, 3rd pass) |
| `boty/config.py` — parse+validate `store_id` per watch | config | transform | `_price()` lines 62-79 and `_retailer_intervals()` lines 95-119 | exact |
| `boty/parse.py` — read the answering store out of `__NEXT_DATA__` | utility | transform | `nextdata_offers()` lines 289-323 + `_dig`/`_WALMART_PRODUCT_PATH` lines 278-286 | exact |
| `boty/retailers.py` — UNKNOWN on unpinned/mismatched store | service | request-response | `_verdict_from_html` UNKNOWN guards lines 240-272 | exact |
| `boty/monitor.py` — health message for an unpinned watch | service | transform | `assess_health()` lines 65-113 | exact |
| `boty/notify.py` — alert text naming only measured causes | service | event-driven | `send_health_warning()` lines 59-81 | exact |
| `boty/pacing.py` — persist `_state` across restart | service | file-I/O | `monitor.State` lines 33-49 (**the** on-disk-state analog) | role+flow match |
| `boty/cli.py` — wire pacer persistence, push policy | controller | event-driven | `watch_cycle` lines 199-290, `watch_loop` lines 293-320 | exact |
| `boty/status.py` — publish the store per watch | service | file-I/O | `write()` watches block lines 90-121 | exact |
| `served/boty/index.html` — render the store tag | component | request-response | `.tag.dom` CSS line 55-59 + row template line 121 | exact |
| `config/products.yaml` — `store_id` on both Walmart watches | config | — | walmart entries lines 59-61 (product) and 86-88 (control) | exact |
| `scripts/mutation_check.py` — mutations for the new gates | test | batch | `M6`/`M7` lines 232-266, `M2` lines 191-203 | exact |
| `tests/test_retailers.py`, `tests/test_pacing.py`, `tests/test_status.py`, `tests/test_dashboard.py`, `tests/test_config.py` | test | — | see § Test-side analogs | exact |

## Pattern Assignments

### `boty/models.py` — store identity on `Result` (model, transform)

**Analog:** itself — `Rung` (lines 27-61), `Extraction` (lines 63-104), the
declaration order comment on `rung`/`extraction` (lines 137-144), and
`Result.degraded` (lines 163-185).

**The declaration rule, verbatim** (`boty/models.py:136-144`):

```python
    #: Which rung produced this reading. Declared last, with a default, so
    #: every pre-existing construction site stays valid and keeps its meaning:
    #: they are all plain TLS fetches, and none of them names a rung.
    rung: Rung = Rung.TLS
    #: What was read out of the page. Declared last, after `rung`, with a
    #: default, for the same reason `rung` is: every pre-existing construction
    #: site stays valid and keeps its meaning, because every one of them reads
    #: a structured payload and none of them names an extraction.
    extraction: Extraction = Extraction.STRUCTURED
```

Copy this exactly for the store field: **declared last, after `refused`, with a
default of `None`**, and a docstring saying what the default MEANS (`None` =
"nobody recorded a store", which for a non-Walmart retailer is the honest value
and must not read as "store 0"). This is the same three-valued honesty
`status.write`'s `duration_seconds` comment (lines 51-57) argues for a number.

**The "deliberately NOT" section** (lines 36-52 and 75-95) is a required part of
this pattern, not decoration. Both enums carry an explicit paragraph on why the
new axis is not folded into `Availability` (`cli.SYMBOL` is indexed
unconditionally — a fourth member is a KeyError mid-report) and not fed into
`Health`. The store field needs the same paragraph, and it has an extra one to
write: **why an unpinned store DOES change `Availability` to UNKNOWN while
`degraded` deliberately does not touch `alertable`** (lines 181-183). That is a
real asymmetry and the docstring must justify it, or the next reader will
"fix" it.

**Type choice.** `Watch.store_id: str | None = None` follows `max_price: float |
None = None` (line 116) — declared last on the frozen dataclass, defaulted, so
every existing `Watch(...)` in the tests stays valid. `Result.store` should be
a `str | None` for the same reason a `Rung` is an enum and a store is not: the
set of Walmart store numbers is not closed.

**What NOT to do:** do not derive store-mismatch into `degraded`. `degraded`
answers "should a reader discount this?" A reading from the wrong store is not
discountable, it is **not about your store at all** — it is UNKNOWN. Keep the
two flags separate the way lines 163-185 keep `rung` and `extraction` separate.

---

### `boty/config.py` — `store_id` as required-with-no-default (config, transform)

**Analog:** `_price()` (lines 62-79) for the per-watch coercion shape,
`_retailer_intervals()` (lines 95-119) for the "refuse the file with a message
naming the offending key" shape.

**Per-watch coercion, refusing the file** (`boty/config.py:62-79`):

```python
def _price(value: Any, where: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):  # bool is an int subclass; `max_price: true` is a typo
        raise ValueError(f"{where}: max_price must be a number, got {value!r}")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{where}: max_price must be a number, got {value!r}") from exc
```

Note the `where` parameter and its call site (line 150):
`_price(entry.get("max_price"), f"watch {entry.get('name')!r}")`. A store_id
coercion takes the same `where`.

**The construction site to extend** (`boty/config.py:144-153`):

```python
        for entry in raw.get("watches") or []:
            watches.append(
                Watch(
                    name=entry["name"],
                    retailer=entry["retailer"],
                    target=str(entry["target"]),
                    max_price=_price(entry.get("max_price"), f"watch {entry.get('name')!r}"),
                    control=bool(entry.get("control", False)),
                )
            )
```

**Critical design note the planner must resolve here.** CONTEXT says store
pinning is "required config with no default", and *also* says unset means
UNKNOWN with a health message. Those are two different failure modes and this
file already has both idioms:

- `_price`/`_interval` **raise `ValueError` and refuse the whole file**.
- `_sub` (lines 33-48) **logs a warning and continues**, explicitly because
  "an unset `${BESTBUY_API_KEY}` is a legitimate state, but it must be visible."

REQ-14 wants the second: a missing `store_id` must NOT crash the daemon, because
crashing takes down five healthy retailers over one Walmart watch. It must load,
read UNKNOWN, and say why in the health message. So follow `_sub`'s pattern
(warn, carry a visible absence) — but the absence must be carried as data on the
`Watch`, not just a log line, because `assess_health` needs it. `log.warning` in
config is the *supplement*, not the mechanism.

Validation this file's precedent demands: reject the bool typo the way `_price`
does (`store_id: true`), and coerce with `str()` the way `target` does (line
149) so YAML reading `store_id: 3520` as an int does not blow up on comparison —
that is `_price`'s own docstring bug, one field over.

---

### `boty/parse.py` — reading the answering store (utility, transform)

**Analog:** `nextdata_offers()` (lines 289-323).

```python
_WALMART_PRODUCT_PATH = ("props", "pageProps", "initialData", "data", "product")


def _dig(doc: Any, path: Iterable[str]) -> Any | None:
    for key in path:
        if not isinstance(doc, dict):
            return None
        doc = doc.get(key)
    return doc
```

and the defensive read (lines 297-313):

```python
    m = _NEXTDATA_RE.search(html)
    if not m:
        return None
    try:
        doc = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None

    product = _dig(doc, _WALMART_PRODUCT_PATH)
    if not isinstance(product, dict):
        return None

    status = product.get("availabilityStatus")
    if isinstance(status, dict):
        status = status.get("value")
    if not isinstance(status, str):
        return None
```

Every step returns `None` rather than guessing — copy that exactly. `None` from
the store reader means "the page did not tell us which store answered", which is
UNKNOWN territory, never "store 0".

**Measured fact for the planner, from the shipped fixture.** `storeId` appears
15 times in `tests/fixtures/walmart/milk-control.html`, with the value `"0"` —
plus `storeName`, `storeIds`, `storeFrontIds`, `"storeId":null`, and a
`storeId=0` query param in embedded ad URLs. So a naive substring grep will hit
the wrong one, and `0` is very likely Walmart's "no store assigned" sentinel,
which is precisely the unpinned condition this phase exists to catch. Pin the
exact JSON path as a module constant beside `_WALMART_PRODUCT_PATH` and give it
the same kind of comment; do not regex the raw HTML.

---

### `boty/retailers.py` — UNKNOWN on unpinned or unexpected store (service, request-response)

**Analog:** the two UNKNOWN guards in `_verdict_from_html` (lines 240-272).
These are the closest thing in the codebase to what criterion 3 asks for: a
*configuration or attribution gap* that must produce UNKNOWN rather than a
verdict, on a marketplace.

**Guard shape to copy** (`boty/retailers.py:258-272`):

```python
        if first_party_only and watch.retailer in MARKETPLACES and any(o.seller is None for o in offers):
            # The page says something is buyable but does not say by whom, on a
            # site where that is a real question. OUT_OF_STOCK would be a
            # confident wrong answer; IN_STOCK could be a flipper's listing.
            return Result(
                watch,
                Availability.UNKNOWN,
                detail=(
                    f"{len(offers)} offer(s) via {source} with no seller recorded, and "
                    f"{watch.retailer} is a marketplace — cannot tell whose offer this is"
                ),
                url=url,
                rung=rung,
                extraction=extraction,
            )
```

The store guards are the same sentence one axis over: *"the page says something
is buyable but does not say WHERE"* (unpinned) and *"it says where, and it is
not your store"* (mismatch). Two separate guards with two distinct `detail`
strings — the config gap and the mismatch are different facts and a reader
needs to tell them apart, exactly as lines 240-257 and 258-272 are two guards
rather than one.

**Where in the function.** Both existing guards sit in the "offers exist but we
cannot attribute them" branch, i.e. after parsing and before any verdict. The
store guards belong at the same depth or earlier, and must precede the
`Availability.IN_STOCK if offer.available` line (line 282) — a store mismatch
short-circuits before any stock verdict is formed.

**`detail` is the evidence channel** (`models.py:131-134`: "Human-readable
evidence for the verdict... so a wrong verdict can be diagnosed without
re-running"). The unpinned detail must name the config key by the name a user
types in `products.yaml`, so the message is a fix instruction and not a
complaint.

**Threading.** Walmart goes through the generic `check_html` (line 295) via
`cli.make_checker`'s fallback arm (`boty/cli.py:84`) — there is no
`check_walmart`. So the store must be read inside `_verdict_from_html`/
`check_html`, and `check_html` must set it on **every** return path including
the two `except` arms (lines 299-302), the same way `check_target_browser`'s
docstring (line 542) commits: "Every Result below carries `rung=Rung.BROWSER`
and `extraction=Extraction.DOM`, **error paths included**". Do not add a
Walmart-specific arm to `make_checker` unless the store read cannot live in the
generic path; the existing arms (lines 66-84) each carry a comment justifying
why a separate reader was unavoidable, and the planner owes the same
justification if it adds a fifth.

---

### `boty/monitor.py` — the health message for an unpinned watch (service, transform)

**Analog:** `assess_health()` (lines 82-110). This is the exact mechanism
criterion 2's "health message saying so" needs, and it already carries the
refusal-vs-breakage split that REQ-15 is about:

```python
            refused = bool(broken) and all(c.refused for c in broken)
            health.append(
                Health(
                    retailer,
                    ok=False,
                    refused=refused,
                    reason=(
                        "the retailer is refusing us — a challenge page or a 403. The "
                        "detector is probably fine; we are asking too often. Backing "
                        "off, and no action is needed unless this persists"
                        if refused else
                        "control product is not reading IN_STOCK — the detector is "
                        "probably broken, so real restocks would be missed silently"
                    ),
                    failing_controls=[f"{c.watch.name}: {c.availability.value} ({c.detail})" for c in broken],
                )
            )
```

**This block is REQ-15's whole subject.** Both of the two live counterexamples
are literally here:

- `"the detector is probably broken, so real restocks would be missed silently"`
  — the else-arm, lines 105-106.
- `"we are asking too often"` — the if-arm, line 102.

REQ-15 says no alert names a cause the code has not established. Read this block
against that standard:

- The `refused` arm asserts *"we are asking too often"*. The code established a
  **refusal**; it did not establish **rate** as the cause. CONTEXT records it
  kept firing after a 6-hour backoff was observed not to help — so the sentence
  outlived its evidence. The measured claim is "the retailer refused us"; the
  rate diagnosis is a hypothesis. The rewrite must state the refusal and, per
  criterion 4, **say the cause is unknown** rather than pick a plausible one.
- The else arm asserts *"the detector is probably broken"* for **every**
  non-refusal failure. After this phase, an unpinned/mismatched store is a third
  cause landing in that same arm, and the sentence would be false again in
  exactly the 2026-08-04 way. The unpinned case needs its own arm with its own
  sentence.

The `all`-not-`any` reasoning at lines 91-93 ("if even one control failed for a
reason that is NOT a refusal, ... the louder reading is the safe one") is the
precedent for how to combine a third cause across a retailer's controls.

**Also note** the fourth cause already in this function: `"no control watch
configured"` (line 80), which is a *config gap* reported as `ok=False` with a
message that names the gap and nothing else. That single line is the closest
analog for the unpinned-store health message — copy its restraint.

---

### `boty/notify.py` — alert text (service, event-driven)

**Analog:** `send_health_warning()` (lines 59-81):

```python
    lines: list[str] = []
    for h in unhealthy:
        lines.append(f"[{h.retailer}] {h.reason}")
        lines.extend(f"  • {c}" for c in h.failing_controls)
    log.warning("sending detector health warning for: %s", ", ".join(h.retailer for h in unhealthy))
    return bool(
        client.notify(
            title=f"bot-y: detector problem ({len(unhealthy)} retailer(s))",
            body="\n".join(lines),
        )
    )
```

Two things the planner must see here. First, **this module composes no
diagnosis of its own** — the body is `h.reason` plus `h.failing_controls`
verbatim. So REQ-15 is fixed in `monitor.assess_health`, not here, and the only
thing wrong in this file is the hardcoded title `"bot-y: detector problem"`,
which asserts *problem with the detector* over a body that may be saying the
detector is fine. That title is the same defect as the two counterexamples, in
the one place a phone notification actually shows.

Second, the return-value contract: both senders return `bool` from
`client.notify`, and `cli.watch_cycle` (lines 250-258, 281-289) treats a `False`
as "not delivered — roll back the memory and retry". Any new notification path
must return the same bool and be wired into that same rollback, or it becomes a
send that "is not a retry — it is a drop nothing will ever mention again."

---

### `boty/pacing.py` — backoff state that survives restart (service, file-I/O)

**Analog:** `monitor.State` (`boty/monitor.py:33-49`). This is the repo's only
load/save-JSON-across-restart precedent and it is a very close fit — same
problem (per-key memory that must outlive the process), same daemon, same
config-driven path:

```python
@dataclass
class State:
    """Last-seen availability per watch, so alerts fire on transitions."""

    path: Path
    seen: dict[str, str]

    @classmethod
    def load(cls, path: Path) -> State:
        try:
            return cls(path, json.loads(path.read_text()))
        except (OSError, json.JSONDecodeError):
            return cls(path, {})

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.seen, indent=2, sort_keys=True))
```

Note: `load` swallows both `OSError` and `JSONDecodeError` into an empty state —
a corrupt or absent file must never stop the monitor starting. Copy that.

**`datastore/` is NOT the analog — do not use it.** It is changedetection.io's
own data directory (`changedetection.json`, per-watch UUID dirs, `secret.txt`,
`.br` page snapshots). Nothing in `boty/` reads or writes it. `state.json` at
repo root is the right precedent, and its path is already configurable:
`Config.state_path` (`boty/config.py:134`, `products.yaml:33`) with
`status_path` beside it (line 136). A pacer state path follows the same
three-line pattern: dataclass field with a default, `settings.get(...)` in
`load`, and a documented key in `products.yaml`.

**Two atomicity models exist and the planner must pick deliberately.**
`State.save` does a plain `write_text`. `status.write`
(`boty/status.py:123-129`) writes a temp file and `replace()`s it:

```python
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2))
        tmp.replace(path)  # atomic, so the page never reads a half-written file
```

`status.json` is atomic because it is *served over HTTP* while being written.
Pacer state has no concurrent reader, so `State`'s simpler form is the closer
analog — but `status.write` also wraps the whole thing in `try/except OSError:
log.exception(...)`, and pacer state should too: failing to persist a backoff
must degrade to today's in-memory behaviour, never take down a cycle.

**The module docstring is a direct obstacle and must be rewritten, not left.**
`boty/pacing.py:29-32` currently argues the opposite of criterion 6:

> Deliberately in-memory. A restart clears the backoff and tries once at full
> rate, which is the right trade: the alternative is a persisted penalty
> outliving the condition that caused it, and one extra request per restart is
> cheaper to reason about than a stale file.

That paragraph is a reasoned position, and criterion 6 overrules it. The
replacement must say *why* it was overruled (a restart resetting every backoff
to zero defeats politeness under a flapping service, and REQ-16's "pushed once
after the cap" is meaningless if the refusal counter resets), and it must answer
the stale-file objection the original raised — most likely by persisting a
timestamp and treating sufficiently old state as absent. This repo's convention
is that a reversed decision gets its reversal argued in place; see
`models.py:145-161` and `pacing.py:5-15` for the house style.

**What must persist:** `_RetailerState(interval, refusals, due_at)` (lines
50-55). `due_at` is on the pacer's own scheduled clock, not wall time —
`watch_loop` advances `scheduled_now` by the sleep it asks for and starts at
`0.0` (`boty/cli.py:313-317`). **A persisted `due_at` on that clock is
meaningless after a restart, because the clock restarts at zero.** This is the
single sharpest trap in criterion 6 and the plan must address it explicitly:
persist wall-clock timestamps, or persist `refusals` only and let `due_at`
rebuild. `refusals` is what REQ-16's "outlasts the cap" test reads
(`cli._refusal_is_entrenched`, lines 192-196, compares
`pacer._for(retailer).refusals >= REFUSALS_BEFORE_PAGING`), so `refusals` is the
field criterion 6 actually needs to survive.

---

### `boty/cli.py` — push policy (controller, event-driven)

**Analog:** `watch_cycle` lines 260-290 — REQ-16's first two clauses are
**already implemented here** and the plan should treat this as "verify and pin",
not "build":

```python
    unhealthy = [h for h in health if not h.ok]
    pageable = [h for h in unhealthy if not h.refused or _refusal_is_entrenched(h, pacer)]
    for h in unhealthy:
        if h not in pageable:
            log.info("%s unhealthy but refusing, not broken — not paging: %s", h.retailer, h.reason)
    fresh = [h for h in pageable if h.retailer not in warned]
    still_unhealthy = {h.retailer for h in pageable}
```

`log.info` for the not-pushed refusal is "recorded but not pushed"; `warned`
gives "pushed once"; `_refusal_is_entrenched` gives "outlasts the cap". What is
missing for criterion 5 is only that `refusals` resets on restart — which is
criterion 6. **The two criteria are one change.**

`Pacer` construction to modify (line 310):

```python
    pacer = Pacer(default_interval=cfg.interval_seconds, overrides=dict(cfg.retailer_intervals))
```

with the comment above it (lines 308-309) already stating the invariant a
persisted pacer must preserve: "One pacer for the life of the loop: the backoff
is memory, and a pacer rebuilt each cycle would forget every refusal and hammer
at full rate."

`State.load(cfg.state_path)` at line 448 is the call-site shape for loading
persisted pacer state at startup.

**`_report`'s tag composition** (lines 91-110) is the CLI half of the dashboard
tag convention and needs the store the same way:

```python
        tags = [
            t
            for t, on in (
                ("[control]", r.watch.control),
                ("[degraded]", r.degraded),
                ("[dom]", r.extraction is Extraction.DOM),
            )
            if on
        ]
        tag = f" {' '.join(tags)}" if tags else ""
```

Note the comment at lines 93-96: `SYMBOL` is indexed unconditionally by
`Availability` and must stay three-membered.

---

### `boty/status.py` — publish the store (service, file-I/O)

**Analog:** the `watches` block (lines 90-121), and specifically the comment at
lines 100-115 which declares these keys a public contract:

```python
        "watches": [
            {
                "name": r.watch.name,
                "retailer": r.watch.retailer,
                "availability": r.availability.value,
                "price": r.price,
                "detail": r.detail,
                "url": r.url,
                "control": r.watch.control,
                "alertable": r.alertable,
                "rung": r.rung.value,
                "extraction": r.extraction.value,
                "degraded": r.degraded,
            }
            for r in results
        ],
```

Add `"store"` here. The precedent for what to publish is the `rung`-beside-
`degraded` argument (lines 104-115): publish the **raw fact** as well as any
derived flag, because "`degraded` alone cannot tell a reader WHY to discount a
reading". Applied here: publish the store that answered, and if a
pinned-vs-answered mismatch flag is added, publish both — a reader must be able
to tell "no store recorded" from "store 4174 answered and you pinned 3520".

`None` for a non-Walmart watch is correct and has its own precedent in this file
— `duration_seconds` (lines 51-57): "`None` means 'nobody timed this pass',
which is not 'it took no time'... A missing measurement serialised as 0 would
read off the dashboard as the fastest check ever recorded." Store `0` is
literally the value in the fixture, so serialising an absent store as `0` here
would be that bug word for word.

---

### `served/boty/index.html` — render the store (component, request-response)

**Analog:** the `dom` tag, added in Phase 3.1 as the second tag on this row.
CSS (lines 54-59):

```css
  .tag.degraded { color: var(--warn); border-color: color-mix(in srgb, var(--warn) 45%, transparent); }
  /* `degraded` says discount this reading; `dom` says why. The flag has two
     ... */
  .tag.dom { color: var(--warn); border-color: color-mix(in srgb, var(--warn) 45%, transparent); }
```

Row template (line 121):

```js
${w.control ? '<span class="tag">control</span>' : ''}${w.degraded ? '<span class="tag degraded" title="lower confidence: ...">degraded</span>' : ''}${w.extraction === 'dom' ? '<span class="tag dom" title="read out of the page&#39;s presentation markup rather than the retailer&#39;s own structured feed — a reskin breaks this silently">dom</span>' : ''}
```

Copy this exactly: one more `${w.store ? ... : ''}` conditional span with a
`class="tag"` (plain, receding — a store number is a label, not a warning) and a
`title=` explaining what it means. Every retailer-controlled string goes through
`esc()` — see the `esc(w.name)` / `esc(w.url)` calls on the same line, and
`tests/test_dashboard.py`'s `UNTRUSTED` list (line 43), which the store must be
added to since it originates in Walmart's JSON.

Note lines 49-53 distinguish a plain `.tag` (recedes) from a louder warning
tag. An unpinned/mismatched store is a *warning*; a correctly-pinned store is a
plain label. Two visual weights, same as `control` vs `degraded`.

---

### `config/products.yaml` — the pin (config)

**Analog:** the two existing Walmart entries.

```yaml
  - name: Pokémon GO Plus +          # line ~58
    retailer: walmart
    target: https://www.walmart.com/ip/Pok-mon-GO-Plus-for-Nintendo-Switch/1203950273
    max_price: 80
```

```yaml
  - name: Great Value milk           # line ~85
    retailer: walmart
    target: https://www.walmart.com/ip/Great-Value-Whole-Vitamin-D-Milk-Gallon-Plastic-Jug-128-Fl-Oz/10450114
    control: true
```

**REQ-14 applies to both** — CONTEXT is explicit that it is "the GO Plus +
product watch, not only the control." Add `store_id:` to each.

The file's comment convention (see the Best Buy block, lines ~90-101, and the
GO Plus + block, lines 63-66) is that any non-obvious key gets a paragraph
explaining the decision behind it. `store_id` needs one covering: why there is
no default, that a missing value produces UNKNOWN rather than a guess, and how a
user finds their store number. This block is a shipped file a stranger reads —
it is the setup step CONTEXT says every user now pays.

Settings block precedent for a new `settings:` key, if pacer persistence needs
one: `state_path: state.json` at line 33.

## Shared Patterns

### The "three-valued honesty" argument
**Source:** `boty/models.py:1-24` (module docstring), applied again at
`boty/status.py:34-39` (paced retailers), `boty/status.py:51-57`
(`duration_seconds: None`), `boty/monitor.py:57-58` (UNKNOWN never overwrites).
**Apply to:** every new field and every new guard in this phase.
The house move is: when a third state appears, name it and publish it rather
than collapsing it into one of the first two. "No store recorded" is a third
state beside "your store" and "someone else's store", and it must not serialise
as `0`, as `""`, or as absent.

### A comment justifying the decision, in the code
**Source:** everywhere — `models.py:36-52`, `retailers.py:31-51`,
`retailers.py:81-94`, `pacing.py:1-33`, `status.py:44-61`, `monitor.py:158-184`.
**Apply to:** every file in this phase.
This codebase's density of *why* comments is its dominant convention. Every
rejected alternative is recorded at the site of the decision, including the two
CONTEXT names as rejected for REQ-14 (default-to-assigned, geolocate-from-ZIP).
A plan that adds a field without adding its paragraph does not match this
codebase.

### Error paths carry the same metadata as success paths
**Source:** `boty/retailers.py:334-338` (Amazon), `:461` (Best Buy browser),
`:542` (Target), `:647-650` (Best Buy API) — four separate docstrings each
committing that error returns carry the same `rung`/`extraction` as the happy
path, with `:650` naming the bug avoided: "Leaving the `Rung.TLS` default in
place on those paths would" misreport the reading.
**Apply to:** the store field on every `check_html` return, `except Blocked` and
`except FetchError` included (lines 299-302).

### Notification delivery is verified, not assumed
**Source:** `boty/cli.py:244-258` and `:281-289`.
**Apply to:** any new push in this phase. A `False` from a sender must roll back
the memory that suppresses the retry.

### `make verify` is the gate
**Source:** `Makefile`. Offline tests + mypy + lint + live controls + mutation
check, one exit code. Per CONTEXT's deferred section, `VERIFY: FAIL (live
controls)` has been standing since 2026-08-06 and Walmart is challenge-blocked —
so **criterion 3's "watched going red" must be satisfiable offline against the
fixtures**, and live confirmation is a bonus. That is a hard constraint on how
the plan writes its evidence step.

## Test-side analogs

### Fixture-backed retailer test
**Analog:** `tests/test_retailers.py:140-151`:

```python
def test_walmart_first_party_offer_is_accepted(
    monkeypatch: pytest.MonkeyPatch, walmart_milk: str
) -> None:
    """The control case: a genuine Walmart.com listing passes both defences."""
    _serve(monkeypatch, walmart_milk, WALMART_URL)
    watch = Watch(name="milk", retailer="walmart", target=WALMART_URL, control=True)

    result = retailers.check_html(watch, first_party_only=True)

    assert result.availability is Availability.IN_STOCK
    assert "Walmart.com" in result.detail
    assert result.price == 2.42
```

with the fetch stub at lines 38-44 and the synthetic-payload builder
`_nextdata(**product)` at lines 54-57 — use `_nextdata` for the store-mismatch
cases (a fixture cannot be edited to hold a different store without lying about
what was captured) and the real fixtures for the unpinned case. Fixtures live in
`tests/fixtures/walmart/` with a paired `.json` note; `tests/conftest.py:109-119`
holds the `walmart_goplusplus` / `walmart_milk` fixtures. `conftest.py:43-79` is
an autouse network guard — offline is enforced, not hoped for.

The single most on-point existing test is
`test_walmart_offer_with_no_seller_recorded_is_unknown_not_a_verdict`
(line 183) — "It must not be IN_STOCK ... and it must not be OUT_OF_STOCK
either". The store tests are that test with `where` swapped for `who`, and
should assert **both** directions the same way.

### Mutation registration
**Analog:** `scripts/mutation_check.py:174-266`.

```python
@dataclass(frozen=True)
class Mutation:
    ident: str
    target: str
    search: str
    replace: str
    breaks: str
```

`M6`/`M7` (lines 232-266) are the exact precedent for this phase: they guard a
*claim* rather than a verdict — a flag whose removal changes no availability, no
price and no alert, which "a suite that only asserts on verdicts would go on
passing" through. A store field is the same kind of thing. Their comments also
establish that **two mutations are needed when a change has two independent
halves** ("M6 dying proves the flag EXISTS. Only M7 proves the flag's NEW
disjunct is load-bearing"), and that sharing a `search` string across mutations
is fine because each runs in its own sandbox.

`M2` (lines 191-203) is the analog for mutating a verdict guard to the wrong
value (`UNKNOWN` → `OUT_OF_STOCK`), which is exactly the store guards' mutation.
Read its re-anchoring comment (lines 194-199): **anchor on the verdict, not the
message text** — "matching the message text would tie a mutation to prose that
is edited far more often than the verdict is." The store guards' prose will be
edited; their `Availability.UNKNOWN` will not.

Expect at minimum: one mutation flipping the unpinned guard to a verdict, one
flipping the mismatch guard, and one clearing the persisted pacer state (a
change that alters no verdict at all — pure M6 territory). `main()` (line 463)
reports `caught/total`; the plan's evidence step should show the count rising
and each new mutation observed caught.

### Pacer tests
**Analog:** `tests/test_pacing.py`. Its module docstring (lines 1-17) is the
prose statement of REQ-15/REQ-16 and should be extended rather than duplicated.
Test helpers at lines 31-44 (`_w`, `_ok`, `_refused`, `_broken`), and it already
constructs `State(tmp_path / "state.json", {})` directly (lines 237, 265) — the
pattern for a `tmp_path`-backed persisted pacer test. `Pacer` takes `now` as a
parameter precisely "so tests can drive a day of cycles without sleeping through
one" (`pacing.py:60-63`), which is how the restart test gets written: run to N
refusals, persist, build a fresh `Pacer`, assert the count survived.

`tests/test_cli_watch.py` (lines 43, 96-370) drives `watch_loop` with
`cycles=` and a fake sleep and re-loads `State` from disk between assertions —
that is the shape of a restart test at the loop level.

### Producer/consumer contract tests
**Analog:** `tests/test_status.py` pins the producing half; `tests/test_dashboard.py`
pins the consuming half. `test_dashboard.py:1-22` states why both are needed:
"A contract asserted at one end only is a comment." Any key added to
`status.write` needs an assertion in both files, and the store must join
`UNTRUSTED` (line 43) since it comes from Walmart's JSON and lands in
`innerHTML`.

### Config validation tests
**Analog:** `tests/test_config.py` (164 lines) — the shape for asserting that a
bad `store_id` is refused with a message naming the watch, and that an absent
one loads without raising.

### Machine-checked doc/code binding
**Analog:** `tests/test_support_matrix.py` (963 lines), which binds README
matrix cells to code both directions. Relevant here **only if** the plan adds a
user-facing claim about store pinning to the README — REQ-18 (matrix binding) is
explicitly Phase 6 and out of scope. If `products.yaml`'s new comment or the
README setup steps make a checkable claim, `tests/test_contributor_docs.py`
(492 lines) is the closer analog than the matrix.

## No Analog Found

None. Every surface has a precedent. The two items with the weakest fit, flagged
for the planner:

| Item | Why the analog is imperfect |
|---|---|
| Persisting `Pacer._state` | `monitor.State` is a strong structural analog, but nothing in the repo persists a *scheduling clock*, and `due_at` lives on `watch_loop`'s synthetic `scheduled_now` which restarts at `0.0`. The plan must decide what is persisted, not just how. |
| Rewriting alert prose (REQ-15) | `assess_health` is the site, but there is no precedent for a message that says "the cause is unknown" — every existing message asserts a cause. This one is genuinely new prose, and criterion 4 is a claim about *absence* (no alert names an unestablished cause), which is harder to gate than a positive assertion. Consider a test that greps `monitor.py`/`notify.py` for the two known-bad strings, in the style of `test_dashboard.py`'s structural source assertions and `monitor.py:181-184`'s self-aware note about a criterion that greps a file. |

## Metadata

**Analog search scope:** `boty/`, `tests/`, `scripts/`, `served/boty/`, `config/`
**Files scanned:** 14 read, ~40 grepped
**Pattern extraction date:** 2026-08-10
