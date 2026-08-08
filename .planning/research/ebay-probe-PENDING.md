---
status: awaiting-external
opened: 2026-08-08
blocks: next milestone roadmapping (eBay)
---

# eBay probe — waiting on keyset activation

**State on 2026-08-08:** Dan registered for the eBay Developers Program and created a
**Production** keyset. eBay said to **allow one day** for activation, so the probe has not
been run. Nothing is blocked except roadmapping the eBay milestone, which is deliberately
held until this is measured.

## The one question this settles

Does a **self-serve** production keyset actually serve `Browse item_summary/search`?
`.planning/research/ebay-access-surface.md` § 2 records eBay's own documentation
contradicting itself on this, and refuses to resolve it by preference.

| Outcome | eBay is | Consequence |
|---|---|---|
| `200` + populated `itemSummaries` | **rung 2 + `structured`** | the project's first true rung-2 path; can be a PRIMARY path (opt-in credential) |
| `403 Insufficient permissions` | **Best Buy's row** | OPTIONAL enhancement only, never the documented way it works |

There is no third outcome, and no credential-free fallback: `robots.txt` carries 211
disallow lines over `/sch/`, so keyword search — the only path that answers "is anyone
selling one cheap right now" — is closed.

## How to run it

```sh
<scratchpad>/ebay_probe.sh ~/.config/boty/ebay-probe.env
```

The script mints a client-credentials token, then does one `item_summary/search` for
"pokemon go plus" (limit 3). It **never prints either secret** — only their lengths — and
reports status codes and byte counts in this repo's evidence idiom. Dry-run against a
bogus keyset returns `HTTP 401 invalid_client` cleanly rather than hanging.

If the scratchpad is gone, the script is ~70 lines and trivially rewritten from the three
steps in `ebay-access-surface.md` § 2.

## Already-measured friction, worth carrying into the accessibility decision

Dan's objection on 2026-08-07 was that requiring a developer account is a barrier:
*"People aren't gonna download this if they need to be a developers. That's not helpful."*

The research had described the signup as "three clicks and a gate", i.e. **friction, not
approval**. That description is now **partly falsified by observation**: activation is not
instant. eBay quoted **about a day**. So even in the favourable branch, enabling eBay costs
a new user a developer-program signup, an account-deletion exemption, and a **~1-day wait**
before the first call succeeds.

That does not change the rung — a wait is not an approval — but it does weaken the
"three clicks" framing that the optional-retailer argument leaned on, and it should be
stated plainly wherever eBay's setup is documented rather than discovered by a user who
thinks their config is broken on day one.

## Not yet recorded in docs/retailer-evidence.md

eBay has **no verdict row**. The honest line today is `**Verdict: UNPROBED (scoped
2026-08-07)**`. Do not open a row with a verdict until the probe runs — rule 6 requires a
measured observation, and neither branch has one yet.
