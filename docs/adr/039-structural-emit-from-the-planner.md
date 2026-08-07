# ADR-039: The planner emits cadence and dependencies structurally

## Status

Accepted

## Date

2026-08-07

## Context

`org_planner` read schedule detail the brief stated and had nowhere structural to put it. A stated
weekday survived only if the model happened to use the weekday-list form; a stated day-of-month
could not be represented at all, and an unrecognised cadence string fell through to the weekly
fallback — so `"monthly on the 5th"` emitted a weekly-Monday routine. A declared dependency had no
field either, so the producer/consumer ordering check inferred it from objective prose and returned
zero findings on a real bundle containing the inversion it was written for.

## Decision

### 1. Structured cadence replaces the token by coercion, rather than sitting beside it

`Cadence` carries frequency plus optional `days_of_week`, `day_of_month` and `months`. A legacy
cadence string is coerced at the model boundary, so one representation reaches every consumer.

Structured fields *beside* the token would be two descriptions of one fact, able to disagree with
nothing to adjudicate. Coercion also keeps a single source of frequency: `day_pattern_for` and
`wakes_per_active_month` read the same object, so what is scheduled and what is budgeted cannot
diverge.

Coercion raises on an unrecognisable cadence rather than defaulting. The former fallback rewarded
discarding information — a planner that kept the stated day got a worse result than one that
dropped it. The raise lands at plan parse, so the failure costs two model calls, not a fan-out.

### 2. `depends_on` is generation-internal and emitted nowhere

The planner records which tasks consume which, because it creates them and knows. The ordering
check reads that instead of scanning prose; the textual match is deleted, not kept alongside.

It appears in no bundle artifact. A UI-imported company is database-backed and the platform has no
dependency primitive (ADR-022), so emitting the field would invent something the importer ignores.

## Consequences

### Positive

- A stated weekday, day-of-month and month list reach the emitted schedule.
- The ordering check fires on dependencies expressed without naming the producer.
- An unrepresentable cadence fails at planning, cheaply and loudly.

### Negative

- `org_planner` must populate the widened fields. No test can prove a model follows an
  instruction; `scripts/probe_cadence_fidelity.py` measures it in two calls. **Result, five runs:
  20/20** — every stated weekday, day-of-month, month list and dependency carried, every run. The
  field was the constraint. Measured on one small fixture that states its cadences plainly; it does
  not establish behaviour on loosely-phrased or buried schedule prose.
- Cadence strings that previously produced a routine now raise.

### Neutral

- Bundle shape is unchanged; plans carrying only the coarse token render byte-identically.

## Notes

Deleting the prose-matching path needed a positive assertion, not an absence of failures. A test
that a prose reference *without* a declaration produces no finding is the only one that fails when
a dormant textual fallback is reintroduced — verified by mutation: 64 tests passed, that one
failed.

## References

- ADR-038 (amended) — the finding, and the superseded conclusion this feature replaces
- ADR-022 — no dependency primitive to import into
- ADR-036 — the hazard classes this feature's testing guards against
- `specs/018-structural-emit/` — spec and contracts
- `specs/019-schedule-grammar/` — held; re-argue against this baseline
