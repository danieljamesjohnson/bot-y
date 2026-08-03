# Blocked on Dan

Two things I cannot do myself. Everything else in the MVP is proceeding without them.

## 0b. Target is rung 4 too — so the five-retailer bar is UNMET, at four

**Not blocking, and there is nothing for you to do.** This is the note the two
below were setting up, and it is the one that closes the question: Phase 3's
criterion 5 wanted five working retailers. **It lands on four** — gamestop,
walmart, bestbuy, nintendo — and it is recorded as unmet rather than padded.

Target's Terms & Conditions (retrieved 2026-08-03,
`https://www.target.com/c/terms-conditions/-/N-4sr7l`, document header
`LAST UPDATED: April 15, 2026`) forbid this in the `Unlawful or Prohibited Uses`
section:

> Make any use of data extraction, scraping, mining or other data gathering
> tools, or create a database by systematically downloading or storing Site
> content, or otherwise scrape, collect, store or use any Content, account
> information, product listings, descriptions, prices or images…

That bullet carries no commercial-use qualifier — unlike the one above it, which
does, and which would not have reached a personal restock monitor. And the
Introduction closes the obvious objection in advance: *"Any person or entity who
interacts with the Site through the use of crawlers, robots, browsers, data
mining or extraction tools … is considered to be using the Site"*, and using the
Site is agreeing to the terms. A scraper never clicks "I agree"; Target has
written down that it does not need to.

- **Zero requests were made to any Target product page.** The terms were read
  first, deliberately, the same way Amazon's were. Four `curl` requests total —
  two policy pages and two `robots.txt` files — all HTTP 200, ≥15 s apart. The
  politeness budget was 12; 4 were spent, and no product page, TCIN lookup or
  browser render ever happened.
- **robots.txt is BROADER than the terms here, which is the opposite of Amazon.**
  `www.target.com/robots.txt` does not disallow `/p/` at all, has no named-bot
  blocks, and *publishes* `sitemap_pdp-index.xml.gz` — a product-detail index
  that would have solved the TCIN problem this project gave up on in Phase 2. It
  was not used. Taking the `/p/` gap because robots.txt omits it, while the
  terms name prices explicitly, is the posture this project already ruled out
  for Amazon's `/dp/` gap.
- **Rung 2 (RedSky) is closed four ways.** `redsky.target.com/robots.txt` is
  `User-agent: * / Disallow: /` — the whole host, every agent. Its `key`
  parameter is not issuable: there is no portal and no signup, and the only way
  to get one is to lift Target's own front-end constant, which means presenting
  yourself to Target's API as Target's website. The terms cover it regardless of
  hostname. And it is CAPTCHA-gated in practice, which is the least important of
  the four because it is the only one that could change.

**What it costs:** the fifth retailer, and that is now final rather than
pending. Phase 3's two candidates were Target and Amazon; both are **rung 4**,
both by written prohibition rather than by a wall, and neither cost this host a
single product-page request. There is no third candidate — the Phase 2 search
established that no other US retailer stocks the Pokémon GO Plus +, and a
control-only retailer like Micro Center was probed and explicitly declined
because it could never alert on the product.

**What it does not cost:** anything else. `make verify` exits 0, all four
retailers are control-verified and read IN_STOCK, `healthy` is true, and
Nintendo still lists the GO Plus + at $54.99 MSRP first-party with no
marketplace attached — the best restock signal this project has.

Every retailer in the roadmap's scope is now either shipped or refused in
writing, so the gap is fully described rather than merely small.
`scripts/evidence_check.py --phase` passes on this tree for the first time, and
03-03 wires it into `make verify` so the four cannot quietly become five.

Full evidence — the clauses in context, the four requests with byte counts, both
`robots.txt` files, and why nobody should re-probe — is in
`docs/retailer-evidence.md` under `## Target`.

## 0a. Amazon is rung 4 — settled by its Conditions of Use, without a single probe

**Not blocking, and there is nothing for you to do.** Same shape as the Pokémon
Center note below: a number that will not match the roadmap, written down before
you have to ask about it.

Amazon's Conditions of Use (retrieved 2026-08-03,
`https://www.amazon.com/gp/help/customer/display.html?nodeId=GLSBYFE9MGKKQXXM`,
document header `Last updated: May 30, 2025`) grant a licence to use the site
that explicitly **excludes** —

> …any collection and use of any product listings, descriptions, or prices; …
> or any use of data mining, robots, or similar data gathering and extraction
> tools.

Availability and price are the only two things bot-y reads. There is no reading
of that sentence under which this monitor is doing something else, and no
transport changes which side of it we are on. So it is **rung 4**, and the
decisive reason is a written prohibition rather than a wall — which is the more
durable finding, because a wall can fall and this cannot.

- **Zero requests were made to any Amazon product page.** The terms were read
  first, deliberately, so that `docs/retailer-evidence.md` could say plainly
  that bot-y makes no requests to amazon.com. Six `curl` requests total, all to
  policy and developer-documentation pages, spaced 22–24 s apart.
- **robots.txt is narrower than the ToU, and they disagree.** `/dp/<ASIN>`
  carries no `Disallow`, but `/dp/product-availability/` and `/gp/offer-listing/`
  — the paths that most directly answer the stock question — are closed. Reading
  `/dp/` because robots.txt forgot to mention it, while the ToU names prices, is
  the posture this project has already ruled out.
- **Rung 2 is closed too, and it moved recently.** The Product Advertising API 5
  is deprecated and now answers HTTP 403. Its successor, the Creators API,
  requires an Amazon Associates account — a commercial agreement, plus a tax
  interview, a Partner Tag and per-region approval. A fresh clone cannot get
  that, which is the same test Best Buy's API failed.

**What it costs:** the fifth retailer, if Target also refuses. That is criterion
5 of Phase 3 and it would then be recorded as unmet rather than padded. Nothing
is blocked on you either way, and Target is the next plan.

Full evidence, including the quoted clause in context and the six requests with
their byte counts, is in `docs/retailer-evidence.md` under `## Amazon`. This
phase also shipped `scripts/evidence_check.py`, which makes the shortfall
mechanically impossible to paper over later — Phase 2's version of that gate had
decayed into one that could no longer fail.

## 0. Pokémon Center is rung 4 — the MVP ships with FOUR retailers, not five

**Not blocking, and there is nothing for you to do. This is a heads-up about a
number that will not match the roadmap.**

Phase 2's criterion 4 says five retailers. It lands on **four**: gamestop,
walmart, bestbuy, nintendo. Pokémon Center was walked all the way down the
escalation ladder and refused at every rung, so it is documented as unreachable
rather than shipped as a detector that cannot detect anything.

- **Rung 1** (`curl_cffi`, chrome impersonation): product pages return Imperva's
  `Pardon Our Interruption` at HTTP **200** (6,183 B), or a DataDome JS
  challenge at HTTP 403 (858 B) on a cold connection. Four attempts, two
  products, warmed session and cold. The **homepage** reads fine at rung 1 both
  before and between those refusals — so this host is not IP-banned, the wall is
  specifically on `/product/*`.
- **Rung 2**: no documented public API, and Pokémon Center's own `robots.txt`
  explicitly `Disallow`s `/cortex`, `/availabilities`, `/prices`, `/offers` and
  `/items` — the exact endpoints that would answer the stock question. Closed by
  the retailer's stated wishes, not just unavailable.
- **Rung 3** (headless Chrome): refused twice, 120 s apart. `Request
  unsuccessful` / `_Incapsula_Resource`, 1,085 B. `boty capture-fixture`
  correctly refused to save the challenge page as a fixture.
- **Rung 4**: documented. Full evidence, including the two probes worth
  retrying later, is in `docs/retailer-evidence.md`.

**No Pokémon Center watch was added to `config/products.yaml` to make the count
read five.** The GO Plus + genuinely is listed there
(`/product/715e10557/pokemon-go-plus`), so a watch would have looked entirely
plausible — and would have been a permanently UNKNOWN detector raising a
permanent health warning. Every other phase criterion holds: `make verify` exits
0, all four retailers are control-verified, and `healthy` is true.

Nintendo more than earned its place, incidentally: it stocks the GO Plus + at
$54.99 MSRP, first-party, with no marketplace anywhere near it. That is the best
restock signal this project has.

Phase 3 targets Target and Amazon. If either lands, the count reaches five
there.

**Update, 2026-08-03: neither landed.** Both are rung 4, both by a written
prohibition in the retailer's own terms rather than by a wall. The count stays
at four and criterion 5 is recorded unmet — see `0b` and `0a` above.

## 1. Telegram bot token — REGENERATE FIRST

The token in the script you dropped is **burned**. It was hardcoded in source and
is now sitting in plaintext in two files on danserver
(`~/feedback-drop/pokemongoplusplus/inbox/2026-08-02_13-51-33/{note.txt,meta.json}`)
after crossing a web form.

- Revoke it in **BotFather** → `/revoke` → pick the bot
- Then put the new one in `/home/dan/.config/boty/env` (I create this file with
  mode 600 and a placeholder):

```
BOTY_NOTIFY_URL=tgram://<new-bot-token>/8119711705
```

The chat id `8119711705` is from your script and should still be valid.

Until this is set, `boty watch` runs and logs normally but sends nothing. The
systemd unit is wired and will pick it up on next restart:
`sudo systemctl restart boty`

## 2. Best Buy API key — NO LONGER BLOCKING (optional enhancement)

Downgraded: the signup requires manual approval and rejects free email domains,
so anyone cloning this repo hits the same wall. Best Buy's primary path is now
rung 3 (browser, flagged DEGRADED) which needs no credentials. If your key is
approved, set it and Best Buy upgrades to the more reliable API path and loses
the DEGRADED flag — but nothing waits on it.

### Original note

Best Buy refuses impersonated HTTP at the connection layer regardless of TLS
fingerprint (HTTP/2 stream reset; HTTP/1.1 times out). Verified across
`chrome` and `safari` impersonation. So the official API is the only viable
path — scraping it is a dead end, not a tuning problem.

- Free key: https://developer.bestbuy.com/ (sign up, instant)
- Add to `/home/dan/.config/boty/env`:

```
BESTBUY_API_KEY=<key>
```

The adapter (`boty/retailers.py::check_bestbuy_api`) is written and waiting.
Without a key, Best Buy watches are skipped rather than reported as failures.

---

## Decision I made without you (reversible)

You asked about GSD/ECC for the build-out. I skipped it. The architecture is
settled and the remaining work is a long tail of ~50-line retailer adapters,
each following the pattern GameStop and Walmart already establish — the
planning overhead would have exceeded the work.

I'd revisit that if you want the web UI, a plugin system for community retailer
definitions, or a hosted version. Those have real design surface.
