# Contributing to bot-y

How to get a working checkout, what the checks mean, and what a pull request has
to carry.

It exists because the checks in this repository are unusual in one specific way:
they are designed to be *able* to fail, and they distinguish between "this is
broken" and "this could not be checked here". A contributor who has not been
told what `PASS (INCOMPLETE)` means will read a correct result as their own
breakage and go looking for a bug that is not there. Everything below is the
short version of that.

## Set up

```bash
git clone https://github.com/danieljamesjohnson/bot-y
cd bot-y
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'
```

That is the same path `README.md`'s Install section documents, and it is worth
using rather than a global install: every target in the `Makefile` looks for an
interpreter in the virtualenv and refuses to run without one, so a contributor
and CI end up checking the same thing.

The browser extra is separate and deliberately optional. It pulls `nodriver`,
which is AGPL-3.0 against this project's MIT, and someone working on the HTTP
retailers must never be forced to pull a browser stack to run the test suite.
Install it only if you want Best Buy or Target covered locally; the README's
"The browser rung" section has the details.

## Install the commit hook before your first commit

```bash
make hooks
```

This is first rather than a footnote, and the reason is the timing. The hook at
`hooks/pre-commit` is tracked, so you get it when you clone — but installing it
is opt-in on purpose, because writing into a git hook directory behind someone's
back is the kind of thing a build should ask for. Until you run that line there
is nothing between a fixture you captured from a retailer and a public
repository.

What it guards: `scripts/identity_check.py` is one rule with three callers — the
hook (staged files only, so it costs milliseconds), `make verify` (the whole
tree), and the test suite, which watches the rule fail per leak class and per
carrier. It scans **every tracked file**, not just the fixture tree, because the
leak that mattered most here was in a planning document. It exits **0** clean,
**1** on a leak and **2** on a usage error.

If it fires and you are certain it is a false positive: widen the rule in
`scripts/identity_check.py` and add a test case for the new shape. Do **not**
bypass with `--no-verify`, and do **not** add the value to an allow-list. Both
of those close the finding without changing what the guard knows, so the next
person hits it too.

## Run the checks

```bash
make verify-offline
```

That is the one to run. `make verify` is the same sequence plus **live requests
to six retailers**, which is the maintainer's to run and not part of a normal
pull-request loop — this project's politeness budget is a real constraint, and
the per-retailer pacing overrides in `config/products.yaml` exist because it was
once exceeded by accident.

A green run comes in three flavours, because "everything passed" and "we could
not check some of it" must not look the same. `README.md` carries the
authoritative verdict table; the short version:

- **`VERIFY: PASS`** — every check ran and passed.
- **`VERIFY: PASS (OFFLINE — ...)`** — no live control ran at all, so nothing in
  the run says the retailers still work. This is what `make verify-offline`
  prints, and it is the expected result of a contributor's loop.
- **`VERIFY: PASS (INCOMPLETE — ...)`** — some live controls could not run **on
  this host**. This is the ordinary result of a fresh clone without the browser
  extra and without Chrome. It is a gap in your machine, not a failure of your
  change, and nothing is known to be broken.

Anything else is `VERIFY: FAIL (<stage>)` and names the stage that failed.

## Adding a retailer

Start by assuming you will write no code, because on half the retailers here
that is the correct answer: three of the six stores bot-y watches have no
adapter at all — they fall through to the generic checker, which reads the
structured data their pages already publish. The most recent retailer added took
one allow-list line and two lines of YAML.

The full walkthrough — a real retailer end to end, why a control product is
mandatory, what makes a bad control, and the contract that an absence is never
reported as out-of-stock — is in
[docs/adding-a-retailer.md](docs/adding-a-retailer.md). Read it before you open
an editor; most of what it has to say is about what not to build.

## What a pull request has to carry

Each of these already has a gate behind it, so this is a list of things that
will be checked rather than things that would be nice:

- **An evidence-log section** in `docs/retailer-evidence.md` for any retailer
  you probed, with a verdict line in one of the three exact forms.
  `scripts/evidence_check.py` matches them character for character, and a
  REFUSED verdict has to rest on an observed measurement rather than prose.
- **A README support-matrix row** that passes `tests/test_support_matrix.py`.
  The row label must match the retailer's display value in
  `scripts/evidence_check.py` character for character, accent included, and the
  cell vocabularies are fixed. Fix the label; do not loosen the comparison.
- **Fixtures redacted by class, not by value**, and captured with the hook
  installed. Redact whole categories — every script body, every host marker —
  rather than the specific strings you happened to notice, and do not name the
  removed values in the redaction record.
- **`make verify-offline` exiting 0**, with the verdict line in the PR
  description.
- **No credentials anywhere in the diff.** The Best Buy API key and the
  notification URL are environment values by design; they must not appear in
  `config/products.yaml`, in a fixture, or in a test.

Contributions are accepted under the project's [MIT](LICENSE) licence.
