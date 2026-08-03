# Phase 3: The Hard Two — Plan Outline

**Phase:** 03-the-hard-two
**Requirements:** REQ-07, REQ-08
**Granularity:** coarse → 3 plans, 3 waves, 3 tasks each

| Plan ID | Objective | Wave | Depends On | Requirements |
|---------|-----------|------|-----------|-------------|
| 03-01 | Amazon: read the Conditions of Use before touching the transport; build the unpaddable-count gate; settle Amazon's rung | 1 | none | REQ-07 |
| 03-02 | Target: read the Terms first, then walk the ladder politely; register it or record rung 4 with evidence | 2 | 03-01 | REQ-07 |
| 03-03 | Close the phase: publish and measure the pass duration (REQ-08), complete and gate the support matrix, prove it live under the service's own environment | 3 | 03-01, 03-02 | REQ-07, REQ-08 |

## Why three waves and not one

All three plans touch `docs/retailer-evidence.md` and `README.md`, and the two
retailer plans additionally touch `boty/retailers.py`, `config/products.yaml`
and `tests/test_retailers.py` **on the branch where their retailer lands**.
Same-wave plans must have zero `files_modified` overlap, so putting 03-01 and
03-02 in one wave would be a planning defect that the execute step would have
to force-serialize anyway. `.planning/ROADMAP.md` records that Phase 2 learned
this the hard way; `03-CONTEXT.md` restates it.

## One conditional plan

`03-04` does not exist yet and is created only on one branch: if Target lands at
**rung 3**, `03-02` stops after the evidence and the fixtures and splits the
registration work — `check_html_browser`, the `_make_checker` arm, a possible new
extractor, fixtures, conftest entries, six behaviour cases, config, README — into
`03-04-PLAN.md` at wave 3, moving `03-03` to wave 4. That branch is a plan's worth
of work and running it inside one task ships rushed work at the end of a context
window. Rung 1 or rung 2 registration is small and stays inside `03-02` task 3.

## Why Amazon is first

`.planning/ROADMAP.md` Phase 3: "Establish reachability cheaply *before*
investing in an adapter." `03-CONTEXT.md`: "Amazon's ToU is notoriously
explicit on this point. Read it first — if a retailer forbids this in writing,
that settles it and no amount of transport work is relevant." The likely honest
outcome of 03-01 is a written prohibition and zero requests to amazon.com,
which costs one plan-hour and tells 03-02 whether criterion 5 rests on Target
alone.

## The likely honest outcome of the phase

Both refused, both documented, criterion 5 unmet and recorded as unmet. Every
plan below is written so that outcome verifies as complete. Each retailer truth
is stated in the `X, or Y-with-evidence` form, and the count gate has a
machine-checkable honest-shortfall clause that cannot be cleared by editing
`config/products.yaml`.
