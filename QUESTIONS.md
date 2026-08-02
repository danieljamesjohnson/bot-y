# Blocked on Dan

Two things I cannot do myself. Everything else in the MVP is proceeding without them.

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

## 2. Best Buy API key

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
