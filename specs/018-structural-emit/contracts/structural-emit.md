# Contract: Structural emit

Postconditions the test suite asserts, each citing the requirement it discharges.

## C1 — Cadence validity

- **C1.1** A cadence stating a frequency and a named weekday is accepted and retains the weekday.
  *(FR-001)*
- **C1.2** A cadence stating a day of the month is accepted and retains it, for any day 1–31.
  *(FR-001)*
- **C1.3** A cadence stating a day and a list of months is accepted and retains both. *(FR-001)*
- **C1.4** A weekday on a non-weekly frequency, or a day-of-month on a weekly one, is **rejected**
  before rendering, naming the inconsistency. *(FR-006)*
- **C1.5** An empty weekday or month list is rejected — a stated field must state a value. *(FR-006)*
- **C1.6** A day of the month above 28 is accepted and reported. *(spec Edge Cases)*
- **C1.7** A legacy bare-string cadence coerces to the equivalent structured form: `"weekly"`,
  `"tue"`, `"mon,wed,fri"`, `"monthly"`, `"quarterly"`. *(FR-017)*
- **C1.8** A string that parses to no recognisable cadence raises, and MUST NOT fall back to a
  default pattern. Today `"monthly on the 5th"` silently yields weekly-Monday; that behaviour must
  not survive. *(FR-007)*

## C2 — Cadence determines the day pattern

- **C2.1** A weekly cadence naming Tuesday emits a trigger firing on Tuesday. *(FR-003, SC-001)*
- **C2.2** A monthly cadence naming day 5 emits a trigger firing on day 5. *(FR-003, SC-002)*
- **C2.3** A quarterly cadence naming day 8 and four months emits that day in exactly those months.
  *(FR-003)*
- **C2.4** A cadence stating no day emits the identical day pattern it emits today. *(FR-004)*
- **C2.5** Time of day is unchanged — still derived from the task slug, unaffected by any cadence
  part. *(FR-005)*
- **C2.6** Rendering the same plan twice yields byte-identical triggers. *(SC-008)*

## C3 — Dependencies drive the ordering check

- **C3.1** A task recording a dependency, scheduled at or before it on intersecting schedules,
  produces the ordering finding naming both. *(FR-010, SC-003)*
- **C3.2** The finding fires when the consumer's objective **never mentions** the producer — prose is
  no longer the signal. *(FR-011, SC-004)*
- **C3.3** A consumer that names a producer in prose but records no dependency produces **no**
  finding. The textual match is replaced, not supplemented. *(FR-011)*
- **C3.4** A consumer scheduled strictly after its producer produces no finding. *(FR-010)*
- **C3.5** A dependency naming a non-existent task produces an advisory finding. *(FR-012)*
- **C3.6** A dependency cycle is reported once and terminates. *(FR-013)*
- **C3.7** A dependency on a non-recurring task produces no ordering finding. *(spec Edge Cases)*

## C4 — Intersection, not equality

- **C4.1** A daily consumer of a weekly producer at an earlier time produces the ordering finding —
  their firing moments intersect on the producer's day despite differing day patterns. *(FR-014)*
- **C4.2** Two schedules that cannot share a firing day produce no ordering finding. *(FR-015)*
- **C4.3** A quarterly and a monthly schedule are compared only where their months overlap.
  *(FR-014)*

## C5 — Coherence and no regression

- **C5.1** For every task, the frequency used for budget weighting derives from the same `Cadence`
  the schedule derives from — one source, not two agreeing implementations. *(FR-016, SC-007)*
- **C5.2** A plan whose cadences state no day and whose tasks record no dependency renders
  **byte-identically** to the pre-feature baseline. *(FR-018, SC-005)*
- **C5.3** A legacy plan carrying bare-string cadences renders identically to today. *(FR-017)*
- **C5.4** `depends_on` appears in no emitted artifact — not in `TASK.md`, not in `.paperclip.yaml`.
  *(data-model; Constitution II)*
- **C5.5** All findings introduced here reach the operator through the existing warning channel and
  none fails validation, except the plan-validation rejections in C1.4/C1.5/C1.8. *(FR-019)*

## C6 — Probe (decision artifact, not a suite test)

- **C6.1** The probe completes without rendering a bundle or fanning out per-agent content.
  *(plan D5)*
- **C6.2** The probe reports, per run and across runs, whether the stated weekday, day-of-month,
  day-and-months and dependency were emitted. *(plan D5)*
- **C6.3** The probe is not part of the default test run and makes no model call unless invoked
  explicitly. *(Constitution — no live calls in the suite)*
