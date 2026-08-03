---
phase: 02-five-retailers-green
verified: 2026-08-03T03:11:16Z
status: human_needed
score: 6/6 must-haves verified
overrides_applied: 0
method: >
  Execution, against the AMENDED ROADMAP (2026-08-02). Every success criterion was
  proved by running a command under the environment the SERVICE sees
  (systemd-run + EnvironmentFile), not a developer shell. Both Criticals were
  re-measured independently rather than read from 02-REVIEW-FIX.md. Gates were
  proved to BITE by breaking the thing they guard and observing a non-zero exit,
  then restoring and confirming a clean tree.
scope_note: >
  The "five or more retailers" criterion was MOVED to Phase 3 by Dan's explicit
  decision, recorded in ROADMAP.md and docs/retailer-evidence.md. Phase 2 was NOT
  assessed against a retailer count. It WAS assessed against the honesty of the
  four-retailer outcome, which is the thing that decision put at risk.
human_verification:
  - test: >
      With a real BESTBUY_API_KEY set in ~/.config/boty/env, run
      `sudo systemd-run --pipe --quiet --uid=dan
      --property=EnvironmentFile=/home/dan/.config/boty/env
      --property=WorkingDirectory=/home/dan/CodeProjects/pokemongoplusplus
      /home/dan/CodeProjects/pokemongoplusplus/.venv/bin/boty check -c config/products.yaml`
      and confirm the Best Buy control row loses its `[degraded]` tag and
      served/boty/status.json records `"rung": "api", "degraded": false`.
    expected: >
      Same SKU, same IN_STOCK verdict, same $59.99 price, no browser launched, no
      `[degraded]` tag.
    why_human: >
      Requires a credential nobody on this project can obtain. Best Buy's developer
      signup needs manual approval AND rejects free email domains — which is the
      documented reason (REQ-04) the API is an optional enhancement rather than the
      primary path. The dispatch, the rung tagging and the flag semantics ARE pinned
      offline (`test_a_key_upgrades_the_same_watch_from_browser_to_api` asserts
      rung=API / degraded=False / identical verdict and price), so what is unproven
      is narrowly the live API response shape, not the wiring. If the key is
      permanently unobtainable, accept this as an override rather than leaving it
      open forever.
  - test: >
      Leave boty.service running for 6–12 hours with the Best Buy rung-3 control
      configured, then run
      `ps --ppid $(systemctl show boty.service -p MainPID --value) -o pid,stat,comm=`
      and `sudo find /tmp/systemd-private-*boty.service*/tmp -maxdepth 1 -name 'uc_*' | wc -l`.
    expected: >
      Zero zombie (STAT Z) children and zero `uc_*` profile directories, with the
      counts flat between two readings hours apart — not merely low.
    why_human: >
      This is the CR-01 class and it is the one gap `make verify` structurally
      cannot close. `make verify` runs a one-shot process; zombie accumulation and
      profile growth are properties of a daemon over hours. The three teardown tests
      drive a FAKE nodriver, so they pin that `_teardown` is CALLED, not that a real
      Chrome child is reaped — 02-REVIEW-FIX.md says so itself ("not test-pinnable
      in-process"). I measured 0 zombies / 0 private-tmp profiles at 18 minutes and
      4 browser cycles, and a controlled render created and removed its profile
      cleanly. That is strong but it is shorter than the 71-minute window in which
      the original leak reached 13 zombies and 204 MB. Only elapsed time closes it.
deferred:
  - truth: "boty check reports five or more retailers with no health warnings"
    addressed_in: "Phase 3"
    evidence: >
      ROADMAP.md Phase 3 SC5, verbatim: "carried over from Phase 2, which reached
      four because no fifth reachable retailer stocks the GO Plus +. Target or
      Amazon landing satisfies it." Amended 2026-08-02 by Dan's explicit decision.
  - truth: "Six Info findings from 02-REVIEW.md (IN-01…IN-06) remain open"
    addressed_in: "Phase 4 / opportunistic"
    evidence: >
      02-REVIEW-FIX.md frontmatter `deferred: 6`, `status: all_fixed` for the 9
      in-scope Critical+Warning findings. IN-03 was resolved incidentally by WR-03.
      I confirmed IN-01 is genuinely still open (scripts/mutation_check.py:7 still
      says "three specific things"; there are six) — the deferral is honest, not a
      silent claim of completion.
---

# Phase 2: Five Retailers Green — Verification Report

**Phase Goal (amended 2026-08-02):** Every retailer we can actually reach reporting trustworthy stock for the GO Plus +, each control-verified.
**Verified:** 2026-08-03T03:11:16Z
**Status:** human_needed — 6/6 criteria verified by execution; two items cannot be closed by an exit code
**Re-verification:** No — initial verification

---

## Executive summary

All six amended success criteria hold, and every one of them was proved by running
a command and reading its output rather than by reading a SUMMARY. The headline
number Dan cares about — `make verify` under the service's own environment — is
**exit 0, `VERIFY: PASS`, 209 tests, mypy clean over 14 files, 8 fixtures ok,
4/4 live controls in stock, 6/6 mutations caught.**

The four-retailer outcome is honest. I checked the three ways it could have been
dishonest and found none of them:

- Pokémon Center's rung-4 evidence is **specific and falsifiable**, not hand-waving.
- **Nothing was padded in.** Micro Center was probed, viable, and declined — and I
  independently re-probed Micro Center to confirm the market fact that justified
  the decline.
- Best Buy's control-only status is recorded in the **three places a reader
  actually looks**, not buried in a planning file.

The residual risk is not in the retailers. It is that this phase's own gates did
not catch either Critical or the false green — see
[Is the verification story trustworthy?](#is-the-verification-story-trustworthy)
below, which is the part of this report worth reading twice.

---

## Goal Achievement

### Observable Truths (ROADMAP success criteria, as amended)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Best Buy reports stock with NO credentials, flagged DEGRADED; and without the DEGRADED flag when an API key IS present | ✓ VERIFIED | **No-credential half proved live.** Under `systemd-run` with the unit's `EnvironmentFile` (no `BESTBUY_API_KEY` present), `boty check` printed `● bestbuy CONTROL — Pokémon Let's Go, Pi $59.99 ld+json: InStock from Best Buy [control] [degraded]`, and `served/boty/status.json` records `rung=browser, degraded=True`. **API half pinned offline:** `test_a_key_upgrades_the_same_watch_from_browser_to_api` asserts the same watch yields `rung=API, degraded=False`, identical `IN_STOCK` and identical `59.99`. Live API run is a human item — no key is obtainable |
| 2 | Nintendo reports stock for a real product; Pokémon Center does the same or is documented unreachable with the evidence | ✓ VERIFIED | **Nintendo live, twice:** `○ nintendo Pokémon GO Plus + $54.99 ld+json: OutOfStock from Nintendo of America Inc.` and `● nintendo CONTROL — Nintendo HDMI cable $7.99 ... InStock`, `rung=tls, degraded=False`. **Pokémon Center documented REFUSED** with a 6-row probe table carrying HTTP codes, byte counts (858 B DataDome 403; 6,183 B Imperva at HTTP **200**, byte-identical across two products; 1,085 B `_Incapsula_Resource` after a 120 s backoff), the three Incapsula cookie names, two transports, two WAF vendors, a quoted Terms-of-Use prohibition, a `robots.txt` excerpt, and a review of ~17 prior-art projects. Verified absent from code: no `pokemoncenter` in `FIRST_PARTY`, no watch in `config/products.yaml`, no `tests/fixtures/pokemoncenter/` |
| 3 | Every retailer has at least one control watch, and `boty check` shows all controls in stock | ✓ VERIFIED | Live, service env: **4/4 controls `in_stock`**, `healthy: True` in `status.json`, **zero health-warning lines** in `boty check` output. Enforced mechanically at three layers, each with a test: `scripts/control_check.py` computes `configured - verified` before any request (`test_a_retailer_with_no_control_watch_fails_the_gate`), `assess_health` fails a retailer whose control cannot be read (`test_retailer_with_no_control_watch_is_unhealthy`), and `test_every_configured_retailer_has_a_control_watch` pins the shipped config |
| 4 | Each new adapter has fixture-backed tests from Phase 1 | ✓ VERIFIED | `tests/fixtures/bestbuy/{pikachu-control,unresolved-sku}.{html,json}` (1.1 MB / 922 KB) and `tests/fixtures/nintendo/{goplusplus,hdmi-control}.{html,json}` (416 KB / 384 KB), every one with a sidecar carrying `captured_at`, `status`, `bytes`, `note`, `transport`. The `fixtures` stage reports all 8 `ok` at 0d. Both the **hit** and the **miss** path are frozen for Best Buy, which is unusual and correct. Tests named per adapter: `test_bestbuy_control_fixture_is_in_stock_priced_and_alertable`, `test_bestbuy_page_with_no_product_markup_is_unknown_not_out_of_stock`, `test_nintendo_goplusplus_reads_out_of_stock_at_msrp`, `test_unparseable_nintendo_page_is_unknown_not_out_of_stock`, +30 more |
| 5 | The support matrix records which escalation rung each retailer landed on | ✓ VERIFIED | `README.md` retailer table has a **Rung** column filled for all six rows: GameStop 1, Walmart 1, Nintendo 1, Best Buy **3 (2 with a key)**, Pokémon Center **4**, Target —. Each row also carries Method and Status, and the table links to `docs/retailer-evidence.md`. `Rung` is not just prose: `boty/models.py` defines the enum, `status.py` serialises it per watch, and `test_every_watch_entry_carries_a_rung_and_a_degraded_flag` pins it |
| 6 | `make verify` exits 0 | ✓ VERIFIED | **Executed under the service's own environment.** `209 passed in 0.88s` · `Success: no issues found in 14 source files` · `8 fixture(s) ... all ok` · `control check: PASS — 4/4 controls in stock` · `mutation check: 6/6 mutations caught` · `VERIFY: PASS` · **exit 0** |

**Score: 6/6 truths verified.**

---

## Behavioral Spot-Checks

Every criterion above was executed. These are the runs behind them.

| Behavior | Command | Result | Status |
|---|---|---|---|
| `make verify` green under the environment systemd gives the service | `sudo systemd-run --pipe --quiet --uid=dan --property=EnvironmentFile=/home/dan/.config/boty/env --property=WorkingDirectory=... /usr/bin/make verify` | `VERIFY: PASS`, **exit 0**; 209 tests, mypy 14 files, 8 fixtures ok, 4/4 controls in stock, 6/6 mutations caught | ✓ PASS |
| The false-green asymmetry is now visible, not silent | `env -u BOTY_BROWSER_PATH -u BOTY_BROWSER_NO_SANDBOX make verify` | `control check: INCOMPLETE — 3/4 control(s) ran, all in stock; 1 could not run here` → `VERIFY: PASS (INCOMPLETE — some controls could not run on this host; the detectors they cover are unverified here)`, exit 0 | ✓ PASS |
| Live controls, all four retailers | (control stage of the run above) | `in_stock` × 4: gamestop $549.99, walmart $2.42, **bestbuy $59.99**, nintendo $7.99 | ✓ PASS |
| `boty check` end to end, service env | `systemd-run ... .venv/bin/boty check -c config/products.yaml` | 10 watches, 4/4 controls green, Best Buy tagged `[control] [degraded]`, **no health warnings**, exit 0 | ✓ PASS |
| Published status payload | `json.load(open('served/boty/status.json'))` | `healthy: True`; retailers `['bestbuy','gamestop','nintendo','walmart']`; bestbuy control `rung=browser, degraded=True`; other three `rung=tls, degraded=False` | ✓ PASS |
| The gate BITES — deliberate break | Flipped the unparseable-page verdict in `boty/retailers.py` from `UNKNOWN` to `OUT_OF_STOCK` (the exact failure this project exists to prevent), then `make verify` | `3 failed, 206 passed` — incl. the **new Nintendo** test `test_unparseable_nintendo_page_is_unknown_not_out_of_stock` → `VERIFY: FAIL (tests)`, **exit 2** | ✓ PASS |
| Tree restored clean after the break | `git status --porcelain` / `git diff --stat` / pytest | Both empty; `209 passed` | ✓ PASS |
| CR-02 guard is not vacuous — it BITES | Appended `true-client-ip: 192.0.2.1 city=REDACTED zip=00000` to a shipped fixture, ran the guard test | `FAILED test_no_fixture_leaks_the_capturing_hosts_identity` — flagged all four markers. Restored; tree clean; test passes | ✓ PASS |
| CR-02 purge is real across ALL history | `git grep -E "true-client-ip[^0-9]{0,12}[0-9.]+" $(git rev-list --all) -- 'tests/fixtures/*'` and the geolocation equivalent, over 622 objects | **No matches.** No client IP, no EdgeScape geolocation anywhere in history | ✓ PASS |
| CR-01 — zombies on the deployed unit | `ps --ppid 287281 -o stat=` at 18 min uptime / 4 logged browser cycles | **0 zombies, 0 children of any kind.** Pre-fix rate was ~1 per cycle | ✓ PASS |
| CR-01 — leaked profiles on the deployed unit | `sudo find /tmp/systemd-private-*boty.service*/tmp -maxdepth 1 -name 'uc_*'` (the unit sets `PrivateTmp=true`, so this is where its profiles would be) | **0** | ✓ PASS |
| CR-01 — controlled single render | one `fetch_rendered` under the service `EnvironmentFile`; `/tmp/uc_*` counted before and after | 1,095,371 bytes rendered; **20 → 20**, no new directory | ✓ PASS |
| WR-04 — the dashboard actually shows `degraded` | Headless screenshot of `http://127.0.0.1:8821/` at 430 px, then read the PNG | Best Buy control row carries an **amber `DEGRADED`** beside its grey `CONTROL`; **no other row does**; banner reads "All detectors verified by control products."; all four control dots green | ✓ PASS |
| WR-05 — dashboard escaping | `grep` for the `esc` helper and every `${…}` sink in `served/boty/index.html` | `const esc = s => String(s ?? '').replace(/[&<>"']/g, ...)`; the only un-escaped interpolation left is `${w.availability}`, an internal enum, used as a CSS class | ✓ PASS |
| Honesty — Micro Center genuinely does not carry the product | One polite `boty.fetch.get` of Micro Center's search for `pokemon go plus` | 19 results, 22 unique titles — sleeved booster packs, a Razer keyboard, microSD cards, Switch titles. **Zero GO Plus + hardware.** The evidence log's reason for declining it is corroborated | ✓ PASS |

---

## Honesty of the four-retailer outcome

This is what the amended roadmap put at risk, so it got the most scrutiny.

### Is Pokémon Center's rung 4 real evidence, or hand-waving?

**Real, and unusually specific.** `docs/retailer-evidence.md` records six probes
across two products, two URL forms and two transports, each with the observation
rather than the conclusion: a DataDome 403 at 858 B; an Imperva `Pardon Our
Interruption` at **HTTP 200**, 6,183 B, byte-identical across two different
products; the three `incap_*`/`visid_incap_*`/`nlbi_*` cookie names that a warmed
session set and that did not help; a rung-3 refusal at 1,085 B with an
`_Incapsula_Resource` iframe after a 120-second backoff. The homepage passed rung 1
**twice**, before and between the refusals, which is what rules out an IP ban and
localises the wall to `/product/*`.

Two things raise it above a technical shrug:

1. **The decisive reason given is the Terms of Use, not the wall.** The doc quotes
   the prohibition on "data mining, robots or similar data gathering" and on
   applications interacting with the service without written consent, and states
   plainly that this is *broader* than the robots.txt finding and supersedes it.
   That is the harder and more honest position — a wall can fall, a written
   prohibition does not — and it comes with an explicit instruction not to re-probe
   waiting for enforcement to lapse.
2. **The prior-art review is a negative result stated as one.** ~17 projects claim
   to read Pokémon Center; exactly one has a written record of a per-product stock
   read, and it needed a human to clear a challenge by hand. Four actively
   maintained 2026 multi-retailer Pokémon monitors were checked and **none**
   includes pokemoncenter.com.

Verified in code, not just prose: no `FIRST_PARTY` entry, no config watch, no
fixture directory. bot-y makes no requests to pokemoncenter.com. The name survives
only in comments and in `boty/fetch.py`'s note on where the Imperva block phrase
came from.

### Was any retailer slipped in to raise the count?

**No.** `config/products.yaml` carries exactly four retailer keys — gamestop,
walmart, bestbuy, nintendo — and `status.json` confirms the same four at runtime.
Seven fifth-retailer candidates are recorded with verdicts; Micro Center is the one
that was viable (rung 1, config-only, availability confirmed to be a real signal
rather than a constant) and it was **explicitly declined** on the grounds that it
does not carry the GO Plus + and could only ever be control-only.

I did not take that on trust. A single search of Micro Center for the product
returned 19 results and **zero GO Plus + hardware** — booster packs, a Pokémon-edition
keyboard, microSD cards. The decline stands on a market fact I re-confirmed.

`config/products.yaml` also contains a written-down refusal in the file itself: a
comment block explaining that there is no `retailer: pokemoncenter` entry, why a
watch there "would look entirely plausible — and would never read anything," and
where the evidence lives. That is the padding pressure being resisted in the exact
file where padding would happen.

### Is Best Buy's control-only status findable, or buried?

**Findable, in all three places a reader would look**, with the reason attached
each time:

- **README.md**, in the support matrix's Status cell: *"Best Buy does not appear to
  stock the GO Plus + itself, so only a control is configured."*
- **config/products.yaml**, at the Best Buy watches: a comment stating it is *"a
  finding rather than an omission,"* naming the disproved SKU `6577129` and the
  consequence (*"a permanent UNKNOWN and a permanent health warning"*).
- **docs/retailer-evidence.md**, under a heading that says it outright: *"Does Best
  Buy sell the GO Plus +? — settled: no watch shipped"*, with the five product URLs
  the saved search pages actually contained.

The README goes further than required and states the shortfall in its own voice:
**"Four working retailers, not five."** A phase that wanted to hide this would not
put that sentence above the install instructions.

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `boty/browser.py` (376 lines) | Rung-3 transport, `_render` seam, bounded teardown | ✓ VERIFIED | `_teardown` stops, `await proc.wait()` under `_REAP_TIMEOUT`, `rmtree`s the profile only when `uses_custom_data_dir` is False, and discards from nodriver's instance registry. Wired: `retailers.check_bestbuy_browser` imports `fetch_rendered`; `tests/conftest.py` patches `_render` by name |
| `boty/retailers.py` (430 lines) | Best Buy browser + API rungs, SKU binding, Nintendo `FIRST_PARTY` | ✓ VERIFIED | `check_bestbuy_browser` / `check_bestbuy_api` both tag their rung on **every** path including errors; `_verdict_from_html` takes `sku=` and binds the verdict to the requested Product node (WR-03); `_redact_host_paths` keeps `$HOME` out of published details |
| `boty/models.py` | `Rung` enum, `Result.degraded` | ✓ VERIFIED | Three members (TLS/API/BROWSER), deliberately not a fourth `Availability` and deliberately not fed into `Health` — both choices documented with the failure they prevent. Pinned by M6 in the mutation set |
| `boty/status.py` + `served/boty/index.html` | `rung`/`degraded` published AND rendered | ✓ VERIFIED | Producing end pinned by `test_a_browser_reading_serialises_as_degraded`; **consuming** end pinned by the new `tests/test_dashboard.py`; and confirmed visually by screenshot |
| `config/products.yaml` | Watches + a control for every configured retailer | ✓ VERIFIED | 10 watches / 4 retailers / 4 controls / 3 transition watches. Best Buy's `target` is a SKU (serves both rungs from one entry); Nintendo's is a URL |
| `tests/fixtures/{bestbuy,nintendo}/` | Frozen pages with sidecars | ✓ VERIFIED | 4 captures, 384 KB–1.1 MB, all with sidecars, all `ok` at 0d |
| `docs/retailer-evidence.md` (699 lines) | Ladder evidence per retailer | ✓ VERIFIED | Best Buy, Nintendo, Pokémon Center each end in exactly one bold Verdict line; plus a fifth-retailer candidate table and a "a browser is not a strict upgrade" section recording that headless Chrome is **Cloudflare-walled by GameStop**, which rung 1 reads on every verify |
| `README.md` | Support matrix with rungs | ✓ VERIFIED | Rung column complete; three-flavour verdict table (`PASS` / `PASS (INCOMPLETE)` / `PASS (OFFLINE)`); the systemd-run recipe and an explicit warning that `env -i` is the wrong check |
| `Makefile` | Exit codes 0/1/3/4 with distinct verdicts | ✓ VERIFIED | Exit 4 (INCOMPLETE) proved live in the plain-shell run; the comment block explains why neither 0 nor 1 nor 3 was correct |
| `tests/fixtures/pokemoncenter/` | *(02-04 plan artifact)* | ⊘ N/A — correctly absent | The plan's own truth carried an OR branch for a REFUSED verdict. `boty.fixtures.capture` propagates `Blocked` and the CLI refused to write a challenge page to disk — the mitigation firing live. A 6 KB Imperva interstitial saved as a fixture would have made a test suite assert against a bot wall while looking green |
| `boty/retailers.py` contains `"pokemoncenter"` | *(02-04 plan artifact)* | ⊘ N/A — correctly absent | Same OR branch. Adding a `FIRST_PARTY` key for a retailer with no watch would be dead config that makes the support surface look larger than it is |

---

## Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `config/products.yaml` (bestbuy) | `check_bestbuy_browser` | `cli._make_checker` bestbuy arm, no key | ✓ WIRED | Proved live end to end — the YAML SKU `6216393` produced `InStock $59.99 [degraded]` through a real browser |
| `config/products.yaml` (bestbuy) + `BESTBUY_API_KEY` | `check_bestbuy_api` | same `_make_checker`, key present | ✓ WIRED (offline) | `test_a_key_upgrades_the_same_watch_from_browser_to_api`. Live run is a human item |
| `scripts/control_check.py` | `cli._make_checker` | the gate builds its checker with the SAME function the monitor uses | ✓ WIRED | Deliberate, and documented in `_make_checker`'s docstring: a gate that routed differently would prove something about a code path nobody runs |
| `scripts/control_check.py` | `config/products.yaml` | `configured - verified`, before any request | ✓ WIRED | `unverified` at line 177; `test_a_retailer_with_no_control_watch_fails_the_gate` |
| `boty/browser.py` markers | `scripts/control_check.py` | **imported**, not retyped, so they cannot drift | ✓ WIRED | This is what makes exit 4 distinguish a host gap from a broken detector |
| `Result.rung` | `served/boty/status.json` → `index.html` | per-watch payload → `.tag.degraded` span | ✓ WIRED | Producing end, consuming end, and the rendered pixels all confirmed |
| `tests/conftest.py` | `boty.browser._render` | autouse network guard patches by name | ✓ WIRED | `test_guard_blocks_the_browser_transport` self-tests it; the 209-test suite never launched a browser in any run above |
| `boty.fetch.BLOCK_PHRASES` | real retailer bytes | Imperva + Akamai markers pinned to captured bytes | ✓ WIRED | `AKAMAI_CHALLENGE` is now the retailer's actual 2,377-byte markup (nonce redacted) rather than a hand-written reconstruction, and a fixture-replay test asserts no shipped fixture became newly "blocked" |

---

## Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Produces real data | Status |
|---|---|---|---|---|
| `served/boty/index.html` | `data.watches[]` | `served/boty/status.json`, written by `status.write` from live `Result`s | Yes — screenshot shows four live prices ($549.99 / $2.42 / $59.99 / $7.99) and four green dots | ✓ FLOWING |
| `boty check` report | `results` | `run_once(cfg.watches, checker, state)` → real fetches | Yes — 10 rows, real prices, real seller attributions | ✓ FLOWING |
| `scripts/control_check.py` | control results | same `_make_checker`, live | Yes — 4/4 in stock with prices and sellers | ✓ FLOWING |
| Best Buy control | `offers` from the rendered page | `fetch_rendered` → 1,095,371 real bytes → `ldjson_offers(html, sku='6216393')` | Yes — and bound to the requested SKU, not the cheapest offer on the page | ✓ FLOWING |

---

## Requirements Coverage

| Requirement | Source plan | Status | Evidence |
|---|---|---|---|
| **REQ-04** — Best Buy's primary path works without credentials; API is an optional upgrade that drops DEGRADED | 02-01, 02-02, 02-03 | ✓ SATISFIED | Live no-credential read at `rung=browser, degraded=True`; key path pinned offline at `rung=api, degraded=False`. The optionality is real: `config/products.yaml` documents `bestbuy_api_key` as "OPTIONAL, and genuinely optional", and `test_no_key_does_not_mean_no_best_buy` guards the regression |
| **REQ-05** — Pokémon Center and Nintendo each report stock or are documented unreachable with evidence | 02-04 | ✓ SATISFIED | Nintendo live at rung 1 with no adapter code (one `FIRST_PARTY` line, two watches). Pokémon Center REFUSED with the evidence detailed above |
| **REQ-06** — Every configured retailer has a control watch; a retailer without one is unhealthy | 02-03, 02-04 | ✓ SATISFIED | 4/4 controls live; three independent enforcement layers, each test-pinned; `healthy: True` published |

No orphaned requirements: REQUIREMENTS.md maps exactly REQ-04/05/06 to Phase 2, and all three are claimed by plans and satisfied.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `scripts/mutation_check.py` | 7, 10 | Docstring says "three specific things" / "The three mutations"; there are six | ℹ️ Info | Known and tracked as **IN-01**, deferred by the review, and confirmed by me to be genuinely still open rather than silently claimed fixed. Cosmetic — the harness itself runs and catches 6/6 |
| `scripts/control_check.py` | `--offline` help | Says "exit 0"; actually returns 3, and is now also stale w.r.t. the new exit 4 | ℹ️ Info | **IN-04**, deferred, and 02-REVIEW-FIX.md honestly notes WR-06 made it slightly *worse*. Help text only; the exit codes themselves are correct and pinned by `tests/test_verify_makefile.py` |
| `/tmp/uc_*` | — | 3 **empty** 4 KB profile directories dated after the CR-01 fix (21:48:06, 21:48:31, 22:02:48) survive in the host `/tmp` | ℹ️ Info | See below. Not the CR-01 leak, and not a blocker |

No `TBD`, `FIXME` or `XXX` markers in any file this phase touched. No stub returns, no placeholder text, no console-log-only handlers.

### On the residual empty profile directories

02-REVIEW-FIX.md reports "0 profile dirs" after the fix. That is true where it
matters and slightly overstated in general, and the distinction is worth recording
precisely:

- The **deployed service** sets `PrivateTmp=true`, so its profiles would land in
  `/tmp/systemd-private-*-boty.service-*/tmp/`. I found **zero** there after 18
  minutes and 4 browser cycles. The fix works on the unit.
- A **controlled single render** under the service `EnvironmentFile` created and
  removed its profile cleanly: `/tmp/uc_*` went 20 → 20.
- But three **empty, 0-entry, 4 KB** directories dated after the fix survive in the
  host `/tmp` from `systemd-run`-style invocations — most likely Chrome recreating
  the directory after `rmtree` on the way out.

Scale: the pre-fix leak was a zombie process plus ~17 MB per cycle (measured: 13
zombies, 204 MB at 71 minutes). What remains is an occasional empty inode. That is
a reduction of roughly four orders of magnitude and it leaks no process and no
bytes — Info, not a gap. The 52 MB of `uc_*` directories still sitting in `/tmp`
are all dated 18:47–19:45, i.e. pre-fix debris that nothing cleans up
retroactively; they are worth deleting by hand but they are not evidence of an
ongoing leak.

---

## Is the verification story trustworthy?

This is the question worth more than the checklist, because this phase produced a
false green and two Criticals that its own gates did not catch. Taking the three
escapes one at a time, by class:

**1. The false green (env asymmetry) — CLOSED, and I proved it both ways.**
`make verify` in a shell with `BOTY_BROWSER_PATH` exported passed while the service
could not find Chrome at all, and the monitor paged 30 minutes later. That can no
longer happen silently: the control check gained exit code **4 (INCOMPLETE)**, and I
ran the gate both ways in this verification. Service env → unqualified
`VERIFY: PASS`, 4/4 controls. Plain shell with the browser variables stripped →
`VERIFY: PASS (INCOMPLETE — some controls could not run on this host; the detectors
they cover are unverified here)`. The two greens no longer look the same, which is
exactly the property that was missing. The fix also correctly refused the easy
option (adding `browser` to the `dev` extra) because it contradicts a recorded
licensing decision and would not have worked anyway — a Chrome binary is not
something an extra can install.

**2. CR-02 (PII in a browser-captured fixture) — CLOSED by an executable gate.**
This is the strongest of the three, because the fix is a test rather than a
promise, and I confirmed the test is not vacuous: injecting a fake client IP and
geolocation into a shipped fixture made it go red naming all four markers. The
guard is also correctly *scoped* — to client-identity markers rather than any
IP-shaped string — which is what keeps it from crying wolf on version numbers and
getting disabled within a week. And the history purge is real: no client IP and no
EdgeScape geolocation appear anywhere across 622 objects. Note the class this
belongs to: **the risk arrived with the browser rung**, because CDNs echo the
client's identity into the DOM and rung 1 never returned a DOM. Every future
rung-3 capture carries it, and now every future rung-3 capture is scanned.

**3. CR-01 (runtime resource leak) — MITIGATED IN CODE, NOT COVERED BY ANY GATE.**
This is the honest weak point, and neither the SUMMARY nor the fix report hides it —
02-REVIEW-FIX.md says outright that process reaping "cannot be pinned by an
in-process test." The three new tests drive a *fake* nodriver, so what they pin is
that `_teardown` is **called** on each path, not that a real Chrome child is
reaped. `make verify` runs a one-shot process; zombie accumulation and profile
growth are properties of a daemon measured in hours. So a regression of exactly the
CR-01 shape would once again be invisible to the gate and discoverable only by
someone running `ps` against the deployed unit.

My independent measurements are good — 0 zombies, 0 private-tmp profiles, a clean
controlled render — but they were taken at 18 minutes, and the original leak needed
71 minutes to reach 13 zombies. That is why this is a human verification item
rather than a checked box.

**The pattern across all three is the same, and it echoes Phase 1's own W-01
warning:** a gate's proof does not automatically reach the layer where the bug
lives. Phase 1 flagged that the mutation set did not touch `monitor.py`; Phase 2
closed that (M4/M5/M6 now cover `models.py` and `monitor.py`, and all six were
caught in my run). Phase 2's equivalent gap is the daemon lifetime, and it is not
closed.

**What genuinely improved this phase, and it is substantial:** the gate suite grew
in direct response to each escape rather than being patched over — exit code 4 for
the env asymmetry, `tests/test_dashboard.py` pinning the *consuming* half of a
contract that had been asserted only at the producing end (which is precisely how
it stayed unimplemented), the PII guard, real Akamai bytes replacing a
self-referential reconstruction, and node-level SKU binding replacing a page-level
substring check that would not have closed its own scenario. The tests went 169 →
209, mypy stayed clean over 14 files, and every fix was watched failing first.

**Where I land:** the four retailer readings are trustworthy and I would act on
them. The *gate* is trustworthy for code regressions and for live retailer
breakage, and it is now honest about what it did not check — the three-flavour
verdict table in the README is a real improvement over a binary pass. It remains
blind to resource behaviour over time. A green `make verify` on this project is
necessary and not sufficient, and the project's own README now says so, which is
the right place for that sentence to live.

---

## Human Verification Required

Neither item is a failure. Both are things an exit code cannot settle.

### 1. Best Buy at rung 2 — the API path with a real key

**Test:** Put a real `BESTBUY_API_KEY` in `~/.config/boty/env`, then run `boty check`
through `systemd-run` with that `EnvironmentFile`.
**Expected:** The Best Buy control row loses its `[degraded]` tag; `status.json`
records `"rung": "api", "degraded": false`; same SKU, same `IN_STOCK`, same $59.99;
no browser launched.
**Why human:** The credential needs manual approval and a non-free email domain —
which is the documented reason (REQ-04) it is an optional enhancement rather than
the primary path. The dispatch, the rung tagging and the flag semantics are already
pinned offline; only the live API response shape is unproven. **If the key is
permanently unobtainable, accept this as an override rather than carrying it
forward as an open item into Phase 3.**

### 2. CR-01 durability over a daemon lifetime

**Test:** Leave `boty.service` running 6–12 hours, then count zombie children of the
main PID and `uc_*` directories inside the unit's private tmp. Take two readings
hours apart.
**Expected:** Zero of both, and **flat** between readings — not merely low.
**Why human:** Only elapsed time can prove this, and no gate covers it. My
measurement was 18 minutes against a leak that took 71 minutes to become obvious.

---

## Gaps Summary

**None.** All six amended success criteria are verified by execution, all three
requirements (REQ-04, REQ-05, REQ-06) are satisfied, both Criticals were
independently re-measured and hold, the gate was proved to bite and the tree is
clean afterwards.

The four-retailer outcome is honest rather than convenient: Pokémon Center's rung 4
rests on six recorded refusals across two transports plus a written Terms-of-Use
prohibition; the viable fifth candidate was probed, declined for a market reason I
independently re-confirmed, and the refusal is written into `config/products.yaml`
itself; and Best Buy's control-only status is stated in the README's own voice
above the install instructions.

Status is `human_needed` rather than `passed` for two items that no exit code can
close — a credential nobody here can obtain, and a resource-leak property that only
elapsed time can confirm. Phase 3 states its criteria in terms of this phase, so
both are recorded rather than rounded away.

---

_Verified: 2026-08-03T03:11:16Z_
_Verifier: Claude (gsd-verifier)_
_Method: execution — 14 commands run, 2 deliberate breaks confirmed to fail the gate, both Criticals independently re-measured, 1 live market claim re-probed, 1 dashboard screenshot read_

---

## Resolution of the two `human_needed` items (2026-08-02)

**1. Best Buy rung 2 — accepted as an override, on a decision already recorded.**
`QUESTIONS.md` downgraded the Best Buy API key to *"NO LONGER BLOCKING (optional
enhancement)"* before this phase ran, with the reason: signup requires manual
approval and rejects free email domains, so anyone cloning this repo hits the
same wall. Rung 3 is therefore the primary path by design, needs no credentials,
and is the one that was verified live.

What *is* pinned offline: dispatch selects the API path when `BESTBUY_API_KEY` is
set, all four `Result` constructions in `check_bestbuy_api` carry `rung=Rung.API`,
and `degraded` is False on that path. What cannot be checked here is a live API
response, and that will remain true for any contributor without an approved key.
Carrying it forward as an open item would mean carrying it forever. Accepted.

**2. CR-01 durability — measurement extended rather than argued.**
The fix was measured over 18 minutes against a leak that took 71 to become
obvious, which is a fair objection. A 16-sample watch over ~80 minutes was
started at verification time, sampling zombie and child counts every 5 minutes.
Result is recorded below rather than assumed.

The verifier's structural point stands and is not resolved by more sampling: the
three teardown tests drive a *fake* nodriver, so they prove `_teardown` is
called, not that a real child is reaped. `make verify` is a one-shot process and
cannot measure a daemon-lifetime property. This is Phase 1's W-01 pattern
recurring — a gate whose proof does not reach the layer where the bug lives —
and it is open, not closed. It is recorded here so Phase 3 inherits the warning
rather than the illusion.
