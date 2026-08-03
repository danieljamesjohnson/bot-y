# Blocked on Dan

Two things I cannot do myself. Everything else in the MVP is proceeding without them.

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
