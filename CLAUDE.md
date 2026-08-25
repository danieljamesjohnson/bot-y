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
  count. It is currently unset, deliberately — see `QUESTIONS.md` § 0f.
- `.env*` reads are blocked by policy. Get env var *names* from docs, never values.
- `datastore/secret.txt` belongs to a vendored changedetection.io datastore. Leave it be.

---

## Registries and invariants

**`scripts/mutation_check.py`** deliberately breaks source in a sandbox and asserts the
suite notices. Currently **M1–M20 and M25–M41**.

> **M21–M24 are an intentional, documented gap. Never fill them.** Phase 6 recorded why:
> `apply_mutation` cannot add a file, so the defect it would have covered is outside the
> harness by construction. The script says so in seven places (`grep -c "INTENTIONAL GAP"`)
> — six until M41 added the seventh on 2026-08-25, which restates the rule rather than
> weakening it: `.github/` was *already* in `SANDBOX_CONTENTS`, so M41 needed nothing added
> to reach it. That is the test M21–M24 failed.

Next free ident is **M42**. Register one only when it defends something new — if every
break is already caught by a second independent test, an ident raises the denominator
without defending anything, and the registry records that reasoning too.

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

- **A restart is the user's call, not yours.** Ask; don't assume, and don't run it as a
  side effect of something else.
- **Do not run `boty check` casually** — it makes live retailer requests *and* writes the
  live `served/boty/status.json` the daemon owns.
- **Never write to `state.json`, `pacer-state.json` or `served/boty/status.json`.** The
  running daemon owns them. Copy them to a scratch dir if you need to exercise something.
- Before a restart, copy those three files. The state document migrates shape on load.
- The unit needs `BOTY_BROWSER_PATH` for rung-3 retailers. A developer shell can find a
  browser on PATH where systemd cannot — and the reverse also happens, so `make verify`
  reporting "no Chrome/Chromium binary found" may be *your shell*, not the service.

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
