# Publishing bot-y 1.0.0 — the four things only Dan can do

> ## SUPERSEDED 2026-08-25 — READ THIS FIRST, THEN THE CARD
>
> **Steps 1 and 3 of this card have happened, for a different version. Step 2 and step 4
> have not, and are no longer wanted.** Nothing below is edited: every value in it was read
> out of the tree on 2026-08-05 and was accurate then. This banner says which parts events
> have overtaken, so the card is not followed as if it were current.
>
> | This card's step | What actually happened |
> |---|---|
> | 1. `git push -u origin main` | **Done 2026-08-06**, by the orchestrator agent rather than by Dan, recorded in Phase 4's outcome table |
> | 2. Claim the PyPI name / configure the trusted publisher | **NOT done, and now deliberately not wanted.** Dan, 2026-08-25: *"forget the pypi part, just get it to github"* |
> | 3. Push the tag | **Done 2026-08-25 — as `v0.3.0`, NOT `v1.0.0`.** *"shipping is fine … just not a 1.0 release"* |
> | 4. Confirm what came out of PyPI | **Not applicable** — nothing was uploaded, and `pypi.org/pypi/bot-y/json` is still 404 |
>
> **Three facts in the table below are stale and one is now dangerous to act on.** The
> version is `0.3.0`, not `1.0.0`; the tag is `v0.3.0`; `main` has had an upstream since
> 2026-08-06 so the unpushed-commit count is long gone. The dangerous one is the *tag
> trigger* row: it is still true that `v*` starts `release.yml`, but since 2026-08-25 the
> publish job is gated on `if: vars.PUBLISH_TO_PYPI == 'true'` (M41) and that variable is
> unset — **so a tag no longer publishes, and following step 3 expecting an upload will
> produce a build and nothing else.** That is the intended behaviour, not a fault.
>
> **What is still exactly right here and worth keeping:** the `git tag -a`-not-`-s`
> reasoning (no signing key on this machine, and the tag is authenticated by the push), the
> environment-name coupling to PyPI's form, and the argument for why `make release-check`
> cannot prove PyPI serves the bytes. If publishing is ever taken up again, steps 2 and 4
> are still the right steps.

The ordered card for the one part of Phase 4 no agent here may perform: pushing
`main`, claiming the PyPI name, pushing the tag, and confirming what came out.

It exists because everything else in this phase could be measured locally and
this cannot. `make release-check` builds both artefacts, installs the wheel into
a venv holding nothing else, and runs the console script from outside the
checkout — but it cannot prove that *PyPI serves those bytes*, because the
download does not exist until somebody with the account publishes it. So the
work stops here, deliberately, and this card carries everything needed to finish
it in one pass on a phone: every value below was read out of the tree at
execution time on **2026-08-05**, not copied out of a plan.

---

## Where the tree stands right now

| Fact | Value | Read from |
|---|---|---|
| `make release-check` on this exact commit | `release check: PASSED — 10/10 checks, sdist and wheel proven` (exit 0) | run at execution time |
| Distribution name | `bot-y` | `pyproject.toml` § `[project] name` |
| Version | `1.0.0` | `pyproject.toml` § `[project] version` |
| Tag to create | `v1.0.0` | `v` + the version above |
| Owner / repository | `danieljamesjohnson` / `bot-y` | `git remote get-url origin` |
| Workflow filename | `release.yml` | basename of `.github/workflows/release.yml` |
| **Environment name** | **`pypi`** | the `environment:` key on the `publish` job of `release.yml` |
| Tag trigger | `tags: ["v*"]` — `v1.0.0` matches, evaluated with `fnmatch`, not eyeballed | `release.yml` § `on.push.tags` |
| `bot-y` on PyPI | **HTTP 404** — unclaimed, so the *pending* publisher form applies | `https://pypi.org/pypi/bot-y/json` |
| Unpushed commits on `main` | **43**, and `main` has **no upstream configured** | `git rev-list --left-right --count origin/main...HEAD` |
| `origin/main` currently points at | `b0a272f` | `git rev-parse origin/main` |
| Local `v*` tags | **none** — this plan created none, and neither did 04-05 | `git tag -l 'v*'` |
| Working tree | clean | `git status --porcelain` |
| Git signing key configured | **no** (`user.signingkey`, `gpg.format`, `commit.gpgsign` all unset) | `git config --get` |

Because there is no signing key on this machine the card below uses **`git tag -a`**
(annotated, unsigned) rather than `git tag -s`. That is not a gap being waved
past: the tag is authenticated by the push, since GitHub authenticates whoever
pushes it, so an unsigned annotated tag does not widen the set of people who can
publish here. That set is already "anyone who can push a `v*` tag", which is
exactly what Trusted Publishing grants. Setting up signing is worth doing and is
not this phase's work.

## What step 2 actually grants

After the trusted publisher exists, **anyone who can push a `v*` tag to this
repository can publish under the name `bot-y`, with no secret involved.** That is
Trusted Publishing working as designed rather than a defect, and it is the thing
being authorised.

Who that is today, read live: `gh api repos/danieljamesjohnson/bot-y/collaborators --jq '.[].login'`
returns exactly one login — `danieljamesjohnson`. The same GET reports the repo
`public`, default branch `main`, and `license: null` — the last of which should
flip to "MIT license" in the sidebar once step 1 pushes 04-02's `LICENSE` file.

---

## 1. Push `main` first

    git push -u origin main

43 commits. The `-u` is there because `main` has no upstream configured yet — a
leftover from the earlier history rewrite. After this once, plain
`git push origin main` works.

**Why first:** pushing only a tag uploads the objects but leaves the
repository's default branch pointing at code older than the release, so GitHub
would display a v1.0.0 that is nowhere on `main`.

**Worked when:** GitHub shows the new tip, and the Actions tab shows a run of
the CI workflow — **the first live run this repository has ever had** —
finishing green. Note it appears under the workflow's *display name*, **`verify`**,
not under the filename `ci.yml`. Its last step runs `make verify-offline` and its
log should end with:

    VERIFY: PASS (OFFLINE — live controls were NOT run, so nothing here says the retailers still work)

Wait: roughly 2–4 minutes.

## 2. Configure the PyPI trusted publisher — the PENDING form

Go to **<https://pypi.org/manage/account/publishing/>** (account settings →
Publishing) and add a **pending** publisher on the **GitHub** tab. It has to be
the pending form and not a project's own publishing page, because the project
does not exist on PyPI yet — measured at execution time, `bot-y` returns HTTP 404.

| Field | Value |
|---|---|
| PyPI Project Name | `bot-y` |
| Owner | `danieljamesjohnson` |
| Repository name | `bot-y` |
| Workflow name | `release.yml` |
| **Environment name** | **`pypi`** |

**The environment name must match the workflow's `environment:` value exactly,
character for character.** If it does not, the failure does not say "wrong
environment" — it fails at the OIDC exchange as an *invalid or unknown
publisher*, which reads like a problem with the project name or with the token.
This is the single most likely thing to go wrong here.

Field *labels* on that form may have shifted since this was written. The values
are what matter, and they are above.

Wait: instant.

## 3. Create and push the tag

**No tag exists yet** — 04-05 deliberately created none and neither did this
plan — so the first command creates it as well as the second pushing it.

    git tag -a v1.0.0 -m "bot-y 1.0.0 — first published release"
    git push origin v1.0.0

The tag push is the trigger. Nothing else starts the publish.

**Worked when:** the Actions tab shows a run of the publish workflow — display
name **`publish`**, file `release.yml` — with two jobs, `build` then `publish`,
and the second showing the `pypi` environment.

Wait: roughly 2–3 minutes.

## 4. Watch it, and confirm

    gh run watch

or open **<https://github.com/danieljamesjohnson/bot-y/actions>**.

**Worked when:** **<https://pypi.org/project/bot-y/1.0.0/>** exists and shows
version 1.0.0 and MIT.

## 5. OPTIONAL — one throwaway pull request

Any one-line change on a branch, opened as a PR against `main`, is the only way
to *observe* CI's pull-request trigger actually running. It is the one half of
criterion 2 that no offline gate and no `push: main` run can reach. Skipping it
costs a footnote in the verdict and nothing else.

---

## If it fails

Four signatures, and the difference between them matters more than any one of
them.

- **"invalid publisher" / "unknown publisher" at the OIDC step** — the PyPI form
  and the workflow disagree on one of owner, repository, workflow filename or
  environment. **Nothing was published.** Fix the form, then use **Re-run failed
  jobs** in the Actions UI. Do not delete the tag and do not make a new one.

- **A missing or protected deployment environment** — create it at repository
  **Settings → Environments → New environment**, named exactly `pypi`, then
  re-run the failed job.

- **The `build` job fails before `publish` runs** — **nothing was published**, so
  the tag can be moved:

      git tag -d v1.0.0
      git push origin :refs/tags/v1.0.0

  fix it on `main`, and tag again.

- **`File already exists`** — this one is **not recoverable**. The version was
  published, and PyPI never allows re-uploading a filename, even after the
  release is deleted. A bad 1.0.0 is fixed by yanking it on PyPI and releasing
  1.0.1. Never by deleting and re-pushing the tag.

## What NOT to do

**There is no `PYPI_API_TOKEN` in this design and no repository secret to add.**
Nothing to mint, nothing to paste, nothing to store, nothing to rotate later —
the publish authenticates by OIDC from the tag push and by nothing else. Any
instruction that asks you to paste a token into repository secrets, or to run an
upload command by hand from a laptop, is from a different setup and is wrong for
this repository.

## If you decline, or defer

**Nothing breaks.** Waves 1–5 are complete and independent of this: the tree
builds, installs, lints, type-checks, tests and has CI, and it simply has not
been published. Publishing later needs nothing that is not already written down
on this card, which stays on disk.

Phase 4 criteria **3** (`pip install bot-y` works from PyPI) and **5** (a tagged
v1.0.0 release exists) are then recorded **UNMET with your reason quoted
verbatim** — which is exactly how Phase 3.1 closed its criterion 1, after the
rewrite that would have made it meetable was proposed and declined. That is an
outcome, not a failure, and the phase closes honestly on it.

---

*Written by 04-06 Task 1 on 2026-08-05, from the shipped tree. Where this card
and any plan disagree, this card was generated from the files and wins.*
