---
phase: 10
plan: 04
subsystem: control-durability
tags: [REQ-24, criterion-3, live-reads, best-buy, false-dead, clause-A]
status: complete
requires:
  - "10-01 — the resolution predicate whose clause A this plan measured on the wire"
  - "10-03 — the durability rule whose bestbuy/D5 cell this plan moved"
  - "QUESTIONS.md § 0g — Dan's authorisation of at most three Best Buy reads"
provides:
  - "three live Best Buy readings, recorded with UTC timestamps, spacing, URL shape and outcome"
  - "the measured finding that clause A returns a FALSE DEAD for a live Best Buy SKU, because Best Buy's SKU search now redirects client-side"
  - "the incumbent control MEASURED ALIVE — IN_STOCK $59.99 first-party, 2026-09-02"
  - "bestbuy/D5 downgraded PARTIAL -> NOT SATISFIED on a live reading, in both records the gate binds"
  - "criterion 3's verdict: MET IN PART, with the missing half named"
affects:
  - "10-05 — criterion 3's row is MET IN PART, and criterion 1's mechanism has a measured false-positive on the wire"
  - "a future phase — the transport remedy is written down and unshipped"
tech-stack:
  added: []
  patterns:
    - "the counting rule and the branch table committed BEFORE the first request, so no outcome can be reinterpreted in its own light"
    - "a capability check pointed at about:blank — a render that never leaves the host — so browser startup cannot consume a read"
    - "one variable changed between two readings, so the difference measures the variable"
key-files:
  created: []
  modified:
    - docs/retailer-evidence.md
    - docs/adding-a-retailer.md
    - config/products.yaml
    - README.md
    - tests/test_control_durability.py
decisions:
  - "Read 2 reallocated from the candidate-class search to re-asking the incumbent at a longer settle — reversed in the dated form BEFORE it was spent"
  - "The control is NOT swapped: the defect is in the resolution path, not the product, and any replacement meets the identical clause A"
  - "The transport fix is NOT shipped: the reads that would confirm it are spent, and an unconfirmed fix is a recommendation"
  - "README's robots.txt and Terms `unread` cells do NOT move — the plan's premise that a product read falsifies them was wrong"
  - "bestbuy/D5 is NOT SATISFIED, not PARTIAL: a LIVE target reading as a dead control is the inverse of what D5 asks"
metrics:
  duration: "~50m"
  completed: 2026-09-02
actuals:
  tokens: 26000
  tasks: 3
  commits: 7
---

# Phase 10 Plan 04: Spend the Three Reads — Summary

**Three navigations left this host. Three of three authorised, Best Buy only, spaced 313 s and
311 s. Zero unspent, zero pre-navigation failures, no fourth request under any branch.**

And the answer they bought is not the one the phase expected: **the incumbent control is alive and
reads `IN_STOCK $59.99` first-party — and the monitor, through the path it is actually configured
to use, calls that same live SKU a dead control.** Twice.

---

## THE READS

| read | UTC start → end | spacing | URL shape | outcome |
|---|---|---|---|---|
| 1 | 14:13:01Z → 14:13:13Z | — | `/site/searchpage.jsp?st=<sku>` | `unresolved=True` off **21,823 B with no `<body>` at all** |
| 2 | 14:18:26Z → 14:19:02Z | **313 s** | `/site/searchpage.jsp?st=<sku>` | `unresolved=True` again, off 150,974 B — carrying Best Buy's own **308** to the product page |
| 3 | 14:24:13Z → 14:24:47Z | **311 s** | `/product/<slug>/<id>/sku/<sku>` | **`IN_STOCK`, `$59.99`, `seller: "Best Buy"`**, 1,157,107 B, `blocks 3 / unparseable 0` |

All three through the adapter directly. `boty check` not run, `scripts/control_check.py` not run
(read for reference only), `state.json` / `pacer-state.json` / `served/boty/status.json` not
written, no restart, no other retailer contacted.

**The pre-navigation exemption was available and was not taken.** Chromium's ability to start was
proved first against `about:blank` — a render that never leaves this host and therefore spends
nothing — precisely so a sandbox failure could not consume it.

---

## THE FINDING: clause A returns a FALSE DEAD for every Best Buy SKU

Read 2's rendered body contains Best Buy's own answer:

    NEXT_REDIRECT;replace;/product/pokemon-lets-go-pikachu-nintendo-switch/J7GSL4G7GQ/sku/6216393;308;

plus a matching `<meta http-equiv="refresh">`. That target is **character-for-character** the
canonical this repository recorded for this SKU on 2026-08-02. A 308 is *moved permanently* — the
product exists, and Best Buy is saying where.

**What changed is a mechanism, not a catalogue.** Best Buy's SKU search used to answer with a
**server-side** redirect: the browser landed on the product page, and `fetch_rendered` snapshotted
the *product* document. It now answers with a **client-side** redirect, so `fetch_rendered`
snapshots the *announcing search shell* — which carries no `ld+json` and a canonical pointing at the
search endpoint. That is **clause A of `10-01`'s predicate, exactly**, so `unresolved=True` is set.

Clause A was adopted on the reasoning that a search-endpoint canonical is *"Best Buy's own statement
about what page you are on"*. It is precisely that — and the page genuinely **is** the search page.
The SKU resolving is stated somewhere clause A does not look.

**So the mechanism this phase built to stop a dead control being misreported was, within four weeks
of being designed, reporting a live control as dead.** Nothing offline could have caught it: the
fixtures are the August pages, and this was the first live reading of this SKU since 2026-08-04.

Read 1's `<body>`-less document was the tell, not the cause: 21,823 B against ~1.1 MB for every
prior capture, `blocks 0 / unparseable 0` (neither the healthy `3/0` nor the 2026-08-04 broken
`3/3`), and Best Buy's own head still calling the request a search with `listCount: null`. Read 2 at
a 25-second settle produced a real document and the **same byte-identical verdict**, which is what
ruled slow rendering out as the whole explanation.

---

## CRITERION 3: **MET IN PART**

*"Best Buy's control is repaired — measured against a real reading, not a fixture — or replaced with
one that reads, with the replacement's durability argued."*

**The half that holds.** Measured against a real reading, not a fixture: read 3. And the premise the
criterion rests on is **disproven** — there was no dead control to repair. `10-DECISIONS.md`
§ Collision 10 established offline that the evidence was absent-then-stale; the wire confirms it.
The defect was in a *record*.

**The half that is missing, named in the same breath.** Through the **configured** path the control
does not resolve and is reported as a dead control. That is named and **unrepaired**: the remedy is
in `boty/browser.py` or `boty/retailers.py`, the three authorised reads were spent establishing the
fault, and **a transport fix that no live reading has confirmed is a recommendation, not a repair.**

Neither half is allowed to stand in for the other, and the criterion is not reworded.

---

## Deviations from Plan

**1. [Rule 4 → decided and recorded in writing BEFORE it was spent] Read 2 reallocated.**
Collision 9 allocated read 2 to a candidate-class search and read 3 to confirming a candidate SKU.
After read 1 returned a verdict off a document with no `<body>`, spending both remaining reads on a
**replacement** would have shipped a control chosen because the incumbent was declared dead on a
page that had not rendered — and the replacement's own confirming read would have met the identical
clause A on the identical page shape. Read 2 re-asked the same SKU with **one variable changed**
(settle 25 s against the shipped 3 s). The reversal is written into
`docs/retailer-evidence.md` in this repository's dated form — withdrawn text quoted whole, then the
measurements that overruled it, then what survives — and **committed before the read was taken**
(`fa9d25f`). What survives Collision 9 unchanged: the cap, Best Buy only, the spacing, the counting
rule, and *a refusal is the measurement*. This changed **which question** a read asks, never how
many may be asked.

**Why this is not "retrying around a refusal".** Read 1 was not refused — `refused=False`, no
`BLOCK_PHRASES` match, no `Blocked` raised.

**2. [The plan got a premise wrong] README's `unread` cells are NOT falsified by a product read.**
The plan, and the outline before it, say Best Buy's README cell reads *"unread — refused at the
connection layer"*, that it is inherited, and that a successful read or an unresolved result makes
it **false** so it must move. The first two halves are right; **the third is wrong**. There are two
such cells and both are **policy-document** columns — `robots.txt` and `Terms` — recording those two
*documents* returning no HTTP status and 0 B at **rung 1** on 2026-08-03. A rung-3 browser read of a
*product page* measures neither: different URL, different transport, different question. The
evidence log already anticipated the distinction — *"the two policy documents are the one thing
nobody has pointed a browser at"*. Reading `robots.txt` would have cost a fourth navigation. **The
cells do not move, and moving them would have put a falsehood into the support matrix.** What read 1
can speak to is the **Status** cell, and that is where the correction landed.

**3. [Rule 2 - correctness] `bestbuy`/`D5` downgraded PARTIAL → NOT SATISFIED.** `D5` asks that a
dead target read as a dead control; a **live** target reading as one means an `unresolved` from Best
Buy carries no information in either direction. PARTIAL described a clause covering two shapes out
of three; NOT SATISFIED describes a signal that is unusable. The withdrawn cell is quoted whole
above the measurement that overruled it, in both records `tests/test_control_durability.py` binds
cell-for-cell, and the failing-cell count moved twelve → thirteen with the earlier figure kept
beside it.

**4. [Not a deviation, recorded because it is the interesting non-change] The control was NOT
swapped, and `config/products.yaml`'s Best Buy target is byte-unchanged.** The defect is in the
resolution path, not the product. Any replacement SKU is reached through the same
`bestbuy_product_url` search and meets the identical clause A. The candidate-class search was
therefore not performed and the recorded reserve stands unchanged, still failing `D2` and `D3`.

---

## Known Stubs

None. No stub, placeholder or TODO was introduced.

## Deferred Issues

**The transport remedy, named and unshipped.** Follow the redirect Best Buy announces, or read the
resolution off the `NEXT_REDIRECT` payload, in `boty/browser.py` or `boty/retailers.py`. Deferred
because the reads that would confirm it are spent and this repository does not ship a control path
on fixture confidence. Recorded in `docs/adding-a-retailer.md` beside the `D5` cell, in
`config/products.yaml` beside the control an operator would reach for, and in
`docs/retailer-evidence.md` § Best Buy.

## Threat Flags

None. This plan added no network surface — it used an existing adapter against an existing
retailer, three times, under a user-set cap.

---

## Gates

| gate | result |
|---|---|
| `make verify-offline` | **PASS (OFFLINE)** — mutation check **39/39 caught**, survivors 0 |
| `scripts/identity_check.py --all` | **PASS — 272 files**, run before every commit; never `--no-verify` |
| `tests/test_control_durability.py` | 16 passed — the config/table binding held through the `D5` move |
| `tests/test_support_matrix.py` | 44 passed — the Status cell keeps its `[degraded]` declaration |
| `tests/test_evidence_check.py` | 74 passed — the Best Buy section still carries exactly one verdict line |

`make verify` was **not** run: it makes live requests to all six retailers and would have blown the
cap.

## Commits

| commit | what |
|---|---|
| `d2c0a36` | the counting rule and the branch table, **before** the first request |
| `1889f05` | read 1 spent — an unresolved verdict off a document with no body |
| `fa9d25f` | read 2 reallocated to discriminate, **decided before it is spent** |
| `639a264` | read 2 — the control is ALIVE, and clause A returned a false dead twice |
| `f4de466` | read 3 — IN_STOCK $59.99 first-party, live |
| `780bd61` | D5 downgraded on a live reading, and the control deliberately not swapped |
| `c6c2999` | criterion 3 MET IN PART, with the missing half named, and the budget accounted for |

## What this plan does NOT claim

- **Not that anything is on the wire.** `boty` is an editable install; the running daemon is on
  pre-phase code. `sudo systemctl restart boty` is Dan's call and still deferred — it now carries
  Phases 8, 9 and 10 together. **Not run, and not run as a side effect of anything here.**
- **Not that one reading is a distribution.** Read 3 is one reading at one moment.
- **Not that Best Buy's robots.txt or terms were read.** They were not.
- **Not that the incumbent is a *good* control.** It fails `D2`, `D3`, `D4` and now `D5`. It is
  **alive**, which is a different claim — and the two were conflated by the requirement this phase
  inherited.
- **Not that the false dead is fixed.** It is measured, named, and left in place with its remedy
  written down.

## Self-Check: PASSED
