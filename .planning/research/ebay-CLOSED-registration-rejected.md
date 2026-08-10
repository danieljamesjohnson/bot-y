---
status: resolved
opened: 2026-08-08
closed: 2026-08-10
outcome: eBay is not reachable for this project — registration refused
---

# eBay probe — closed. The registration was rejected, so the probe never ran.

**Superseded the pending state of 2026-08-08.** The probe described below was never
executed, because the credential it needs cannot be obtained.

## What happened

Dan registered for the eBay Developers Program on 2026-08-08 with a real, established eBay
account. eBay said to allow about a day. On **2026-08-10** the registration came back
**rejected**, verbatim:

> Your account registration was rejected due to problems with the data provided or other
> irregularities. If you believe this rejection is in error, please see our FAQs and
> Contact Channels page or work with your eBay representative directly.

No reason was given beyond that boilerplate, and the remedy offered is *"work with your
eBay representative"* — i.e. a commercial relationship.

## Why this closes the question rather than deferring it

`.planning/research/ebay-access-surface.md` § 2 recorded eBay's own documentation
contradicting itself about whether production Browse access is self-serve, and deliberately
refused to resolve it by preference. It named one probe that would settle it, and said the
first step might answer everything with no HTTP request. **It did.**

The finding is stronger than the 403 we were looking for:

- A **403** would have said *this keyset is not entitled to this API*.
- A **rejected registration** says *this person does not get a keyset at all*.

And it is a **measured observation, not a policy reading** — which matters in this repo
specifically. Phase 3 dropped Target and Amazon on a reading of their Terms of Use having
never sent a request, and Phase 3.1 had to reverse it; rule 6 in `scripts/evidence_check.py`
exists because of that. This is the opposite shape: an attempt was made and refused.

## What it means against this project's own rules

`REQUIREMENTS.md` § Non-Functional Requirements, *Works from a fresh clone*:

> Paths requiring a credential most people cannot obtain — manual approval, a paid domain,
> a commercial agreement — may be supported as an OPTIONAL enhancement, but never as the
> documented way that retailer works.

A credential whose **registration is discretionary and can be refused without a stated
reason** is squarely in that class. It is a harder failure than Best Buy's:

| | Best Buy (REQ-04) | eBay |
|---|---|---|
| Credential gated? | Yes — approval + non-free email domain | Yes — and the registration itself was **refused** |
| Credential-free fallback? | **Yes** — rung 3 browser read, ships today | **No.** `robots.txt` carries 211 disallow lines over `/sch/`, closing all keyword search — the only path that answers "is anyone selling one cheap right now" |
| Shippable as optional? | Yes, and it is | **No** — the author cannot obtain the credential, so there is nothing to ship even as an opt-in |

So eBay is **dropped**, and the reason recorded is an observation.

## Not written into docs/retailer-evidence.md, deliberately

Two reasons, both worth stating so the next person does not assume it was an oversight:

1. **eBay is not one of the roadmap's retailers.** The seven are GameStop, Walmart, Best Buy,
   Pokémon Center, Nintendo, Target and Amazon. eBay was a candidate for a *future*
   milestone, never a v1.0 target, so the evidence log has no gap.
2. **Rule 6's grammar does not fit this refusal.** `REFUSAL_RE` requires
   `**Refusal observed (rung [1-3]):**` with a status code, byte count or matched block
   phrase in the body — it is built for a *transport* refusal. Zero requests were ever made
   to eBay's API or listing pages. Writing a `**Verdict: REFUSED**` here would mean bending
   a gate to fit a different kind of event, which is the failure mode that gate exists to
   prevent. If eBay is ever revisited, the honest entry is a new section stating the
   registration rejection in its own terms.

## If it is ever revisited

- The rejection *may* be appealable, and "problems with the data provided" may be something
  mundane. One retry is cheap and would cost nothing but time.
- **The structural finding stands either way.** Even if Dan personally gets through on
  appeal, a registration that can be refused at eBay's discretion cannot be the documented
  way a retailer works for someone cloning this repo. It would make eBay a personal
  enhancement for one operator, not a supported retailer.
- Everything else researched still holds and is worth keeping:
  `ebay-prior-art.md` (build, take no dependency; `ebay-rest` is 82× the size of `boty/`)
  and `ebay-access-surface.md` (the field list, the 5,000/day cap, and § 5's finding that
  the first-party seller filter is meaningless on a marketplace and the price ceiling must
  apply to the **delivered total**). That last one is a good idea independent of eBay.
