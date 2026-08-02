# bot-y

A self-hosted restock monitor for big US retailers that **tells you when it breaks.**

```
● gamestop  CONTROL — PS5 console       $  549.99  ld+json: InStock from GameStop      [control]
○ gamestop  Pokémon GO Plus +           $   54.99  ld+json: OutOfStock from GameStop
○ walmart   Pokémon GO Plus +                      1 offer(s), none first-party
```

## Why another one

The existing tools are mostly dead. The big-retailer monitors on GitHub stopped
getting real commits in 2021–22, which is exactly when Akamai and PerimeterX got
serious. What's left either targets soft Shopify/sneaker sites, or is a
general-purpose page watcher pointed at the most defended pages on the consumer web.

bot-y is built around three things those tools get wrong.

### 1. "I don't know" is not "out of stock"

This is the bug that matters. When a retailer reskins its page, a selector-based
monitor stops matching, reports out-of-stock forever, and **looks perfectly
healthy.** You find out weeks later, having missed the drop. Silence and "no
stock yet" are indistinguishable.

So `Availability` has three values, and a detector that can't tell must say
`UNKNOWN`. Then every retailer carries a **control product** — something known to
be in stock. If the control stops reading in-stock, the detector is broken and
you get paged about *that*, as loudly as a real restock.

### 2. "In stock" from a scalper is not a restock

On marketplaces a sold-out item is nearly always available from resellers at a
markup. The Pokémon GO Plus + has a $54.99 MSRP and sits on Walmart at $229.99
from a third-party seller, while Walmart itself has none.

bot-y reads the seller on each offer and defaults to first-party only, with an
independent price ceiling as a second line of defence. Either alone suppresses
that listing.

### 3. Fetching: TLS first, browser last

Anti-bot systems read your TLS ClientHello **before any HTTP header arrives**. A
stock `requests` handshake is identifiable as a script no matter what User-Agent
it sends — header spoofing is theatre, and a headless browser fixes the
JavaScript fingerprint while leaving the TLS one untouched.

bot-y uses [`curl_cffi`](https://github.com/lexiforest/curl_cffi) to replay a real
Chrome TLS stack. In practice this reaches pages that a full Playwright browser
gets served a CAPTCHA on — at a fraction of the cost, with no browser at all.

Stock state is then read from **structured data** — schema.org JSON-LD, Next.js
hydration payloads — rather than CSS selectors. Retailers keep those accurate
because Google Shopping depends on them, so they rot far more slowly than class
names.

## Retailer status

| Retailer | Method | Status |
|---|---|---|
| GameStop | `curl_cffi` + schema.org JSON-LD | ✅ Working |
| Walmart | `curl_cffi` + `__NEXT_DATA__`, seller-aware | ✅ Working |
| Best Buy | Official API (free key) | ⚠️ Needs a key — Best Buy refuses impersonated HTTP at the connection layer, so scraping it is a losing game |
| Target | RedSky API | 🚧 Planned |
| Pokémon Center | — | 🚧 Planned |

## Install

```bash
git clone https://github.com/danieljamesjohnson/bot-y
cd bot-y
python3 -m venv .venv && .venv/bin/pip install -e .
```

## Use

Adding a product is editing `config/products.yaml`. No code, no rebuild:

```yaml
watches:
  - name: Pokémon GO Plus +
    retailer: gamestop
    target: https://www.gamestop.com/.../pokemon-go-plus-plus/20003961.html
    max_price: 80

  - name: CONTROL — Great Value whole milk
    retailer: walmart
    target: https://www.walmart.com/ip/.../10450114
    control: true
```

```bash
boty check    # one pass, print a table
boty watch    # loop, notify on transitions
```

Notifications go through [Apprise](https://github.com/caronc/apprise), so Telegram,
ntfy, Discord, Slack and ~100 others work out of the box:

```bash
export BOTY_NOTIFY_URL='tgram://<bot-token>/<chat-id>'
```

**Pick controls carefully.** A grocery staple is ideal — first-party, restocked
daily, never contested. Don't use a console: on Walmart those are often held by
marketplace sellers, so an out-of-stock reading would be *correct* and you'd
chase a bug that isn't there.

## Being a good citizen

Default cadence is 5 minutes with jitter, which is plenty for a drought that
lasts weeks. Polling every few seconds buys nothing and is what gets an IP
blocked. This is a personal notification tool — it does not add to cart, does not
check out, and does not run at a scale that would be unfair to anyone else
shopping.

## License

MIT
