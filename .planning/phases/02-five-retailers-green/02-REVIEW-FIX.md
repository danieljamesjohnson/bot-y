---
phase: 02-five-retailers-green
fixed_at: 2026-08-03T03:00:00Z
review_path: .planning/phases/02-five-retailers-green/02-REVIEW.md
iteration: 1
findings_in_scope: 9
fixed: 8
already_resolved: 1
skipped: 0
deferred: 6
status: all_fixed
---

# Phase 2: Code Review Fix Report

**Fixed at:** 2026-08-03
**Source review:** `.planning/phases/02-five-retailers-green/02-REVIEW.md`
**Iteration:** 1
**Scope:** critical + warning (CR-01, CR-02, WR-01…WR-07). Info deferred.

**Summary:**

| | Count |
|---|---|
| Findings in scope | 9 |
| Fixed this session | 8 |
| Already resolved before this session | 1 (CR-02) |
| Skipped | 0 |
| Info findings deferred | 6 |

Every fix is pinned by a test that was watched failing against the unfixed code
before the fix was written, except CR-01's process reaping, which is not
test-pinnable in-process and is substituted by a controlled live before/after
measurement. The failing output is recorded per finding below.

## Gates

All four hold. Actual output:

| Gate | Before | After |
|---|---|---|
| `.venv/bin/python -m pytest tests/ -q` | 169 passed | **209 passed** |
| `.venv/bin/python -m mypy` | clean, 14 files | **clean, 14 files** |
| `.venv/bin/python scripts/mutation_check.py` | 6/6 | **6/6 caught** |
| `make verify` (systemd-run, service env) | — | **exit 0 — `VERIFY: PASS`, 4/4 controls in stock** |
| `make verify` (plain shell) | — | **exit 0 — `VERIFY: PASS (INCOMPLETE — …)`** |

The two `make verify` results differing is the intended outcome of WR-06, not a
discrepancy. The plain shell has no `BOTY_BROWSER_PATH` (it lives in the service
`EnvironmentFile`), so Best Buy's rung-3 control cannot run there. It now reports
`INCOMPLETE` and names the cause, instead of the old `FAIL — the extractor has
stopped matching`. It is also, deliberately, *not* an unqualified `PASS`: a green
obtained in a shell without the browser environment is now visibly not the same
claim as the systemd one — which is the precise asymmetry behind the false green
that paged Dan earlier in this phase.

Under `systemd-run` with the unit's `EnvironmentFile`, all four controls run and
pass, Best Buy included. That run exercises the new browser teardown and the new
SKU binding against live Best Buy bytes.

---

## Fixed Issues

### CR-01: every browser render leaks a zombie Chrome and a Chrome profile directory

**Commit:** `3911d73`
**Files:** `boty/browser.py`, `tests/test_browser.py`,
`.planning/phases/02-five-retailers-green/deferred-items.md`

**Confirmed live before touching anything.** The reviewer measured 9 zombies at
58 min; independent re-measurement at 71 min found **13 zombies and 204 MB** of
`/tmp/uc_*` profiles — growing, as predicted.

**Applied fix.** `_teardown()` stops the browser, `await`s `proc.wait()` to
actually reap the child, then `rmtree`s the profile — but only when nodriver's
own `uses_custom_data_dir` says nodriver created it, so a caller-supplied profile
is never destroyed.

The timeout was moved to bound the *inner* coroutine rather than the whole
thing. This is a deliberate departure from the review's suggested patch, which
put the reap in a `finally` running under cancellation and reached for
`asyncio.shield` to survive it. Shielding lets the inner task outlive the
cancellation, but the loop is closing immediately afterwards, so the reap still
may not complete. Bounding the work and cleaning up outside that bound means the
teardown's `await` runs in an uncancelled context on every path. `_REAP_TIMEOUT`
keeps the cleanup itself bounded.

**Pinned by** three tests (success path, page-explodes path, caller-supplied
profile). Failing output before the fix:

```
E  AssertionError: the Chrome child was never awaited — SIGTERM without wait()
   leaves a zombie held by this process for the life of the monitor
E  assert None is True
3 failed
```

**Verified by observation, not argument.** Process reaping cannot be pinned by an
in-process test — the fake nodriver has no real child — so it is substituted by
a controlled experiment: three real renders under the service `EnvironmentFile`,
identical in every respect except the code under test.

| | zombies | leaked `uc_` dirs | `Event loop is closed` |
|---|---|---|---|
| unfixed `boty/browser.py` | **3** | **3** | 2 per render |
| fixed | **0** | **0** (`[]`) | **0** |

**And on the deployed unit.** `boty.service` restarted, then left to run through
its browser-driving cycles (Best Buy control, rung 3, 300 s interval):

```
=========== BEFORE (pre-fix code, 71 min uptime) ===========
zombie children:   13
uc_ profile dirs:  13
profile footprint: 204M

=========== AFTER (fixed code, restarted, left to run) ===========
uptime:            847s  (14 min)
browser cycles:    5     (rung-3 launches logged since restart)
zombie children:   0
all children:      (none)
uc_ profile dirs:  0
profile footprint: 0
Event loop is closed tracebacks: 0
service state:     active
```

Prior rate was ~1 zombie and ~17 MB per cycle. Five browser cycles would have
produced five of each; it produced none, and two readings 2 minutes apart
(728 s and 847 s) both read zero. **The count is not climbing** — which was the
stated bar for calling this fixed.

**`deferred-items.md` corrected.** The `Event loop is closed` entry called the
tracebacks cosmetic; they were this leak surfacing — the loop was closing before
the child was reaped, which is why the subprocess transports finalised against a
dead loop. The entry is struck through and kept, with its original text preserved
and the wrong reasoning named, rather than deleted. The lesson worth keeping is
that "the exit code is unaffected" is not evidence that nothing is wrong.

---

### CR-02: a committed fixture publishes the capturing machine's public IP and geolocation

**Status: ALREADY RESOLVED — no action taken this session, as instructed.**

Resolved before this session: the client identity was scrubbed from
`tests/fixtures/bestbuy/unresolved-sku.html`, a guard test added
(`test_no_fixture_leaks_the_capturing_hosts_identity` in `tests/test_fetch.py`,
which scans every committed fixture for CDN client-IP echoes and EdgeScape
geolocation), and the values purged from git history with two `git filter-repo`
passes and a force-push.

Verified intact: that guard test is present and green in the 209-test run.

---

### WR-01: a Chrome spawned by a failing `nodriver.start()` is never stopped at all

**Commit:** `966de31`
**Files:** `boty/browser.py`, `tests/test_browser.py`

`nodriver.start()` spawns Chrome and only then polls DevTools five times over
~2.75 s before raising, without terminating what it spawned. These are *live*
browsers with a real RSS, not zombies.

The review's suggested patch (`browser = None` outside the `try`) does not
actually close this: when `start()` itself raises there is no return value, so
`browser` stays `None` and the `finally` has nothing to stop. The handle that
does exist is nodriver's instance registry — it adds the instance the moment the
subprocess exists, *before* the handshake that fails. `_registered()` reads it
defensively (it is an internal of an optional dependency) and the teardown falls
back to the registry diff whenever the normal path produced nothing.

**Also fixed in the same commit:** torn-down browsers are now discarded from that
registry. It is the same never-exits root cause a third time — nodriver clears
the set only at `atexit`, so `boty watch` accumulated one dead `Browser` object,
with its Config and connection objects, per poll cycle.

**Pinned by** two tests. Failing output before:

```
E  AssertionError: a half-started browser was never stopped
E  AssertionError: 3 dead Browser instance(s) still registered after 3 renders —
   this set is only cleared at interpreter exit, which a monitor never reaches
```

`_render`'s docstring claimed the browser was stopped "on every path including
cancellation". Corrected to name the case it used to skip.

---

### WR-02: the sandbox opt-out fires on `BOTY_BROWSER_NO_SANDBOX=0`

**Commit:** `c1664ac`
**Files:** `boty/browser.py`, `tests/test_browser.py`, `README.md`

`sandbox = not os.environ.get(...)` treated any non-empty value as "disable" —
including the four ways a person writes "no". Now an allow-list: `1`, `true`,
`yes`, `on` and nothing else. Recognised negatives pass quietly; an unrecognised
value resolves to *no* and warns, naming the value, so nobody is left believing a
flag is doing something.

Second hole in the same claim: nodriver auto-disables the sandbox under root and
logs at INFO, below boty's WARNING default — so as root the launch said
`sandbox=True`, nodriver ignored it, and the log showed a sandbox that was not
there. Now warned explicitly on `geteuid() == 0`.

**Pinned by** 15 parametrised cases plus two log assertions. **10 failed** before
the fix:

```
E  AssertionError: BOTY_BROWSER_NO_SANDBOX='0' produced sandbox=False;
   only an explicit yes may downgrade isolation
   … same for 'false', 'no', 'off', 'False', 'OFF', '   ', 'banana'
E  AssertionError: running as root disables Chrome's sandbox and nothing said so
```

**Live check on this host.** Confirmed under the service `EnvironmentFile` that
the configured value is still read as an opt-in and rendering is unchanged — the
existing warning still fires, and no "not a recognised yes/no value" warning
appears. No behaviour change on danserver; no risk of this fix breaking the
deployed unit's Chrome launch. README updated with the accepted values and the
root caveat.

---

### WR-03: nothing binds Best Buy's rendered page back to the requested SKU

**Commit:** `2885c8e`
**Files:** `boty/parse.py`, `boty/retailers.py`, `tests/test_retailers.py`

The most product-critical finding, and the one where the review's suggested fix
does not close its own scenario.

The review proposed a page-level substring check (`f'"sku":"{sku}"' in html`).
The requested SKU appears **71 times** in the shipped Best Buy control fixture —
recommendation rails, breadcrumbs, "customers also viewed". So a search-results
page listing the requested product *among eleven others* contains it too, passes
the check, and `_pick` still returns the cheapest offer on the page. The scenario
the finding describes survives its own remedy.

The binding therefore has to be at the node, not the page:
`parse.ldjson_offers(html, sku=...)` reads offers only from the `Product` whose
`sku` is the one requested. This is the same reasoning `_WALMART_PRODUCT_PATH`
already records in the same module — *"a generic walk happily reports a $12
screen protector as your restock"*. Best Buy went through the generic walk.

Only Best Buy passes a `sku`. GameStop and Nintendo are addressed by URL, where
the page that came back *is* the product requested; their behaviour is unchanged.

**Pinned by** four tests. Failing output before — the first line is the finding:

```
E  AssertionError: read in_stock at $9.99 from a page that does not contain the
   requested SKU at all
E  AssertionError: read $9.99 — the cheapest offer on the page, not the
   requested product's
E  AssertionError: a SKU that merely appears in this page's recommendation rails
   was read as the page's own product
E  AssertionError: assert '6577129' in 'no structured stock data found (page
   shape changed?)'
4 failed
```

A $9.99 HDMI cable, reported as the Pokémon GO Plus +, under the watch's own
name, alertable beneath an $80 ceiling, with health and dashboard both green.

**Carries IN-03 with it** (the review predicted it would): an unresolved SKU is
now diagnosed as `sku … did not resolve to a product page` instead of `page shape
changed?`, which pointed the reader at a working extractor.

Live Best Buy control still reads IN_STOCK at $59.99 under `systemd-run`, so the
binding did not cost the control its green.

---

### WR-04: the status page never shows `degraded`

**Commit:** `a895c35`
**Files:** `served/boty/index.html`, `tests/test_dashboard.py` (new)

`status.write` publishes `degraded` and calls it "a contract with the dashboard".
The page rendered neither `rung` nor `degraded`, so Best Buy's control was a green
dot at $59.99, indistinguishable from GameStop's rung-1 row — the contract met in
letter, defeated in the one place a human reads.

The tag is styled deliberately louder than `control`: control is an ordinary
label that should recede, degraded is a claim about what the number beside it is
worth.

`tests/test_dashboard.py` is new and pins the *consuming* half of a contract that
was previously asserted only at the producing end — which is exactly how it
stayed unimplemented. Failing output before:

```
E  AssertionError: the dashboard never mentions `degraded` at all
E  AssertionError: no `.tag.degraded` rule — a degraded tag styled like every
   other tag does not tell a reader to weigh the number differently
```

**Verified by looking at it.** Screenshotted the live page (the service serves
this directory directly) at phone width: the Best Buy control now carries an
amber `DEGRADED` beside its grey `CONTROL`, and no other row does.

---

### WR-05: retailer-controlled strings are interpolated into the dashboard's `innerHTML`

**Commit:** `d3b92cb`
**Files:** `served/boty/index.html`, `tests/test_dashboard.py`

**Demonstrated as exploitable, not argued.** Served the pre-fix page against a
`status.json` whose seller name was `<img src=x onerror="document.title=…">` and
drove a real browser at it:

```
PRE-FIX   document.title = "BANNER-XSS"     <- arbitrary JS executed
POST-FIX  document.title = "bot-y"          <- rendered as text
```

Escapes at the sink, once, over five characters, applied to every interpolated
value including operator-controlled ones — "these three but not those two" does
not survive the next edit to the template. The test asserts the general rule over
every `${…}` in the file, so a newly added raw retailer field fails there rather
than shipping.

Three tests, all failing beforehand:

```
E  AssertionError: no `esc` helper defined
E  AssertionError: retailer- or config-controlled strings reach `innerHTML`
   unescaped: r.reason, r.retailer, w.detail, w.name, w.retailer, w.url
E  AssertionError: r.retailer is interpolated into the health banner unescaped
```

---

### WR-06: a fresh clone that follows the README fails `make verify`, and the gate blames the detector

**Commit:** `a01393e`
**Files:** `scripts/control_check.py`, `scripts/mutation_check.py`, `Makefile`,
`boty/browser.py`, `README.md`, `tests/test_control_check.py`,
`tests/test_verify_makefile.py`

**Reproduced in a genuinely clean venv** (`python3 -m venv` + `pip install -e
'.[dev]'`, no browser extra), before and after:

```
BEFORE                                                      exit 1
  control check: FAIL — 1/4 control(s) not reading IN_STOCK
    bestbuy/CONTROL: unknown — fetch failed: the browser transport needs the
    optional extra … (ModuleNotFoundError: No module named 'nodriver')
    This is a statement about the DETECTOR, not about the market.
    …the extractor has stopped matching…
    Next: re-capture the fixture with `boty capture-fixture …`

AFTER                                                       exit 4
  control check: 1/4 control(s) could not run on THIS HOST
    This says nothing about the DETECTOR. The browser rung (rung 3) needs
    the optional `browser` extra and a Chrome/Chromium binary…
      .venv/bin/pip install -e '.[browser]'
  control check: INCOMPLETE — 3/4 control(s) ran, all in stock; 1 could not run here

  $ make verify   ->   exit 0
  VERIFY: PASS (INCOMPLETE — some controls could not run on this host;
                the detectors they cover are unverified here)
```

**Did not take the review's first option** — adding `browser` to the `dev` extra.
It contradicts a decision recorded in `STATE.md` (nodriver is AGPL-3.0 to this
project's MIT; a contributor working on the HTTP retailers must never be forced
to pull a browser stack), and it would not work anyway, since the rung also needs
a Chrome binary that no extra can install.

New exit code **4 (INCOMPLETE)**, for the same reason 3 (SKIPPED) exists. Not 1 —
nothing is broken, and failing contradicts both the "exits 0 on a healthy tree"
criterion and the works-from-a-fresh-clone NFR. Not 0 — those detectors were not
verified, and "I could not tell" must never read as "fine". Not 3 — that means
*nothing* ran; this means *some* did. The Makefile prints a distinct verdict for
each, and `test_verify_makefile.py` pins that an incomplete run is not reported
with the offline wording.

The markers live in `boty/browser.py` beside the messages they match and are
**imported** by `control_check`, not retyped, so they cannot drift; a test drives
the real `fetch_rendered` failure paths and asserts each produced detail is still
recognised. Bot walls stay failures — being blocked by a retailer is the monitor
not working, as the script's own docstring insists. Host gaps are also no longer
retried, since a missing extra will not appear three seconds later.

**Also in this commit:** `served/` added to the mutation sandbox. The new
`tests/test_dashboard.py` reads `served/boty/index.html`, and a sandbox missing it
fails the baseline with *"This is not a result. Nothing was proved about the test
suite either way."* Caught by running the real `make verify` rather than pytest
alone — the exact reason the phase insists on the former.

---

### WR-07: the Akamai block markers are pinned only against a hand-written reconstruction

**Commit:** `cbd92e6`
**Files:** `docs/retailer-evidence.md`, `tests/test_fetch.py`

**Re-probed kohls.com. Both markers appear verbatim; neither needed correcting.**

```
URL     https://www.kohls.com/product/prd-4351200/nintendo-switch-2.jsp
STATUS  200            <- again a wall, not an error
BYTES   2,377
sec-if-cpt-container      1 occurrence, byte 213
scf-akamai-protected-by   1 occurrence, byte 849
```

Note `<p class ="scf-akamai-protected-by">` — the stray space before `=` is
Akamai's own, which is why the phrase is the bare class name and not
`class="…"`. Full excerpts with surrounding markup and the response size are now
in `docs/retailer-evidence.md`, recorded the way the Imperva entries are.

Went further than the review asked: the test constant `AKAMAI_CHALLENGE` was
replaced with the retailer's **actual bytes** (session nonce redacted), so the
test is no longer self-referential, plus a test asserting each phrase appears in
those bytes. Proved the pin now bites by re-running the reviewer's own
hypothetical — real container id `sec-cpt-if`, our phrase wrong:

```
E  Failed: DID NOT RAISE Blocked
```

which the old reconstruction could never have produced, because it contained
whatever we believed the marker to be.

Did **not** add the bare vendor name as a third marker: `akamai` occurs 10 times
in this challenge, but also 33 times on Best Buy's working search page and 15
times in Walmart's CSP header.

---

## Skipped

None. Every in-scope finding was fixed.

## Deferred (Info — out of scope for this pass)

| ID | Summary | Note |
|---|---|---|
| IN-01 | `mutation_check.py` docstring still says "three mutations"; there are six | Also in `deferred-items.md` |
| IN-02 | Duplicated rationale comment on `SANDBOX_CONTENTS` | Touched that comment block to add `served`; left the duplication alone to respect scope |
| IN-03 | Best Buy SKU miss reported as "page shape changed?" | **Resolved incidentally by WR-03**, as the review predicted |
| IN-04 | `control_check --offline` help text says "exit 0", returns 3 | Now also stale w.r.t. exit 4 |
| IN-05 | Fixture path components unsanitised (`capture()` path traversal) | Phase 1 IN-06, still open |
| IN-06 | Repo ships changedetection.io compose + root-owned `datastore/` | Relevant to Phase 4 |

## Notes for the next pass

- **IN-04 got slightly worse.** WR-06 added exit code 4, so `--offline`'s help
  text ("skip the live check entirely and exit 0") is now wrong about two codes
  rather than one. Worth folding into IN-04 whenever it is picked up.
- **The `_render` seam is preserved.** `tests/conftest.py` still patches
  `boty.browser._render` by name, and its signature is unchanged. The guard's own
  self-test (`test_guard_blocks_the_browser_transport`) still fires — verified
  green in every run above, and the suite never launched a real browser during
  any of it. Live probes were run deliberately and separately, outside pytest.
- **`make verify` in a plain shell now says INCOMPLETE, not PASS.** This is worth
  knowing before trusting a green: only the `systemd-run` form exercises Best
  Buy. That asymmetry is now visible in the verdict rather than silent.

---

_Fixed: 2026-08-03_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
