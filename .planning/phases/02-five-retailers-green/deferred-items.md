# Deferred items — phase 02

Out-of-scope discoveries. Logged, not fixed, per the executor scope boundary.

## ~~`Event loop is closed` noise after every browser render~~ — RESOLVED, and it was not cosmetic

**Found during:** 02-03, every live `fetch_rendered` call.
**Closed by:** the code review's CR-01. **This entry's diagnosis was wrong** and
is kept, struck through, as the record of how.

The entry below called the tracebacks cosmetic. They were the visible half of a
production resource leak. `asyncio.run` was closing the loop before nodriver's
Chrome child had been reaped, which is *why* the subprocess transports finalised
against a dead loop — and the same missing reap left a defunct `chrome` process,
plus its `/tmp/uc_*` profile, behind on every single render. Measured on the
deployed `boty.service` at 71 minutes of uptime: **13 zombies and 204 MB of
leaked profiles**, one of each per poll cycle, with no ceiling.

The lesson worth keeping: "the exit code is unaffected" is not evidence that
nothing is wrong. A stderr traceback from a *cleanup* path is a statement about
cleanup, and this one was true.

Fixed in `boty/browser.py` by `_teardown` — stop, `await proc.wait()`, then
remove the throwaway profile — with the timeout moved to bound the inner
coroutine so the teardown's `await` never runs under cancellation. Verified by
observation rather than argument, three real renders under the service
environment, before and after: `zombies=3, leaked uc_dirs=3` → `zombies=0,
leaked uc_dirs=[]`, and the tracebacks are gone with them.

---

*Original entry, preserved:*

> At interpreter shutdown, `asyncio.base_subprocess.BaseSubprocessTransport.__del__`
> fires after the loop `asyncio.run` created has already closed, and prints a
> `RuntimeError: Event loop is closed` traceback to stderr — twice, once per Chrome
> pipe. It is cosmetic: the render has already returned, the fixture has already
> been written, and the exit code is unaffected (`Exception ignored in:` means
> exactly that).
>
> It is still worth fixing, because it makes a successful `boty check` on a host
> with Best Buy configured look like it crashed, and a real traceback in that
> output would now be camouflaged by two fake ones.
>
> Cause is in `boty/browser.py:_render` — `asyncio.run` closes the loop while
> nodriver's subprocess transports are still referenced.
>
> Pre-existing since 02-01; not caused by 02-03's changes.

## `scripts/mutation_check.py` module docstring says "three mutations"

**Found during:** 02-03 (already noted by 02-02).

The docstring says "corrupts three specific things" and "THREE THINGS THAT WOULD
MAKE THIS PROVE NOTHING" enumerates four. There have been six mutations since
M4/M5 landed in phase 1. The equivalent drift in `README.md` was fixed by 02-03
because that file was being edited anyway; the script's own docstring was not
touched, to keep the mutation harness textually stable across a plan that moves
one of its anchors.
