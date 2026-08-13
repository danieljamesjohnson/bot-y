# Changelog

What changed in each release, and what each change was measured against.

It exists because a version number is a claim and nothing else in a published
artefact explains it. `pip install bot-y` hands someone a monitor whose whole
argument is that it refuses to report a stock verdict it cannot back — so a
release note that says "improved reliability" would be the wrong register for
this project twice over. Every entry below names the thing that changed and,
where there is one, the measurement behind it. `pyproject.toml` states the
version, and two separate checks bind this file's top heading to it:
`scripts/release_check.py` at release time, over the network, and
`tests/test_packaging_metadata.py` in every `make verify-offline` run — which
binds the same number to `README.md`'s publication instruction and to this
project's own milestone record as well. So the numbers cannot drift, and the
offline half runs on every commit rather than only on a release day.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Nothing yet.

## [0.3.0] - 2026-08-13

**Nothing is tagged, uploaded or released here either** — `git tag -l` is empty and
`pypi.org/pypi/bot-y/json` is 404, exactly as at `0.2.0`. This heading marks the line the
tree is on, opened when milestone v0.3 was scoped on 2026-08-13.

### Changed

- **A health warning is only pushed when it names something you can do.** The
  monitor still derives per-retailer health exactly as before and still publishes
  every state in full — `status.json`, `boty check` and the log are untouched —
  but a notification now costs a stated remedy. `Health` carries an `action`
  field which is **empty by default**, `monitor.assess_health` fills it on one
  arm only (a Walmart `store_id` that is unset or answering for a different
  store, whose remedy is a value in the daemon's `EnvironmentFile`), and
  `cli.watch_cycle` pages exactly the states that carry one.

  This is a positive rule rather than a list of exceptions, deliberately: a
  blocklist of known-useless alerts is stale the moment an arm is added, because
  the new arm is loud by default. Under this shape a health state written next
  year says nothing until somebody writes down what to do about it. Two mutations
  in `scripts/mutation_check.py` watch both directions of that — one rebuilds the
  loudness, one silences the single remaining remedy.

  Asked for by the maintainer on 2026-08-12, the second time he raised it: *"im
  still getting annoying messages. we need to never hit the user unless its
  something they can buy or actually do"*. The message that produced it fired at
  16:49:58 that day, about an Amazon control that did not read `IN_STOCK` — true,
  worth recording, and not something anybody can act on from a phone.

- **A refusal is never pushed, however entrenched.** `REFUSALS_BEFORE_PAGING` and
  `cli._refusal_is_entrenched` are deleted. They implemented a rule that a
  refusal outlasting the backoff deserves a human, and entrenchment turned out to
  measure only how sure we are of a fact nobody can act on — you cannot make a
  retailer answer at five refusals any more than at one. **The backoff itself is
  unchanged**: `pacing.Pacer` still counts refusals, stretches the interval and
  persists both, so the response the monitor can take by itself is intact.

  **What this overrules, said plainly:** the second and third clauses of REQ-16
  ("a refusal that outlasts the cap is pushed once"; "a detector producing a
  wrong verdict is pushed immediately"). Both states are now recorded and not
  pushed. The requirement's text is left as it stood at its milestone's close
  rather than edited under it; this entry is the record of the reversal.

- **The stuck-monitor warning still pushes, and now says why it is allowed to.**
  Three consecutive raising cycles means nothing is being checked and no restock
  can reach you, which is the one health state that is both actionable and worth
  the interruption — so it carries an explicit action rather than surviving by
  default.

- **The notification body renders the action** as the last line of each block,
  where there is one, through the same store-number redaction as the rest of the
  body. A state with nothing to ask for leaves the body's shape exactly as it
  was.

## [0.2.0] - 2026-08-10

**The number went DOWN, and that is the entry.** This release renumbers the
project from `1.0.0` to `0.2.0`. It is a correction, not a bump.

The `1.0.0` above was declared before this project had shipped, published or
bought anything — it was a plan to publish, written as though the publishing had
happened. That is the same overclaim this release corrects everywhere else, so
correcting it in the version number too is the only consistent thing to do.

Rolling a version *down* is normally reckless, because somebody may already be
pinned to the number you are taking away. Nobody is, and that was re-measured on
2026-08-10 rather than assumed: `git tag -l` reports **0 tags**,
`git ls-remote --tags origin` reports **0 refs** against a remote that answered,
and `https://pypi.org/pypi/bot-y/json` and `https://pypi.org/pypi/bot-y/1.0.0/json`
both return **HTTP 404**. No `1.0.0` of this package exists anywhere, so no
install can break. Nothing was tagged or uploaded by this release either.

### Added

- **The price ceiling measures the delivered total** where the retailer publishes
  a shipping cost readably: `max_price` compares `price + shipping` rather than
  the item price, and a resolvable total above the ceiling is still suppressed.
  GameStop is the worked case — $54.99 + $6.99 = $61.98, under 80. Watched going
  red by mutations in `scripts/mutation_check.py`.
- **Where shipping cannot be resolved, the alert is sent anyway and says so.**
  The body carries two separate fields, the same shape either way —
  `price: $54.99   shipping: unknown` — and states no delivered total, because
  none was established. **This means a listing with large unread shipping can
  reach you**: a $54.99 item with $45 of shipping the retailer does not publish
  will page you, and you are not told the $45.

  This reverses the rule as first shipped, at the maintainer's direction on
  2026-08-11: *"where we don't know just send it. If the user gets there and it's
  50 dollar shipping that's disappointing but it's worse to feel like you 'missed
  out'."* The first implementation suppressed those alerts, which cost Nintendo —
  the only first-party GO Plus + listing here, at MSRP — and Amazon. All four
  watches carrying a ceiling can page again. The requirement that asked for
  suppression is recorded unedited beside the reversal in `.planning/`, rather
  than reworded to match what shipped.
- **The README support matrix's Rung cell is bound to the code.** Both joins —
  retailer to adapter out of the command-line dispatcher, adapter to rung out of
  `boty/retailers.py`, read statically rather than by running anything — with
  nine red-watches and two mutations. It was previously bound to nothing:
  mutating the Amazon adapter to claim a browser transport, directly contradicting
  the shipped `| Amazon | 1 | dom |` row, left the suite at **exit 0, 687 passed**.
- **Workflow files are gated by directory, not by name.** Every file under the
  continuous-integration workflow directory is covered by the action-pin,
  exit-code, timeout and runner rules, so a second workflow added tomorrow cannot
  escape them by not being the one file a rule was written against.
- **`CHANGELOG.md` is gated on its contents.** Eight rules over this document —
  leaked agent markup, heading shape and real calendar dates, unreplaced
  placeholders, end-of-file shape, required headings, empty release sections,
  stale path citations, line-numbered citations. Every prohibition is paired with
  a presence rule, because "no markup and no placeholders" is satisfied by an
  empty file. Watched red on the byte-exact document that shipped with two lines
  of leaked tool-call markup for the whole of the previous release: with no
  contents rule in the tree it passed at **exit 0, 711 passed**; with the gate it
  fails naming the file and both lines.
- **The version number is bound in four places.** `pyproject.toml` is the
  referent; `README.md`'s publication instruction, this file's top released
  heading and the project's own milestone record are each checked against it, in
  both directions, with a deleted statement reported as a finding rather than as
  agreement. Two mutations prove it bites where the mutation harness runs. Before
  this release nothing offline read any of the four, and two of them had already
  diverged.
- **Walmart readings are pinned to a store.** A Walmart price is a statement about
  one store, and this monitor was comparing readings from whichever store the site
  assigned. The store is now read from the same page node the offer comes from and
  published alongside the verdict; an unpinned or unexpected store returns UNKNOWN
  rather than a number. Found by measurement: the same URL and parser produced
  `OUT_OF_STOCK` at $3.17 and `IN_STOCK` at $2.42 minutes apart.
- **Backoff state survives a restart.** Refusal counts and the paging memory
  round-trip through a state file, so restarting the monitor no longer forgets
  that a retailer asked it to slow down. The next-due time is deliberately *not*
  persisted, so a restart still asks once at full rate.

### Changed

- **`Development Status` is now `4 - Beta`.** At `1.0.0` the classifier said
  Production/Stable; at `0.2.0` that would be the same asserted-versus-real
  disagreement pointed the other way. What refuses Production/Stable: nothing
  published, no tag, nobody but the maintainer has installed it. What refuses
  Alpha: this has run as a service against six live retailers publishing
  per-cycle status, and the offline gate has been the phase contract since the
  first phase. The classifier is bound to the version by a rule now, in both
  directions, so it cannot go stale at the next change.
- **Health warnings no longer guess at a cause they cannot know.** Four sentences
  that asserted a cause — including "the detector is probably broken" — were
  withdrawn and replaced with a partition that includes an explicit
  cause-unknown case, so the fix cannot be satisfied by deleting every
  explanation.

### Not in this release

- **None of this is running on the maintainer's daemon.** The deployed service
  still executes code from before all of it, because the restart was deferred.
  Every claim above is a claim about the tree, verified by `make verify-offline`,
  and not a claim about a running process.
- **`make verify` still fails live**, in three classes: two controls cannot run
  on that host for want of a browser binary, and one reads UNKNOWN because the
  offline gate runs in a shell with no store pinned — which is the store guard
  above working, not a defect. None of the three was caused by this release and
  none is fixed by it.
- **Still not published.** `pip install bot-y` resolves nothing, and this release
  does not change that. A release note claiming deployed behaviour would be the
  exact overclaim `0.2.0` exists to correct.

## [1.0.0] - 2026-08-05

The first release intended to be published. Everything below has been running as
a service on the maintainer's machine; what 1.0.0 adds is the part that makes it
usable by someone who is not the maintainer.

### Added

- **A stock reading that can say "I don't know".** `Availability` has three
  members, not two, and `UNKNOWN` is a first-class verdict rather than a
  fallback. The whole project exists because "I could not read this page" being
  reported as "out of stock" is a silent failure that looks exactly like a
  working monitor.
- **Six retailers, of which four can alert on the Pokémon GO Plus +.** GameStop,
  Walmart and Nintendo at rung 1 with structured extraction; Amazon at rung 1
  with DOM extraction; Best Buy at rung 3 with structured extraction; Target at
  rung 3 with DOM extraction. **Best Buy and Target are control-only** — Best Buy
  does not appear to stock the product and Target delisted it (TCIN `88714054`
  served HTTP 200 as late as 2025-05 and now 404s). That is a finding recorded
  as one, not a shortfall: a watch on either would have read UNKNOWN forever
  while making the retailer count look better.
- **Control products, and the reason they are mandatory.** Every retailer is
  configured with at least one evergreen, first-party, always-in-stock item. A
  control that stops reading `IN_STOCK` means the *detector* is broken, which is
  the failure mode a green test suite cannot see: fixtures keep passing forever
  after a retailer redesigns its site. `scripts/control_check.py` reports this
  with four outcomes rather than two — 0 pass, 3 SKIPPED (no connectivity), 4
  INCOMPLETE (some controls cannot run on this host) — because flattening
  "nothing was checked" into either a pass or a failure loses the only thing
  worth knowing.
- **An escalation ladder, stated per retailer rather than averaged away.** Rung 1
  impersonated HTTP, rung 2 a sanctioned API, rung 3 a real browser, rung 4
  "dropped, with the evidence written down". A second independent axis,
  `Extraction`, says whether a reading came from the retailer's own
  machine-readable feed (`structured`) or from presentation markup (`dom`).
  `[degraded]` fires on either. **Rung 3 is an optional extra:** `nodriver` is
  AGPL-3.0 against this project's MIT licence, so it lives behind
  `pip install 'bot-y[browser]'` and a default install pulls no browser stack.
- **Flipper defences that suppress the alert this project exists not to send.**
  A marketplace offer with no named seller is UNKNOWN, never a restock; a
  first-party-only mode and a per-watch price ceiling each suppress a reseller
  listing independently. Measured on Amazon: the only GO Plus + offer there is a
  **used** unit at **$219** from a third-party seller against a $54.99 MSRP, and
  both defences suppress it.
- **Per-retailer pacing with exponential backoff.** `interval_seconds` is per
  pass, so a naive configuration multiplies into far more daily requests than it
  looks like. Backoff is capped, resets on a good read, and a refusal no longer
  pages as "the detector is probably broken" — which it is not.
- **An identity guard over every tracked file.** `scripts/identity_check.py`
  scans the whole tree, not just `tests/fixtures/`, for host identity: IP
  addresses, coordinates, tokens, postcodes. It runs at commit time through the
  tracked `hooks/pre-commit` (installed with `make hooks`), inside `make verify`,
  and from the test suite, which watches the rule fail per class and per
  carrier. It exists because this repository leaked real values into public
  history through a file nobody was scanning.
- **`make verify` as the contract.** One command, one exit code, and every phase
  of this project states its success criteria in terms of it. As of this release
  the stages are `identity`, `lint`, `test`, `types`, `fixtures`, `controls`,
  `mutation`, in that order. `make verify-offline` is the same minus the live
  retailer requests.
- **A mutation check, because a green suite is not evidence it detects
  anything.** `scripts/mutation_check.py` corrupts eight specific things in a
  throwaway copy of the package — the buyable check, UNKNOWN collapsing into
  out-of-stock, the seller filter, the price ceiling, the restock edge detector,
  the degraded flag, the DOM availability decision — and requires the suite to
  go red for each. A survivor names a hole that could ship green.
- **An `MIT` `LICENSE` file.** The licence had been a metadata string and a README
  heading for three phases with no text behind it; `tests/test_packaging_metadata.py`
  now fails when the declaration and the file disagree in either direction,
  because the build does not — setuptools emits `License-Expression` and silently
  drops `License-File` when the target is missing.
- **Contributor documentation.** `CONTRIBUTING.md` and
  `docs/adding-a-retailer.md` walk a real adapter end to end using Nintendo,
  whose whole lesson is that the default answer is *no adapter code at all*, and
  state why a control product is mandatory. `tests/test_contributor_docs.py`
  checks that every cited path exists and every pinned symbol occurs in both the
  doc and the file it names.
- **A linter.** `ruff` over `boty/`, `scripts/` and `tests/`, with the rule
  selection committed in `pyproject.toml` so a bare `ruff check` judges the same
  files for everyone, and a `lint` stage inside `make verify`.
- **Continuous integration on every pull request.** `.github/workflows/ci.yml`
  runs `make verify-offline` — one job, one step, so there stays one definition
  of the check order and one of the verdict. Least privilege (`contents: read`),
  every action pinned to a commit SHA, no caching.
- **Packaging metadata that a release check can read.** PEP 639 licence
  expression, a pruned sdist that ships no captured retailer HTML, and
  `scripts/release_check.py` (`make release-check`), which builds both artefacts
  in an isolated venv, runs `twine check`, installs the wheel into a second venv
  holding nothing else, and runs the console script from outside the repository.

### Fixed

- **`boty check` on a fresh install no longer raises `FileNotFoundError`.**
  `-c/--config` defaults to the repo-relative `config/products.yaml`, and
  `config/` is deliberately not packaged, so the first command the README
  teaches died with a stack trace naming a directory that only exists inside a
  git checkout. It now prints what it looked for, why no default config ships,
  and where to get one, and exits 2 — the same code as the two neighbouring
  "you have not configured this yet" refusals. Found by installing a wheel into
  a clean venv; `make verify` could never have seen it, because it runs from the
  repo root where that path resolves.
- **Best Buy's JavaScript-escaped JSON-LD is now read.** Best Buy began serving
  its schema.org blocks with `\'` inside strings and literal `\n` outside them,
  so `json.loads` refused all three and the control read UNKNOWN with a detail
  naming the wrong cause. Parsing is strict first and only then offers an
  already-failed block to a string-state-aware repair; a repaired read publishes
  as `ld+json (repaired)` so it cannot look ordinary.
- **Target's UNKNOWN was a render race of our own making.** The markup carrying
  the add-to-cart control arrives between 1 s and 3 s — measured absent at
  `settle=1.0`, present at 3.0 and 6.0 — against a default of exactly 3.0.
  `check_target_browser` now re-renders once at 10 s before concluding.
- **Amazon's captcha interstitial is no longer saved as a fixture.** It returned
  HTTP 200 and matched no block phrase, so a bot wall was written to disk under
  a product's name. The phrase was added and the file deleted; the obvious
  phrase was rejected because it also appears in real product pages.
- **Fixtures are redacted by class, not by value.** A by-value guard passed a
  Target capture carrying a session token, a visitor id, this host's
  geolocation and five nearby store addresses. Every `<script>` body is now
  emptied, and widening the guard found the same leak class already committed in
  four Walmart and Best Buy fixtures.

### Changed

- **`Result.degraded` fires on a browser transport *or* a DOM extraction.** It
  was derived from the rung alone, so a rung-1 DOM adapter — the most fragile
  thing this codebase could acquire — would have shipped looking fully
  trustworthy. Amazon is exactly that adapter.
- **Health warnings distinguish a refusal from a broken detector.** Reporting
  every failing control as "the detector is probably broken" sent 20 pages in 24
  hours for what was a retailer refusing us on cadence.
- **`requires-python` floor executed rather than declared.** `>=3.10` had been a
  claim verified against nothing; the full check now runs on 3.10 in CI.

### Not in this release

- **This is the first published release.** Before it, `bot-y` existed only as a
  git repository.
- **The `boty` name on PyPI is not this project.** `bot-y` — with the hyphen — is
  what `pip` needs. See the README's install section: the neighbouring name
  belongs to an unrelated package last released in 2012 and cannot be claimed.
