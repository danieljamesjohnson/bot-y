# Fixtures

Frozen copies of real retailer product pages, each stored as
`<retailer>/<name>.html` with a `<retailer>/<name>.json` sidecar recording when
it was captured and what stock state it represented.

## What they are for

Catching **code** regressions in the extraction layer, offline and
deterministically. If a change to `boty/parse.py` or `boty/retailers.py` stops a
detector reading a page it used to read correctly, the fixture tests go red
immediately — no network, no flakiness, no rate limits, same result on your
laptop and in CI.

## What they are NOT for

**A green fixture suite does not mean a retailer still works.** It means the
code still does the same thing to a page captured on some date in the past. If
Walmart reshapes `__NEXT_DATA__` tomorrow, every fixture test here keeps passing
while the live detector reads UNKNOWN on every real check.

Telling you whether a retailer still works is the job of the **live control
products** — known-in-stock items checked against the real site on every pass,
which raise a health alert the moment a detector stops seeing them. That gap is
not an oversight; it is the whole design:

| | Catches | Misses |
|---|---|---|
| **Fixtures** (this directory) | Code regressions: a refactor breaks an extractor | Reality: the retailer changed its page |
| **Live control products** (`config/products.yaml`, `control: true`) | Reality: a known-in-stock item stops reading in stock, so the detector is broken | Code regressions that happen to affect no control |

Neither substitutes for the other. Believing that green fixtures prove a working
detector is exactly the false confidence this project exists to eliminate — it
is the same error as a monitor reporting "out of stock" when the truth is "I
could not parse the page."

## Fixtures are frozen on purpose

They are never auto-refreshed in CI. Auto-refreshing would let a genuine
breakage land disguised as a fixture update: the retailer changes, the capture
step quietly re-saves the new page, the expectations are regenerated to match,
and the suite stays green while the detector is broken. Refreshing a fixture is
a deliberate human act with a diff you have to look at.

## Capturing a new fixture

```
boty capture-fixture <retailer> <name> <url> --note "<what stock state this is>"
```

Worked example — the Walmart GO Plus + page, which at capture time was held by a
marketplace reseller:

```
boty capture-fixture walmart goplusplus \
  "https://www.walmart.com/ip/Pok-mon-GO-Plus-for-Nintendo-Switch/1203950273" \
  --note "IN_STOCK but seller is a marketplace reseller at ~4x MSRP; must be rejected by first-party filter AND by price ceiling"
```

That writes `walmart/goplusplus.html` plus a sidecar with `url`, `retailer`,
`name`, `captured_at`, `status`, `bytes` and your `note`.

Notes:

- **Always write a `--note`.** A 470 KB wall of HTML with no note is
  uninterpretable six months later; nobody can tell whether it is still a
  meaningful test case or a stale snapshot of a page that has since changed.
- **A blocked fetch writes nothing.** If a bot wall answers instead of the page,
  `capture-fixture` exits 1 and leaves no file. A CAPTCHA interstitial saved
  under a product's name would make the entire suite assert against a bot wall
  while looking perfectly green.
- **Check the marker.** After capturing, confirm the file actually contains the
  structured data its extractor depends on — `application/ld+json` for GameStop,
  `__NEXT_DATA__` for Walmart. If it does not, the page changed or the fetch was
  degraded; delete it rather than committing a useless fixture.
- **A synthetic fixture is acceptable if it is labelled.** If a page no longer
  exercises the case you need (say the reseller loses the buy box), hand-editing
  one is fine — but say so in the note, and say why.

Load one in a test with no network capability:

```python
from boty.fixtures import load

html = load("walmart", "goplusplus")
```

`boty.fixtures` imports `boty.fetch` lazily, inside `capture()`, so importing the
module in a test cannot reach the network.

## Staleness

`make verify` warns when a fixture is more than 90 days old. It is a warning,
not a failure — an old fixture is still a valid regression test of the code.

When you see the warning:

1. Re-capture the page with the same command.
2. Re-run the tests and **read the failures**. If the expected values changed,
   that is not a chore — it is a real signal that the retailer changed something,
   and the live detector may already be wrong.
3. Update the expectations and the note together, in one reviewable commit.
