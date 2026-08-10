# Adding a retailer

What to actually do when you want bot-y to watch a store it does not watch yet.

It exists because the instinct on adding a retailer is to write a class, and on
half the retailers in this repository that instinct is wrong. Three of the six
stores bot-y watches — GameStop, Walmart and Nintendo — have **no adapter code
at all**: they fall through `_make_checker` to `check_html`, which reads the
structured data their pages already publish. So the first job of this document
is to talk you out of the code you were about to write, and the second is to
tell you how to find out whether you are the exception.

The order below is the order to work in, and it is not the order it is tempting
to work in. The evidence comes before the code, the control comes before the
product watch, and the commit hook comes before your first commit.

---

## The default answer is "no adapter"

Nintendo is the worked example because it is the cheapest retailer here to
support and the most recent one added, so every edit it took is still visible in
the tree. There are four of them and none is an adapter.

### 1. Probe, and write the evidence before you write any code

Everything that comes back from a probe goes in `docs/retailer-evidence.md`,
under a `## ` heading beginning with the retailer's display name. That file
exists because *"we tried and it did not work"* is a claim, not a finding —
without the observation behind it, nobody six months from now can tell whether
the wall you hit was the retailer's or your own.

Nintendo's section (`docs/retailer-evidence.md` § Nintendo) records what a
probe looks like when it is done properly: **8 requests, spaced 12–20 s apart,
no refusal, no rate limiting, no retry needed**, and an observations table where
every row carries a status code or a byte count rather than an adjective. A
guessed slug came back HTTP **404** at 217,381 B as a genuine rendered error
page — which is how you learn that a wrong URL on this store is a clean 404 and
not a refusal. The product page came back at 416,346 B with one `ld+json` block
carrying `price=54.99`, `seller='Nintendo of America Inc.'` and `OutOfStock`.

Your section closes with a verdict line, and a verdict line is matched
mechanically by `scripts/evidence_check.py`, so it is one of exactly three
forms, character for character:

```
**Verdict: REACHABLE (rung N)**
**Verdict: REFUSED**
**Verdict: UNPROBED (scoped YYYY-MM-DD)**
```

There is deliberately no rung-4 REACHABLE form: rung 4 **is** refused. Copy one
of those three lines rather than paraphrasing it — a paraphrase reads fine and
fails the gate.

### 2. One `FIRST_PARTY` line

`boty/retailers.py` § `FIRST_PARTY` maps a retailer key to the seller names that
mean "the store itself". Nintendo's entry is:

```python
"nintendo": {"nintendo of america inc.", "nintendo", "nintendo.com"},
```

The first value is the literal `offers.seller.name` string read off a live page,
lowercased. The other two are the obvious short forms, and they are there so a
wording change at the retailer does not silently demote the manufacturer of the
product to an unrecognised third party. **Nothing longer is guessed.** One
observed string plus the obvious contractions of it is the whole rule; if you
find yourself inventing a fourth spelling you have not read a page yet.

### 3. Decide `MARKETPLACES` membership — and understand that leaving it out is a claim

`boty/retailers.py` § `MARKETPLACES` is the set of retailers where a third party
can hold the buy box. Nintendo is deliberately not in it, and the comment above
the set is the most important paragraph in this document:

> `nintendo` is deliberately absent, and that absence is a claim backed by
> evidence rather than an oversight: Nintendo's store has no third-party seller
> surface at all — no buy box, no "other sellers", nobody but Nintendo of
> America who can list on it. Adding it here "to be safe" would be the opposite
> of safe, because it would strip `_pick`'s unattributed-offer fallback and turn
> any future page that drops the seller node into a permanent UNKNOWN.

A blank is a claim. Adding your retailer to `MARKETPLACES` says "a reseller can
hold this buy box, so an offer with no seller attribution is UNKNOWN". Leaving
it out says "nobody but this store can list here, so an unattributed offer is
still theirs". Both are statements about the retailer, and both need a sentence
of evidence in your evidence-log section. Neither is the safe default.

### 4. Two YAML watches, one of them a control

`config/products.yaml` is where a retailer becomes something the monitor
actually reads, and adding a product is editing that file — no code, no type
unions, no rebuild. Nintendo has two entries: a product watch on the GO Plus +
with `max_price: 80` against a $54.99 MSRP, and a control watch on a
replacement HDMI cable. The comment above them says it in the repository's own
words:

**What `max_price` measures, because it decides whether your retailer can alert
at all.** It is the **delivered total** — item price plus shipping — and not the
item price: a $54.99 listing with $45 shipping is a $99.99 purchase, and a
ceiling reading the item price alone waves it through. Where your reader cannot
establish a delivered total, a watch with a ceiling **will not alert**, by
design. So if your retailer publishes a shipping cost, read it into
`Offer.shipping`; if it publishes one only as prose, do **not** parse it —
Nintendo's sentence yields $6.99 for an item that ships free, which is a wrong
verdict rather than a missing feature. A control watch carries no ceiling and is
unaffected either way.

> No adapter code exists for Nintendo and none is needed. Its pages carry
> ordinary schema.org Product markup that `check_html` already reads — the
> whole of its support is one FIRST_PARTY line and these two watches.

**The measurement, and it is the point of this whole section:** Nintendo ships
with **zero** new extractors, **zero** `_make_checker` branches and **zero**
`MARKETPLACES` entries. `check_html` reads it as shipped.

---

## Why a control product is mandatory

A control is a second watch on something that is *always* in stock at that
retailer. It is not optional, and the argument for it is already written in
`README.md` rather than re-derived here:

> When a retailer reskins its page, a selector-based monitor stops matching,
> reports out-of-stock forever, and **looks perfectly healthy.** You find out
> weeks later, having missed the drop. Silence and "no stock yet" are
> indistinguishable.

That is the failure this project exists to prevent, and it cannot be detected
from inside. A control is the only way to ask "does this detector still work?"
from outside the detector.

### The rule a control has to satisfy

`config/products.yaml` states it five times against five different retailers,
and it is the same rule every time: **first-party, evergreen, restocked
routinely, never the subject of a buy-box fight, and not a console.** A gallon
of milk is the archetype. A console is the anti-archetype — on a marketplace
those are frequently held by resellers, so an out-of-stock reading would be
*correct* and you would spend a day chasing a bug that is not there.

### The rule biting, on a real candidate that was rejected

Amazon's control is `B00NTCH52W`, a 20-pack of AA batteries. It is the second
candidate. The first was `B014I8SIJY`, an HDMI cable, and it was fetched and
then **rejected** — recorded in `docs/retailer-evidence.md` § Amazon rather than
quietly replaced — because its availability region read *"Only 2 left in stock -
order soon."*

A control that can plausibly sell out is a control that reddens `make verify`
for a reason that is not a defect, and a gate that cries wolf gets ignored
inside a week. The batteries read a flat *"In Stock"*.

Choosing a control is a recorded decision with a fallback, not a guess. Nintendo
names its reserve candidate in the config file in the same breath as its control
— if the cable is ever discontinued, the AC adapter takes over. Write yours
down the same way.

### Controls are not pass/fail, and you need to know that before you run them

`scripts/control_check.py` has three green-ish exits and they mean different
things:

| Exit | Means |
|---|---|
| **0** | Every control ran and read in stock |
| **3** | SKIPPED — `--offline` was passed, so nothing was learned either way |
| **4** | INCOMPLETE — some controls could not run **on this host** |

`README.md`'s verdict table carries the corresponding `VERIFY:` lines. The one
to expect on a fresh clone is **INCOMPLETE**: the shipped config carries a
mandatory Best Buy control, Best Buy's only credential-free path is a real
browser, and the browser extra is deliberately not installed by the dev extra.
That is a gap in your machine, not in your change, and the gate says so rather
than telling you your extractor broke.

---

## The UNKNOWN contract

From `boty/retailers.py`'s own module docstring, and it governs everything you
write:

> A checker takes a Watch and returns a Result. The contract that matters: if it
> cannot determine stock state, it returns UNKNOWN with a reason. It never
> guesses, and it never reports out-of-stock as a way of saying "the page
> changed and I got lost".

**An absence is never OUT_OF_STOCK.** The concrete form of that rule lives in
`boty/parse.py` § `add_to_cart_offers`, which returns `None` — never `[]`,
never `available=False` — when the add-to-cart control is not on the page.

The reasoning is worth copying because it shows what "measured" means here.
Target *keeps* the button and disables it when an item is out of stock, so on
Target an absent control means the render failed and returning UNKNOWN costs
nothing. Amazon *removes* the control, so on Amazon an absence is genuinely
ambiguous between "sold out" and "the page changed" — and since this repository
has never seen an unavailable Amazon page, it says UNKNOWN rather than picking.
That is a gap, and `docs/retailer-evidence.md` § Amazon records it as one
instead of papering over it with a guess.

### The seller default is per page family, and it is the most dangerous thing to get wrong

On Target, the *absence* of a seller block is the first-party signal — measured,
not assumed: zero occurrences of a "Sold & shipped by" block on the first-party
control page, unmissable on a partner-sold one.

Carrying that default across to Amazon would have meant that every Amazon buy
box the parser could not read would report as **sold by Amazon** — so a reseller
whose block failed to parse would alert, at whatever price they were asking.
This is exactly the alert this project exists not to send: the only GO Plus +
offer on Amazon today is a used unit at $219 against a $54.99 MSRP.

So on Amazon the default is `None`, which on a member of `MARKETPLACES` means
UNKNOWN, and `test_an_amazon_offer_with_no_seller_recorded_is_unknown_not_a_verdict`
in `tests/test_retailers.py` pins it. If your retailer shares a reader with another
one, the seller default is per page family and you have to say which family
yours is.

---

## When a new adapter is genuinely needed

Amazon is the second worked example, and the useful part is the diagnosis rather
than the code.

**The signature:** `check_html` reads Amazon's product page perfectly and says
UNKNOWN forever. Not a 403, not a challenge — three requests on 2026-08-03,
three HTTP 200s of 1.9–3.2 MB each, no block phrase anywhere. Amazon simply
publishes no structured data on that page: zero `ld+json`, no `__NEXT_DATA__`,
and no JSON blob carrying a price, an availability or a seller. A retailer that
serves you the page and withholds the data needs a **reader**, not a heavier
transport. Reaching for a browser at that point spends a Chrome process to
obtain something curl already returned.

**Where the code goes:** `boty/cli.py` § `_make_checker`, which is one function
with one `if` per special case and a fallback to `check_html`. There is **no
plugin registry**, and its docstring says why:

> `scripts/control_check.py` deliberately builds its checker with this same
> function rather than its own: a gate that routed requests differently from the
> running monitor would prove something about a code path nobody runs. So this
> stays one function with one `if`, and there is no registry to fall out of sync
> with it.

You add an arm. You do not register anything. `check_amazon` in
`boty/retailers.py` is what that arm points at: the same transport `check_html`
uses, a different reader, and `extraction=Extraction.DOM` on every path
including the error paths.

### Declare both axes, because they say different things

- **Rung** says how the bytes were obtained — 1 impersonated HTTP, 2 a
  documented API, 3 a real browser, 4 dropped with the evidence written down.
- **Extraction** says what was read out of them — `structured` for a retailer's
  own machine-readable feed, `dom` for presentation markup.

`Result.degraded` fires on **either** a browser transport or a `dom` extraction,
because both mean *discount this*. Amazon is the pathological case that widening
was done for: the cheapest transport in this repository with the most fragile
extraction in it.

Be blunt with yourself about what a `dom` row costs. **A reskin breaks it
silently** — no error, no 403, no red control until the next control cycle; the
parser simply stops finding the button and the reading goes quiet. That is why a
`dom` adapter's control watch is not negotiable, and why mutation M8 in
`scripts/mutation_check.py` inverts that reader's availability decision and
requires the suite to go red.

---

## What the gates already require of you

Four things, all of them enforced today. You are being told here so you find out
from a document rather than from a red run.

**1. An evidence-log section with a verdict line in one of the three exact
forms.** `scripts/evidence_check.py` reads `docs/retailer-evidence.md` on every
`make verify`. If your verdict is REFUSED it needs at least one anchored line of
the form `**Refusal observed (rung N):**` whose body carries a **measurement** —
an HTTP status code, a byte count, or a quoted block phrase. Target and Amazon
need two, including one at rung 3. Prose alone is rejected, and the reason is
worth stating plainly: an anchored line by itself is satisfiable by typing the
sentence, and this project has already dropped two retailers on a desk review of
their written terms with every gate green.

**2. A README support-matrix row that passes `tests/test_support_matrix.py`.**
The table is located by its header cells, so prose around it can move freely,
but the row label must match your retailer's display value in
`scripts/evidence_check.py` § `ROADMAP_RETAILERS` character for character,
accent included. The cell vocabularies are fixed. If a row does not match, fix
the README label — do not loosen the comparison, or the file stops being able to
fail.

**3. Fixtures redacted by class, not by value, before they are committed.** Two
incidents, one sentence each. A Target capture carried a session token, a
visitor id, this host's geolocation and five nearby store addresses, and the
automated guard **passed** on it. Widening the guard then found the same leak
class already committed in four Walmart and Best Buy fixtures. Redact by
emptying every `<script>` body and every host marker, not by deleting the
specific strings you happened to notice — a guard that only knows the exact
spelling it was taught keeps passing until the shape changes. And when you write
the redaction record, do not name the values you removed: a record that spells
out what it took out is a copy of it.

**4. `make hooks`, before your first commit.** This is the security-critical
instruction in this document.

`hooks/pre-commit` is tracked, so you get it when you clone — but installing it
is deliberately opt-in, because writing to a git hook directory behind someone's
back is the kind of thing a build should ask for. Until you run `make hooks`,
you have **no protection at all**. It checks only staged files, so it costs
milliseconds on a normal commit.

The distinction that matters: `make verify` finds a leak *after* it is in
history. The hook finds it before. This repository has already had to rewrite
its own published history over a value that had already been pushed to the
public repository — and it got there through a planning document, not a fixture
and not a test, which is why
`scripts/identity_check.py --all` scans **every tracked file** rather than only
the fixture tree.

If the hook fires and you are certain it is a false positive, widen the rule in
`scripts/identity_check.py` and add a test case for it. Do **not** bypass with
`--no-verify`, and do **not** add the value to an allow-list. Both of those
close the finding without changing what the guard knows, which means the next
person hits it too and the one after that does not.

---

## Before you open a pull request

`make hooks` once. Then, every time:

```bash
make verify-offline
```

**Use the offline target, not `make verify`.** `make verify` makes live requests
to six retailers, and the politeness budget here is a real constraint rather
than a slogan. The per-retailer pacing overrides in `config/products.yaml` exist
because nobody had done the arithmetic — `interval_seconds` is per *pass*, not
per request, so a retailer's real load is watches × 288 per day — and the two
retailers carrying the most watches are exactly the two that started refusing.
Contributor PR loops making live retailer requests is that same arithmetic with
more people in it.

Two rules that follow from the same place:

- **Do not escalate transports to get past a refusal.** The ladder says stop at
  the first rung that works, and it also says stop at the rung that refused you.
  A retailer that turned down plain HTTP has not invited an impersonating one.
- **Do not re-probe a retailer with a written refusal** without reading its
  section in `docs/retailer-evidence.md` first. Some of those sections carry an
  explicit instruction about whether and when to look again.

Credentials live in the environment and never in the repository. The Best Buy
API key and the notification URL are read from environment variables by design —
they must not appear in `config/products.yaml`, in a fixture, or in your diff.
The API key is an optional upgrade in any case: every retailer here works
without one.

Contributions are accepted under the project's [MIT](LICENSE) licence.
