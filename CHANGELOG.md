# Changelog

What changed in each release, and what each change was measured against.

It exists because a version number is a claim and nothing else in a published
artefact explains it. `pip install bot-y` hands someone a monitor whose whole
argument is that it refuses to report a stock verdict it cannot back — so a
release note that says "improved reliability" would be the wrong register for
this project twice over. Every entry below names the thing that changed and,
where there is one, the measurement behind it. `pyproject.toml` states the
version; `scripts/release_check.py` binds this file's top heading to it, so the
two cannot drift.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Nothing yet.

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
</content>
</invoke>
