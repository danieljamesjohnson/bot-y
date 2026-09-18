# bot-y — working notes for agents

A restock monitor for the Pokémon GO Plus +. Six retailers, ~13 watches, a systemd
daemon on danserver, a dashboard on the tailnet.

**The core value, and the thing every rule below serves:** never say *"out of stock"*
when the truth is *"I couldn't tell"*, and never say *"in stock"* when the truth is
*"a reseller has one at 4× MSRP"*. A monitor that lies confidently is worse than no
monitor, because you stop checking yourself.

---

## The evidence standard

This repository is stricter than most, in one specific way: **a claim must be tied to
a measurement, and anything unmeasured must say so.** That applies to code, comments,
commit messages, docs and your own summaries. It is enforced by gates, not by manners.

Concretely, the rules that will trip you if you ignore them:

- **Watch every gate go red before you trust it.** Adding a test means running it
  against the *unfixed* code first, recording the actual failure count, then fixing and
  recording the pass. A test that has never failed is not a gate. If you can't make it
  fail, say so — that is a finding, not a formality.
- **Never round a claim up.** "MET IN PART" and "not measured" are normal, shippable
  outcomes here. Rewording a criterion so it passes is the one unforgivable move.
- **Superseded measurements are recorded *beside*, never edited away.** If a number was
  true when written and isn't now, add a dated note next to it; don't overwrite it. The
  convention is stated in `docs/retailer-evidence.md` § 6, with worked precedents.
- **If a gate goes red on your own prose, fix the prose, not the gate.** This happens
  more than you'd think — several gates count literal strings and can't tell code from
  a comment quoting it. There are at least four precedents in the history.
- **Don't page unless it's actionable.** A failure the user can't act on gets recorded
  (`QUESTIONS.md`, `STATE.md`, the summary), not pushed. `notify-dan` goes to a phone.

---

## Commands

```bash
make verify-offline   # THE gate. Must exit 0. identity + lint + tests + types + fixtures + mutation
make verify           # the above plus LIVE retailer control checks (network, slow, rate-limited)
make test             # tests only
make hooks            # install the tracked pre-commit hook into .git/hooks
```

`make verify` has three distinct passes and they are not interchangeable:
`PASS`, `PASS (OFFLINE — live controls were NOT run)`, and
`PASS (INCOMPLETE — some controls could not run on this host)`. The last one means a
detector is *unverified here*, not broken. Read the verdict line, not the exit code alone.

**Python is the venv, not the system.** Bare `python` on this box has no pytest.

```bash
.venv/bin/python -m pytest tests/test_status.py -q
```

**Node is nvm-only, and `make` does not inherit it.** In a non-login shell:

```bash
export NVM_DIR=$HOME/.nvm; . $NVM_DIR/nvm.sh
```

This is not trivia — `tests/test_dashboard.py` needs a JS runtime to parse-check
`served/boty/index.html`, and it silently **skipped** inside `make verify-offline` for a
while because of exactly this. `_js_runtime()` now globs the nvm root itself. If you add
another JS-executing gate, make sure it *binds* rather than skips, and prove it.

---

## Traps that have actually bitten

### `gsd-tools` state/phase WRITES corrupt `.planning/STATE.md`

**Do not invoke them. Edit `STATE.md` by hand with Edit.**

Fourteen recorded corruptions across three subcommands (`state.advance-plan`,
`state.begin-phase`, `phase.complete`), all on gsd-core **1.4.5**.

Root cause, reproduced: `state-document.cjs` edits by **regex over the whole file**,
keyed on field name, with no scoping to the frontmatter block — and it tries the
`**Bold:**` form *first*. This `STATE.md` retains historical body sections from earlier
milestones containing `**Phase:**` and `**Stopped At:**` lines, so the writer finds
*those* and overwrites them.

Symptoms on 1.4.5: YAML frontmatter comment blocks deleted wholesale; `stopped_at`
regressed to a stale value four separate times; `phase.complete` rewriting the v1.0
status line into the incoherent `**Phase:** 07 of 5 (Open Source Ready)` /
`**Plan:** Not started`. It also returned false data — `{"advanced": false, "reason":
"last_plan", "current_plan": 6}` for a phase on plan 3 *and* plan 4 of 6, and
`roadmap_updated: true` while changing nothing.

**Status on 1.11.0 (installed 2026-08-21), measured against a copy of this STATE.md:**

| Symptom | 1.11.0 |
|---|---|
| Frontmatter comments deleted | **FIXED** upstream (#3257, `propagateCommentChannel`) — 79 comment lines in, 79 out |
| `**Bold:**`-first clobbering | **STILL PRESENT** — same repro, byte-identical output on both versions |
| Cosmetic reflow | **NEW** — inserts a blank line after every frontmatter comment (+93 lines here). One-time and idempotent; stable across runs 2–4 |

So the *recoverable* symptom is fixed and the *data-losing* one is not. **The ban stands.**
Note also that `state.advance-plan` rewrote the file even on the run where it returned
`{"error": "Cannot parse Current Plan or Total Plans in Phase from STATE.md"}` — an error
return is not evidence that nothing was written.

If you ever must run one anyway: `cp .planning/STATE.md /tmp/x` first, `diff` after, and
restore-and-hand-apply if it misfired. That protocol caught all fourteen.

**Read-only `gsd-tools query` verbs are fine and have been reliable** —
`roadmap.analyze`, `init.*`, `config-get`, `roadmap.update-plan-progress`, `commit`.

Never edit the `milestone:` key: `tests/test_packaging_metadata.py` binds it to
`pyproject.toml`'s version component-wise.

### The identity checker guards a public repo

`scripts/identity_check.py` scans **every tracked file** for this machine's identity —
IPs, postal codes, store numbers, session tokens. It runs in `make verify` *and* as a
tracked pre-commit hook (`make hooks`), because the same rule lived only in the test
suite once and leaked seven times anyway.

- **Redact the value, never the key** — the key has to stay real or the rule stops
  matching a real page.
- **Never add a value to the allow-list**, and **never name a removed value in a commit
  message or a redaction note** — a record that names what it removed is a copy of it.
  That has happened here three times.
- **Never `--no-verify`.**
- `.planning/phases/` and `.planning/milestones/v*-phases/` are *probe-dir exemptions*:
  planning documents legitimately quote the patterns, so they get an exact-match check
  against previously-scrubbed values instead of the shape rules. The exemption swaps
  which check runs; it does not disable checking. Its size is pinned by
  `tests/test_identity_check.py` so it cannot quietly grow.

Git history was rewritten once (`filter-repo`, force-push, 170 commits) because of a
leak in `.planning/`, not in fixtures. That is why this is loud.

### A stale `.pyc` can keep a reverted red-watch perturbation LIVE

**Found 2026-09-01 by 09-01, handed forward through `09-DECISIONS.md`, and recorded here by
09-05 because every red-watch in this repository walks into it.** The protocol above —
perturb, run, observe the red, revert, `diff` to confirm — **has a hole, and the hole is
`diff`.**

A perturbation that changes a source file's **length not at all** (`900` → `600`, `<=` → `>=`,
`True` → `Fals`) and is reverted **within the same wall-clock second** leaves CPython's and
pytest's caches valid: both validate a `.pyc` against the source's **mtime at one-second
resolution and its size**, and both matched. The reverted source is never recompiled and the
interpreter keeps executing the perturbed bytecode.

Every symptom points away from the cause: `diff` says identical, `git status` is empty, `grep`
finds the right value in the working tree *and* in `HEAD` — and the suite fails citing a value
that is **in no file on disk**. Bisecting by test file names every file as the trigger, which
is a session-level cause wearing a test-interaction costume. Measured on the day: the cached
`.pyc` was written 186 ms before the source it was supposedly built from.

**Clear the caches between a perturbation and its revert. Every time:**

```bash
find . -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} + ; rm -rf .pytest_cache
```

**The failure mode is the worst available** — the gate goes red for a reason not in any file,
and the natural response is to distrust the new test.

**And do NOT revert a perturbation with `git checkout <file>` while the surrounding work is
uncommitted.** Found 2026-09-02 by 10-02, which lost a finished `assess_health` arm that way.
`git checkout` restores `HEAD`; it cannot tell your three-character perturbation from the two hundred
lines you wrote before it, so it discards both. The tell is subtle in exactly the wrong direction:
the *next* perturbation's run still reports failures — because the real work is gone, not because
the perturbation landed — so the output looks like a successful red watch. `git status` showing the
file **unmodified** is what gives it away.

**Commit the work first, or revert from a copy:** `cp boty/x.py /tmp/x.keep` before the first
perturbation, `cp /tmp/x.keep boty/x.py` to revert, and `diff` the two afterwards to prove the
restore was byte-identical. Counts taken against a tree in this state are measuring something else
and have to be re-taken — say so beside them rather than keeping the first number.

### The dashboard has two non-obvious gates

`served/boty/index.html` is a real page served over the tailnet.

- **No HTML comments inside the `<script>` block.** A backtick inside one closed a
  template literal and stopped the whole page parsing while every regex gate stayed
  green. There is a gate for this now, and a mutation.
- **`esc()` on every `UNTRUSTED` field.** A reproduced XSS sink shipped here: an
  unescaped `w.availability` in a `class="dot ${...}"` attribute, reachable because the
  monitor deliberately returns any string from `state.json`.
- Run `node --check` on the extracted script before committing.

### Secrets and the store pin

- `WALMART_STORE_ID` lives in `/home/dan/.config/boty/env` (mode 600, outside the repo).
  **Never read, derive, infer or print it.** Its presence may only ever be measured as a
  count. **It is SET ON DISK AND IN EFFECT** — Dan supplied it on 2026-08-25 after two deferrals,
  and the restart that activated it happened **2026-08-27 07:23:34**. *(This bullet said
  **2026-09-11 07:56:33** for a few hours on 2026-09-14, which was wrong by fifteen days and was the
  date five separate records in this project had settled on without checking. The pin is dated by
  the first store-DISAGREEMENT warning, because that warning is unreachable until a store is pinned:
  the first one is 2026-08-27 20:07:53, 12 h 44 m after that restart, on Walmart's 6-hour backoff.
  Caught by phase 11's verifier.)* Any process that does not
  load that env file — a test, a dev shell — still sees no pin, so a Walmart reading there is
  store-gapped for a reason that is not a config defect. *(This bullet read "it is currently unset,
  deliberately" until 2026-09-02, and "SET ON DISK and NOT YET IN EFFECT … the next restart, which
  is still deferred" until 2026-09-14. Each was true when written; each is corrected rather than
  deleted, because § 0f records what changed it and a guide that quietly agrees with itself teaches
  nothing.)*
  - **IN EFFECT IS NOT THE SAME AS PRODUCING A READING, and the difference bit this project's own
    records.** Measured 2026-09-14: all three Walmart rows in `state.json` carry `read_at: null` and
    `checked: false`, so **no resolved Walmart reading has ever been recorded** — a stamp is written
    only for a non-`UNKNOWN` verdict (`boty/monitor.py:417-418`, `:441`) and a refusal never writes
    one. `STATE.md` and `08-UAT.md` both claimed on 2026-09-11 that Walmart's rows "carry real
    verdicts after the restart"; those values are the migrated ledger's **memory**, read off the
    dashboard and taken for fresh. Both are corrected beside. **`read_at` is the field that tells
    them apart — use it.**
  - **What the pin DID do, measured, is make the store-disagreement warning reachable for the first
    time — and it has been silently failing ever since.** **4,305** warnings between **2026-08-27
    20:07:54** and 2026-09-13 05:26:07, **sixteen days**, every one rejected by Telegram at byte
    offset 353, **not one reaching a phone**. `17d3e5d` fixes it and that fix is **in the tree and
    not on the wire**. *(A first draft of this bullet said "546 times … from 2026-09-11" — a count
    taken inside a `journalctl --since` window and then published as a total. **`--since` is an
    assumption wearing a measurement's clothes**; if you bound a query, say so beside the number.)*
    See `QUESTIONS.md` § 0f.
- `.env*` reads are blocked by policy. Get env var *names* from docs, never values.
- `datastore/secret.txt` belongs to a vendored changedetection.io datastore. Leave it be.

---

## Registries and invariants

**`scripts/mutation_check.py`** deliberately breaks source in a sandbox and asserts the
suite notices. Currently **M1–M20 and M25–M44** — 40 idents, all 40 caught, survivors 0.

> **M21–M24 are an intentional, documented gap. Never fill them.** Phase 6 recorded why:
> `apply_mutation` cannot add a file, so the defect it would have covered is outside the
> harness by construction. The script says so in ten places (`grep -c "INTENTIONAL GAP"`)
> — seven until M42 added the eighth on 2026-08-28, eight until M43 added the ninth on
> 2026-09-01, and nine until M44 added the tenth on 2026-09-02. Each restates the rule rather
> than weakening it: `.github/` was *already* in `SANDBOX_CONTENTS` for M41, `boty/pacing.py`
> already was for M43, and `boty/monitor.py` already was for M44 — which already carried four
> idents — so none of them needed anything added to reach its target. That is the test
> M21–M24 failed.

Next free ident is **M45**. Register one only when it defends something new — if every
break is already caught by a second independent test, an ident raises the denominator
without defending anything, and the registry records that reasoning too.

**M44 defends the sentence a dead control gets.** It empties the one assignment that decides
whether a control whose target no longer resolves reaches its own health arm; under it the
monitor goes back to calling that a probably-broken detector and stops naming the one repair
a person could make, while `Result.unresolved`, `DEAD_CONTROL_ACTION` and every comment around
the arm still read as though the state exists. Ten of its eleven killers are reached by no
other ident. Its block also records the anchor it did **not** take — the resolution predicate
at the producer, four killers, three of them reached by nothing — as an **open hole rather
than a refusal**, so an `M45` there would defend something new.

**M42 is kept on LOCALISATION alone, and its own comment block says so.** Its kill set is a
proper subset of M33's, so it closes no hole in the suite — 08-04 recorded that as a measured
finding rather than rounding it up into coverage it does not provide. Re-measured 2026-09-02 by
10-05: the relation still holds and the counts have grown with the suite — 18 killers inside
M33's 32, where 08-04 measured 16 inside 28. Both figures are kept; the newer one does not
replace the older. If a future reader judges
that insufficient, the honest remedy is to delete the ident, not to reword it.

**M43 is the other answer to the same question, and it is why the measurement is worth taking
rather than assuming.** Registered by 09-05 on the de-lockstep's birth phase, its five killers
are **disjoint from the union of all 38 idents that preceded it** — re-measured one sandbox
each on 2026-09-01, largest overlap with any existing ident: zero tests.
**AND IT KILLS SIX AS OF 2026-09-14**, re-measured at `570df66` by a phase-9 verifier: `e88a350`
rewrote `test_each_retailer_is_asked_the_same_number_of_times_a_day_as_before` (the day cut moved
from 1728 wakes to 86 400 seconds) and under M43 the OLD version passed while the new one fails.
**Repairing a seed-pinned gate grew a mutation's kill set** — the pleasant direction, and the one
nobody thinks to re-measure. The disjointness claim above is about **the original five**; whether
the sixth overlaps any other ident is **not measured**, and is not pretended to be. So M43 buys
**detection**, not localisation: before it, criterion 1's separation, criterion 3's window
maximum, the restart-phase test and the idle-wake test were gated by tests and ungated by this
harness. Its block also records the anchor it did **not** take — the grid advance, 11 killers,
six of them already under M33 — as measured evidence rather than a discarded draft, and says
why a second ident for it was refused.

*(These counts drift whenever nothing moves them, and nothing in the suite gates them. They were
stale for three days once — M42 landed 2026-08-28 and this section still read M25–M41 / seven /
"next free is M42" until 2026-08-31, when the phase-8 code review caught it as WR-04, and "next
free ident is M42" would have handed the next agent a collision. They were correct as
M25–M42 / eight / M43 up to 2026-09-01; 09-05 ADVANCED them in the same commit that registered
M43, and 10-05 did the same for M44 on 2026-09-02 — one commit, `test(10-05)`, carrying both the
ident and the counts that describe it. That is the only discipline available here.)*

A mutation must anchor on **behaviour**, not on message text or a prose comment.

**Retailers** follow an escalation ladder — stop at the first rung that works:
TLS impersonation (`curl_cffi`) → official API *only if a fresh clone can get the
credential* → headless browser, marked `DEGRADED` → drop, with written evidence. `Rung`
and `Extraction` (`structured` | `dom`) are independent axes; a `dom` reader is degraded
even at rung 1, because a reskin breaks it silently. The support matrix in `README.md`
is gated against the code — it cannot drift.

---

## Deployment

`boty` is an **editable install**: the systemd unit runs this working tree's venv from
this working tree. So a code change is deployed by:

```bash
sudo systemctl restart boty          # the watcher daemon
```

`boty-web.service` separately serves `served/boty/` on `127.0.0.1:8821` (loopback), so
page edits are live on next load without a restart.

> ### RESOLVED 2026-09-15 ON DAN'S INSTRUCTION — and the page is still loopback-only
>
> He said *"kill the pos-facelift server and restart boty-web"*. Done: PID 1177060 stopped (identity
> re-confirmed immediately beforehand, so not a recycled PID), `boty-web` `active (running)`,
> `Result=success`, `NRestarts` reset **110102 → 0**, serving the real page, zero console errors.
>
> **`boty-web` binds `127.0.0.1` and NOTHING PROXIES IT** — measured: no `caddy`/`nginx` rule for
> `8821`, and `tailscale serve` fronts five other loopback services and not this one. So
> `http://danserver:8821` is reachable **from this host only**, and the thirteen-day outage made it
> *look* reachable off-host because the squatter bound `0.0.0.0`. **The dashboard has never been
> reachable from a phone.** Exposing it is a one-line `tailscale serve` in the house style and is
> Dan's call — `QUESTIONS.md` § 0i.
>
> **The block below is the measurement that found it, kept unedited.**
>
> ### THE DASHBOARD WAS DOWN FROM 2026-09-02 TO 2026-09-15, AND `:8821` SERVED ANOTHER PROJECT
>
> **Measured 2026-09-15.** `boty-web.service` is in a crash-loop: `ActiveState=activating`,
> `Result=exit-code`, **`NRestarts=110102`**, dying every ~10 s on
> `OSError: [Errno 98] Address already in use`.
>
> **The port was taken by a different project and the timing is exact.** PID 1177060, started
> **2026-09-02 06:34:58**, cwd `/home/dan/CodeProjects/pos-facelift`, running
> `python3 -m http.server 8821 --bind 0.0.0.0 --directory served/tickets`. `boty-web` logged its
> first `Address already in use` at **06:35:08** — **ten seconds later** — and has not served a page
> since.
>
> **So anyone opening `http://danserver:8821` for the last two weeks got pos-facelift's kitchen
> tickets, not the restock monitor**, and the squatter binds `0.0.0.0` where this unit binds
> loopback, so it is reachable across the tailnet where the real dashboard never was.
>
> **THIS IS NOT AN AGENT'S TO FIX.** Two projects want one port and choosing between them is Dan's:
> stop the other server, re-point one of the two units, or give bot-y a different port. **Do not
> kill another project's process to free a port.** Recorded in `QUESTIONS.md`.
>
> **To look at the dashboard meanwhile**, serve it yourself on a free port and point the
> `go-look-at` skill at loopback — that is how `08-UAT.md` item 2 was finally discharged on
> 2026-09-15:
>
> ```bash
> .venv/bin/python -m http.server 8831 --bind 127.0.0.1 --directory served/boty
> ```
>
> **And note what this cost in evidence, not just in convenience.** Every record in this project has
> described "a dashboard on the tailnet" throughout, including the sentence directly above this
> block. **Nothing measured it**, because nothing gates a systemd unit's health — the same class of
> gap as a monitor that reports green about a question nobody asked, arriving one layer below the
> monitor.

- **A restart is the user's call, not yours.** Ask; don't assume, and don't run it as a
  side effect of something else.
- **AND A RESTART COSTS ONE LIVE REQUEST PER BACKED-OFF RETAILER, IMMEDIATELY.** Measured
  2026-09-18 across both of this project's restarts: `Pacer.load` deliberately does not restore
  `due_at` (*"it was measured against a clock that no longer exists"*), so every retailer mid-backoff
  or mid-cool-off is due within seconds of start-up. 2026-09-11 probed amazon at **+4 s** and target
  at +3 m 11 s; 2026-09-15 probed amazon at **+3 s**, walmart and target at +3 m 52 s. **Target was
  1 day 18 h into a three-day cool-off**, and the resulting refusal restarted that clock — so the
  restart both broke the politeness window and lengthened the blackout by ~1.2 days. Five
  unnecessary requests across two restarts, all to retailers already refusing us. **Factor it into
  the ask**, and do not restart repeatedly to test something. Full working and why it is not being
  hotfixed: `docs/retailer-evidence.md` § *A restart re-probes every backed-off retailer*.
- **Do not run `boty check` casually** — it makes live retailer requests *and* writes the
  live `served/boty/status.json` the daemon owns.
- **Never write to `state.json`, `pacer-state.json` or `served/boty/status.json`.** The
  running daemon owns them. Copy them to a scratch dir if you need to exercise something.
- Before a restart, copy those three files. The state document migrates shape on load.
- The unit needs `BOTY_BROWSER_PATH` for rung-3 retailers. A developer shell can find a
  browser on PATH where systemd cannot — and the reverse also happens, so `make verify`
  reporting "no Chrome/Chromium binary found" may be *your shell*, not the service.

### `RuntimeError: Event loop is closed` in the journal is NOISE, and it says so in its own first line

**Observed once, 2026-09-15 17:53:50, twelve seconds after a rung-3 browser start.** An agent
tailing `journalctl -u boty` sees the word `Traceback` and a `RuntimeError` and reaches for the
wrong conclusion. It is the headless browser's asyncio subprocess transport being finalised after
its event loop closed — `BaseSubprocessTransport.__del__` → `write_eof` → `call_soon` →
`_check_closed`.

**It cannot propagate**, and its own first line says so: `Exception ignored in: <function
BaseSubprocessTransport.__del__ …>` — the interpreter's unraisable hook, printed and discarded.

**Measured after it rather than assumed:** the daemon stayed `active (running)`, same `MainPID`,
`NRestarts=0`, and `status.json` was rewritten **45 s later** on the ~50 s tick, `healthy: true`,
2 of 13 watches checked. Nothing was lost.

**TWO COUNTING TRAPS THIS ONE INCIDENT SET, AND BOTH CAUGHT ME INSIDE TEN MINUTES:**

- **`grep -c "Event loop is closed"` returns 2 for ONE traceback.** The
  `raise RuntimeError('Event loop is closed')` source line and the final `RuntimeError: …` line
  both match. I reported "2 occurrences" off that count; it is one. **Count timestamps, not lines.**
- **A gap between `status.json` writes is not a wedged loop.** `watch_loop` sleeps the tick *after*
  the cycle, so a slow browser fetch pushes the next write past the 42.5–57.5 s jitter band. I
  flagged 60 s of silence as marginal; the next write came at 45 s and was entirely normal.
  **Wait for one more write before concluding anything.**

**First occurrence in a journal reaching back to 2026-08-02** (29,051 lines), so *new* is a real
observation rather than a retention artifact — **and why it is new is NOT established.** Nothing in
this project's code appears in that stack, and one sample does not support an explanation.
Recorded as unexplained rather than diagnosed.

---

## Git and records

- **This project is TAGGED as of v0.3.0 (2026-08-25) and is still NOT published.** The two
  halves used to be one rule and they are now separate, so read them separately.
  - **Tagging is allowed and has happened.** Dan reversed the no-tag decision on
    2026-08-25: *"shipping is fine. correct it so that it can ship. just not a 1.0
    release."* `v0.3.0` is an annotated tag on GitHub with a release beside it. The rule
    this bullet used to carry — *"never been tagged or published, deliberately; do not
    create a tag"* — was true from the project's start until that date and is recorded
    here rather than deleted, because his reversal is the reason it changed and a guide
    that quietly agrees with itself teaches nothing.
  - **Publishing to PyPI is still not done, and that is still deliberate.** His words the
    same day: *"forget the pypi part, just get it to github."* `pip install bot-y`
    resolves nothing and `pypi.org/pypi/bot-y/json` is 404. The reason from 2026-08-06
    stands unchanged — *"I wouldn't publish it without more real testing"*.
  - **A `v*` tag no longer uploads anything**, and you should know why before you tag
    again. It used to: the only trigger on `.github/workflows/release.yml` is a `v*` tag
    push and that starts the job holding `id-token: write`. The publish job is now gated
    on `if: vars.PUBLISH_TO_PYPI == 'true'` (M41), the build job deliberately is not, so
    a tag builds and stops. To publish, configure the trusted publisher on pypi.org and
    set that repository variable — no code change. **Do not remove the gate to "make the
    release work".**
  - **Nothing above licenses a 1.0.** v1.0.0's definition of done still includes "Dan has
    successfully bought a GO Plus +" — a market condition — so the audit's recommendation
    against calling it shipped is untouched, and his instruction was explicitly *"just
    not a 1.0 release."* The version ships from the `0.x` line; `Development Status ::
    4 - Beta` stays.
- **"Archived" is not "shipped", and now "tagged" is not "published" either.** Milestone
  records distinguish complete-in-the-tree from running-on-the-daemon, and that
  distinction is usually the most important line in them. v0.3 is all three of complete,
  running (since 2026-08-20) and tagged, and is still not published — say which you mean.
- Commits are atomic and conventional (`feat(07-03):`, `fix(identity):`, `docs(v0.3):`).
- Commits use the repo's configured no-reply identity. An author email has silently gone
  wrong here once — check `git config user.email` before a push rather than after.
- Push freely when asked; don't push unasked.
- **Planning artifacts live in `.planning/`** (with the dot). Completed milestones archive
  to `.planning/milestones/`, including their phase directories.
- `QUESTIONS.md` holds decisions only the user can make. Answers are recorded **verbatim
  and dated**, beside the original question, not in place of it.

---

## Layout

| Path | What |
|---|---|
| `boty/` | the package — `retailers.py` (adapters), `models.py` (`Result`, alertability), `monitor.py` (the ledger + alerting), `pacing.py` (cadence + backoff), `status.py` (the published payload), `cli.py` |
| `scripts/` | `identity_check.py`, `mutation_check.py`, `control_check.py`, `evidence_check.py`, `release_check.py` |
| `served/boty/index.html` | the dashboard |
| `config/products.yaml` | the watches — tracked and public, so no real store numbers |
| `docs/retailer-evidence.md` | the evidence record. Gated by `tests/test_evidence_check.py` — a verdict must cite a measurement |
| `.planning/` | GSD planning. `STATE.md` is hand-edited (see above) |

---

## When this file is wrong

Fix it as part of your work. A stale `CLAUDE.md` misleads every future agent, and
several rules above exist only because someone learned them the expensive way.
