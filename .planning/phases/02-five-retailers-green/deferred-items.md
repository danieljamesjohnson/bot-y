# Deferred items — phase 02

Out-of-scope discoveries. Logged, not fixed, per the executor scope boundary.

## `Event loop is closed` noise after every browser render

**Found during:** 02-03, every live `fetch_rendered` call.

At interpreter shutdown, `asyncio.base_subprocess.BaseSubprocessTransport.__del__`
fires after the loop `asyncio.run` created has already closed, and prints a
`RuntimeError: Event loop is closed` traceback to stderr — twice, once per Chrome
pipe. It is cosmetic: the render has already returned, the fixture has already
been written, and the exit code is unaffected (`Exception ignored in:` means
exactly that).

It is still worth fixing, because it makes a successful `boty check` on a host
with Best Buy configured look like it crashed, and a real traceback in that
output would now be camouflaged by two fake ones.

Cause is in `boty/browser.py:_render` — `asyncio.run` closes the loop while
nodriver's subprocess transports are still referenced. Likely fix: drive the loop
manually (`new_event_loop` → `run_until_complete` → `shutdown_asyncgens` → let
the transports finalise before `close()`), or await the browser's own teardown
rather than calling the synchronous `browser.stop()` in the `finally`.

Pre-existing since 02-01; not caused by 02-03's changes.

## `scripts/mutation_check.py` module docstring says "three mutations"

**Found during:** 02-03 (already noted by 02-02).

The docstring says "corrupts three specific things" and "THREE THINGS THAT WOULD
MAKE THIS PROVE NOTHING" enumerates four. There have been six mutations since
M4/M5 landed in phase 1. The equivalent drift in `README.md` was fixed by 02-03
because that file was being edited anyway; the script's own docstring was not
touched, to keep the mutation harness textually stable across a plan that moves
one of its anchors.
