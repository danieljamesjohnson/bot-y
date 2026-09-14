# Runbook — kicking off a long autonomous run on bot-y

Written 2026-09-14, from the run that did phases 8, 9 and 10. Everything here is a
thing that actually happened, not a precaution someone imagined.

---

## 1. Before you start (2 minutes)

```bash
cd ~/CodeProjects/pokemongoplusplus
git status --porcelain          # must be empty
git log --oneline -1
export NVM_DIR=$HOME/.nvm; . $NVM_DIR/nvm.sh
make verify-offline             # must exit 0. TAKES ~11 MINUTES now.
```

**If `make verify-offline` is red, do not start an autonomous run.** It cannot tell
its own breakage from yours, and it will spend a phase arguing with the mess.

Check what the tooling thinks is unfinished — this is what the run will pick up, and
it is not always what you expect:

```bash
gsd-tools query init.manager | python3 -c "import json,sys; [print(p['number'], p['phase_complete'], p['verification_status']) for p in json.load(sys.stdin)['phases']]"
```

A phase with `verification_status: missing` will be **re-entered**, not skipped —
even if its ROADMAP box is ticked. That is how phases 9 and 10 got verified late.

---

## 2. The command

```
/gsd-autonomous
```

Useful flags, and when they earn their keep:

| flag | use it when |
|---|---|
| `--to N` | you want it to stop before a phase that spends something (money, requests, a deploy) |
| `--from N` | resuming after a stop |
| `--only N` | one phase, no milestone lifecycle at the end |

**`--to N` is the important one here.** Without it, a run that finishes the last
phase goes straight into the milestone lifecycle: audit → **complete-milestone
(archives the milestone)** → cleanup. That is a lot of irreversible tidying to
discover by surprise.

---

## 3. Say these things in the kickoff message

The workflow will not ask permission for most of them, so pre-authorising or
pre-forbidding is what keeps a long run unattended.

**Always paste this:**

> Follow `CLAUDE.md` exactly — it is binding. In particular:
> - **Never run a `gsd-tools` state or phase WRITE** (`state.advance-plan`,
>   `state.begin-phase`, `phase.complete`). Fourteen recorded corruptions of this
>   repo's `STATE.md`, one of which invented content. Hand-edit `STATE.md` after a
>   `cp`, and `diff` afterwards. **The autonomous workflow's own `update_roadmap`
>   step calls `phase.complete` — you must not follow it there.**
> - **No live retailer request, no `boty check`, no `systemctl restart boty`, and no
>   write to `state.json` / `pacer-state.json` / `served/boty/status.json`** unless I
>   have authorised it in this message.
> - Watch every gate go red before trusting it, and record the actual counts. Never
>   round a verdict up — MET IN PART is a normal outcome.
> - Record superseded measurements **beside**, never edit them away.

**Add a live-request budget only if the phase needs one:**

> You may make at most **N** live requests, to **<retailer>** only, spaced ≥300 s.
> Any navigation that leaves this host is spent whatever it returns; only a
> pre-navigation failure is exempt, once. A refusal IS the measurement — record it,
> do not retry around it. State the worst-case count in the plan so I can check it by
> counting.

**And if you want the run to actually finish phases:**

> Run the verifier on every phase before closing it. A phase closed on the
> orchestrator's own assessment is not verified, and `verification_status: missing`
> will make the next run re-enter it.

---

## 4. What will stop and ask

Genuine pauses, worth answering:

- **Grey-area design decisions** during discuss (unless `workflow.skip_discuss=true`,
  which it currently is — so the ROADMAP goal is taken as the spec).
- **`human_needed` verification** — usually a deploy observation.
- **`gaps_found`** — it offers gap-closure, continue, or stop.
- **Cleanup** — asks before deleting.

It will **not** reliably stop for: making live requests, spending a probe budget, or
calling the banned `gsd-tools` writes. Those are yours to fence in section 3.

---

## 5. Checking on it

```bash
git log --oneline -15                    # commits are the real progress bar
ls .planning/phases/*/                   # SUMMARY.md per plan = a wave landed
tail -40 .planning/STATE.md              # hand-written, so it is current
journalctl -u boty --since "1 hour ago" | tail   # the daemon is unaffected by a run
```

A wave takes roughly 20–60 minutes. Long silences are normal — subagents produce no
output until they return. `make verify-offline` alone is ~11 minutes and runs at
least once per plan.

---

## 6. Stopping and recovering

Interrupt at any time. The tree is safe if the working tree is clean; each plan
commits atomically, so a stop between plans loses nothing.

```bash
git status --porcelain     # if not empty, a plan was mid-flight
git log --oneline -5
```

Resume with `/gsd-autonomous --from N`. If `STATE.md` looks wrong, check whether a
banned `gsd-tools` write ran — that is the single most likely cause, and
`git diff .planning/STATE.md` will show it.

---

## 7. The traps that actually cost time on the last run

1. **A gate timed by the host.** A test passed here and failed in CI because a real
   wall-clock term reached a simulated schedule. If a test drives a simulated span,
   inject the clock — `watch_loop` now takes `monotonic=` for exactly this.
2. **A stale `.pyc` keeping a reverted perturbation alive.** `diff` says the file is
   clean and the interpreter still runs the old bytecode. Between a perturbation and
   its revert: `find . -path ./.venv -prune -o -name __pycache__ -type d -print0 | xargs -0 rm -rf`
3. **Deleting code as unreachable on the strength of the newest capture.** An older
   *measured* capture showed the shape that code handled. Both were real.
4. **A gate that goes false without going red.** Tests that enumerate "all four arms"
   by name keep passing when you add a fifth. Green is the symptom, not the evidence.
5. **`.planning/` paths in a mutation-registry citation** fail the sandbox baseline —
   `SANDBOX_CONTENTS` excludes `.planning/`.
6. **The identity checker fires on your own prose**, including a test's failure
   message. Fix the prose, not the gate.

---

## 8. Two standing facts about this project

- **"Complete in the tree" is not "on the wire."** `boty` is an editable install, so
  a phase reaches the daemon only at `sudo systemctl restart boty` — **your action,
  never the agent's.** Before any restart, copy `state.json`, `pacer-state.json` and
  `served/boty/status.json`; the state document migrates shape on load.
- **A restart can execute code that has never run.** The 2026-09-11 restart activated
  the Walmart store pin, which made a store-disagreement warning reachable for the
  first time — and it had a defect that broke every health notification. Watch
  `journalctl -u boty` for the first hour after a restart, not just the first minute.
