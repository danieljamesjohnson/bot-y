# A reading does not carry its age

**Found 2026-08-13, by Dan asking a question the system could not answer.**

He asked, of the Amazon and Walmart GO Plus + watches: *"so they are out of stock
as of when?"*

There is no recorded answer. Not a hard one to find — **absent**.

## What is actually stored

`state.json`, the file that survives restarts, stores the availability string and
nothing else:

```
"walmart:Pokémon GO Plus +"   ->   "out_of_stock"
```

Every entry is a bare string. `sorted({f for v in state.values() if isinstance(v, dict) for f in v})`
returns `[]` — there are no per-entry fields at all.

`served/boty/status.json` carries one top-level `updated` for the **whole cycle**,
and its per-watch rows have these fields and no other:

```
alertable, availability, control, degraded, detail, extraction,
name, price, retailer, rung, store, store_pinned, url
```

No timestamp. So a row that was read four seconds ago and a row last read two days
ago are **byte-identical in shape**, and the page presents both as current.

## Why this is the project's own defect, one level up

v0.2's thesis was *say only what you measured*. A reading with no age is a claim
about **the past, presented as the present** — the same shape as *"the detector is
probably broken"*, except the unestablished thing is **when**.

It has teeth rather than being tidiness. A retailer that refuses us backs off to
multi-hour intervals, so **the rows least likely to be current are exactly the ones
that look identical to the fresh ones**. The staler the reading, the longer it sits
there looking like fact.

## The measurement that opened it

Reconstructed from refusal history, because nothing recorded it directly:

| Watch | `state.json` says | Actually last read |
|---|---|---|
| Amazon GO Plus + | `out_of_stock` | early 2026-08-13, before ~06:37 — refusal streak of 2 began then, and the counter had reset, which only happens on a successful read |
| Walmart GO Plus + | `out_of_stock` | **cannot be established.** No later than 2026-08-12 16:49, plausibly 2026-08-11 |
| Nintendo GO Plus + | `out_of_stock` | within the last cycle or two — it is healthy |

Walmart is the honest failure: its refusal streak of 7 traces to 2026-08-12
16:49:57, but **a service restart at that moment zeroed the counter**, so the
streak may be longer and the last real read older. The evidence that would have
settled it was destroyed by the restart. That is itself worth keeping — the
reconstruction only worked at all because `pacer-state.json` persists
`refused_at`, and it stopped working precisely where that persistence began.

## What a fix looks like

Follow the `store` field's path exactly — it is the worked precedent, four times
over (`rung`, `extraction`, `degraded`, `store`):

1. Stamp each `Result` when it is read.
2. Persist it, and publish it per-watch in `status.json`.
3. Surface it in `boty check` and on the dashboard.
4. **Gate it:** a reading older than its retailer's current interval is shown as
   stale rather than as fact — and where there is no stamp, say `unknown` rather
   than guessing. Watched going red.

The interval is the right comparison rather than a fixed clock, because a
retailer in backoff is *legitimately* checked less often; what is dishonest is
not the age, it is presenting an age you never recorded.

## Not to be confused with

- **`status.json`'s `updated`** — that is when the *cycle* ran, not when a
  particular retailer answered. It is fresh even when every row in it is stale.
- **The fixtures' 90-day staleness warning** (`make verify`'s `fixtures` stage) —
  that ages *captured test pages*, not live readings.
