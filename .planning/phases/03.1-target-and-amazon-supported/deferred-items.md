# Deferred items — 03.1

Out-of-scope discoveries. Logged rather than fixed, per the executor scope boundary.

## From 03.1-02 (Target), 2026-08-03

**1. Zombie chromium processes held by Mission Control's `server.py`, not boty.**
The plan's live-state check asked for orphaned Chrome/chromium processes belonging
to `dan` after a full cycle. Five `[chromium] <defunct>` were found — all five
parented to PID 3741873, `python3 ./server.py`, which is Mission Control's
(probably the `go-look-at` headless screenshot path). **None is parented to
`boty.service`** (MainPID 446442 has no children at all), so boty's `_teardown`
is reaping correctly across both browser-rung retailers. Different project,
different repo; not touched.

**2. 23 stale `/tmp/uc_*` nodriver profile directories, 52 MB.**
Newest is 2026-08-03 00:53, i.e. all of them predate this plan. `boty.service`
runs `PrivateTmp=yes`, so these are not the daemon's — they are left over from
earlier agent-shell / manual browser runs outside the unit. Every render this
plan performed cleaned up after itself (none dated 07:5x–08:12 survives). Safe to
delete by hand; not deleted here because removing files this plan did not create
is exactly the blast radius the scope boundary is about.

**3. `docs/retailer-evidence.md` § Target is now very long and has three
conclusions layered on it.** Everything is accurate and each supersession is
marked and dated, but a reader arriving cold has to scroll past two reversed
verdicts to reach the current one. A future editorial pass could split the
historical record into an appendix. Deliberately not done here: rewriting the
history while landing the third verdict is how a record quietly loses the
evidence its own conclusion was revised through.
