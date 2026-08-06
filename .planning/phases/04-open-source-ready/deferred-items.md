# Phase 4 — deferred items

Things measured during Phase 4 that are real, are out of this phase's scope, and
are written down rather than fixed inside a closing plan.

---

## `make verify` fails live on this host — 4 of 6 controls, two different reasons

**Measured** 2026-08-06 by 04-06 Task 3, running the phase gate once, live:

    VERIFY: FAIL (live controls)     # exit 2

This is **not** a Phase 4 regression. No plan in Phase 4 changed a retailer, an
extractor, a control or `boty/` at all — the phase's whole diff outside
`.planning/` is docs, licence, lint config, CI and packaging. It is recorded
because the closing record is where it would otherwise get lost.

`control_check.py` separates the two classes itself, and the separation is the
point — one of these says something about the detector and the other does not.

### Class 1 — could not run on this host (says nothing about the detector)

    control check: 2/6 control(s) could not run on THIS HOST
        bestbuy/CONTROL — Pokémon Let's Go, Pikachu! (Switch): fetch failed:
          no Chrome/Chromium binary found — set BOTY_BROWSER_PATH to one
        target/CONTROL — up&up microfiber dust cloths: fetch failed:
          no Chrome/Chromium binary found — set BOTY_BROWSER_PATH to one

Both are rung 3 (browser transport). Measured on this host: `nodriver 0.50.3`
**is** installed in `.venv`, but there is **no Chrome or Chromium binary** —
`command -v` finds none of `google-chrome`, `chromium`, `chromium-browser`,
`chrome`, and `BOTY_BROWSER_PATH` is unset. So the browser extra is half
present: the driver without a browser to drive.

**Fix, when someone wants the live gate green on danserver:** install a
Chromium binary and point `BOTY_BROWSER_PATH` at it. Not done here because
this plan may modify no file outside `.planning/` and installing a browser on
the host is not this plan's business.

### Class 2 — blocked at the edge (this *is* a statement about the detector)

    control check: FAIL — 2/6 control(s) not reading IN_STOCK
        walmart/CONTROL — Great Value whole milk: unknown —
          blocked: challenge page matched 'robot or human' (HTTP 200)
        amazon/CONTROL — Amazon Basics AA batteries (20-pack): unknown —
          blocked: challenge page matched 'to discuss automated access to amazon data' (HTTP 200)

Both retried once and were blocked again. Both read **UNKNOWN**, not
OUT_OF_STOCK — which is the fail-safe working: the detector is refusing to
claim a stock state it could not read, rather than reporting a false negative.
That is the designed behaviour and it is why this is a deferred item and not an
incident.

What it does mean, in `control_check.py`'s own words: *"real restocks are being
missed silently right now"* for those two retailers from this IP.

Both were green when 03.1-04 closed Phase 3.1 on 2026-08-03 (Walmart control
IN_STOCK; Amazon control green, with the product watch reading OUT_OF_STOCK
correctly). So this is a change in what the retailers serve this host, observed
2026-08-06, not a change in the code.

**Not diagnosed here, deliberately.** Distinguishing "this IP is now rate-limited
or reputation-flagged", "the challenge is new and unconditional", and "the
extractor needs a new shape" needs probing at a polite cadence and a fixture
re-capture, which is a plan, not a footnote in a closing record. The two
detector failures Phase 4 *did* investigate (Best Buy's JS-escaped JSON-LD,
Target's render race) are written up in `docs/retailer-evidence.md` and that is
the shape this one should get.

### The two prior detector notes, for whoever picks this up

`docs/retailer-evidence.md` already carries, from 2026-08-04 (commits `bf01421`,
`60c51c1`):

- **Best Buy served JavaScript-escaped JSON-LD** — 3 blocks found, 0 parsed,
  8 × `\'` inside strings and 34 × literal `\n` outside them. Fixed by
  `parse.ldjson_read` trying strict parsing first and publishing a repaired read
  as `ld+json (repaired)`. Explicitly **not claimed**: that the repair is what
  restored the live reading. The escaping is intermittent — a clean probe does
  not disprove it.
- **Target's UNKNOWN was our render race, not their page** — measured across
  `settle_seconds`: 1.0 s → 317,597 B, 1 `add to cart`, UNKNOWN; 3.0 s →
  ~352,000 B, 3 occurrences, `add-to-cart enabled`.

Neither of those is what is failing today: today both of those retailers cannot
be reached at all for want of a browser binary.

---

## The plan's phase-base derivation recipe undershoots

04-06 Task 3's verify block derives the phase base as the parent of the commit
that *added* `docs/adding-a-retailer.md`:

    BASE=$(git log --diff-filter=A --format=%H -- docs/adding-a-retailer.md | tail -1)^

That yields `4cfe2b2`, only **22** commits back — because 04-01 made two commits
(`db85e41`, `4cfe2b2`) *before* the one that added the doc. The plan's stated
*definition* is "the parent of the first execution commit", which yields
`8301f9f` (23 commits), and the SHA the plan expected, `b0a272f`, is the
pre-planning tip (44 commits) and wider still.

All three windows return the same criterion-4 answer: **zero** changed lines
matching the support-matrix row/header alternation. The widest, `b0a272f..HEAD`,
is what the ROADMAP records, because a superset window is the stronger claim.

No action needed — noted so the next plan that copies that recipe knows it is a
proxy for the definition and not the definition itself.
