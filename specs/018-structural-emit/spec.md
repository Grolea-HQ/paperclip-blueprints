# Feature Specification: Structural emit — org_planner writes what it already decided

**Feature Branch**: `018-structural-emit`

**Created**: 2026-08-06

**Status**: Draft

**Input**: User description: "org_planner reads the brief's stated schedule and dependencies and then discards them, because the fields it must write into cannot hold them. Widen the task stub to carry a structured cadence (frequency, day-of-week, day-of-month, months) and an explicit dependency list, so the planner emits structurally what it already decided instead of leaving it in prose that nothing reads."

## Context

A brief states its schedule in prose that `org_planner` reads: a weekly scan on **Tuesday**, quarterly
reviews on the **5th** and the **8th**, and three routines that consume another's output and must
follow it. The generated bundle put the scan on **Monday**, both quarterlies on the **1st**, and
scheduled the consumer an hour **before** its producer.

The planner is not misreading the brief. It is writing into fields that cannot hold what it read:

| What the brief states | Field available | Outcome |
|---|---|---|
| Weekly, on Tuesday | `recurrence: str` — accepts `tue` | Representable; the **prompt** steers to `weekly` → Monday |
| Monthly, on the 5th | `recurrence: str` | **No form exists.** Any attempt falls through to the default pattern — `* * 1`, weekly Monday |
| B consumes A's output | none | Survives only in objective prose |

Row 2 is the sharpest: an unrecognised cadence does not degrade to a monthly-on-the-1st, it degrades
to a *weekly Monday* routine. The field punishes a faithful reading — the planner gets a better
result by discarding the day than by trying to keep it.

Row 3 is the same shape one level over. The planner decides the dependency when it creates the
tasks, has nowhere to record it, and the downstream ordering check is left inferring dependencies by
looking for one task's identifier inside another's objective prose. On the reference bundle that
check produces **zero** findings while a real inversion is present, because the objective describes
the dependency without naming the producer. Injecting the identifier makes it fire immediately.

This feature is one mechanism applied twice: **emit structurally what the planner already decided.**

**Relationship to the deferred schedule grammar.** A brief-side schedule grammar (held as 019) would
make these values operator-stated and deterministic rather than model-mediated. It is a larger
change — brief format, grammar, task-identity channel, operator materials — and it must be argued
against the baseline *this* feature establishes, not against today's. Nothing here forecloses it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A stated day survives into the schedule (Priority: P1)

An operator whose brief says a scan runs weekly on Tuesdays, and a review on the 5th of each quarter
month, gets routines on Tuesday and on the 5th.

**Why this priority**: Two-thirds of the observed defect, and the part nothing else addresses.

**Independent test**: Plan against a brief stating a named weekday and a day-of-month; confirm the
emitted triggers carry that weekday and that day.

**Acceptance Scenarios**:

1. **Given** a brief stating a weekly cadence on a named weekday, **When** the bundle is generated,
   **Then** the routine fires on that weekday.
2. **Given** a brief stating a monthly cadence on a stated day of the month, **When** the bundle is
   generated, **Then** the routine fires on that day — including days other than the 1st.
3. **Given** a brief stating a quarterly cadence on a stated day and stated months, **When** the
   bundle is generated, **Then** the routine fires on that day in those months.
4. **Given** a cadence with no stated day, **When** the bundle is generated, **Then** the day pattern
   is exactly what it is today, and the derived time-of-day is unchanged.
5. **Given** a structured cadence, **When** the same plan is rendered twice, **Then** the emitted
   trigger is byte-identical.

---

### User Story 2 - A dependency the planner knows about is recorded (Priority: P1)

The ordering check stops inferring dependencies from prose and reads them from the plan.

**Why this priority**: Equal to US1. The check exists, is well-designed, and produces nothing on a
real bundle containing the exact defect it was written for. A correct check wired to an unreliable
signal is indistinguishable from no check.

**Independent test**: Plan a consumer that depends on a producer without naming it in prose; confirm
the ordering finding fires when the consumer is scheduled at or before the producer.

**Acceptance Scenarios**:

1. **Given** a task recorded as depending on another, scheduled at or before it on an intersecting
   schedule, **When** the bundle is rendered, **Then** the ordering finding names both.
2. **Given** the same pair where the consumer's objective never mentions the producer, **When** the
   bundle is rendered, **Then** the finding still fires — prose is no longer the signal.
3. **Given** a consumer scheduled strictly after its producer, **When** the bundle is rendered,
   **Then** no finding is emitted.
4. **Given** a plan recording no dependencies, **When** the bundle is rendered, **Then** no ordering
   findings are emitted and nothing else changes.

---

### User Story 3 - A plan that cannot be honoured is visible (Priority: P2)

Where the planner emits something the schedule cannot express or that does not resolve, the operator
is told before import.

**Why this priority**: The failures being prevented are silent by construction — a discarded day
produces a plausible schedule, and a dangling dependency produces none.

**Acceptance Scenarios**:

1. **Given** a structured cadence whose parts are inconsistent (a day-of-month on a weekly
   frequency), **When** the plan is validated, **Then** it is rejected before rendering.
2. **Given** a recorded dependency naming a task that does not exist, **When** the bundle is
   rendered, **Then** an advisory finding names it.
3. **Given** a recorded dependency between tasks whose schedules cannot intersect, **When** the
   bundle is rendered, **Then** no ordering finding is emitted — there is no well-defined "before".

---

### Edge Cases

- **A cadence with a day-of-month greater than 28**: accepted but reported, since it will not fire in
  every month.
- **A dependency cycle** (A depends on B, B on A): reported once, naming the cycle; never a crash and
  never an infinite loop.
- **A task depending on a non-recurring task**: no ordering finding — a non-recurring task has no
  trigger to be "before".
- **A daily consumer of a weekly producer**: their firing moments intersect on the producer's day, so
  ordering is compared there rather than skipped.
- **A plan from before this feature**, carrying only the coarse cadence token: continues to work
  unchanged, producing today's day patterns.
- **Three copies of the reference bundle exist and they do not agree.** Anything reading one later —
  a coverage check, a regeneration, a future session — must know which it has:
  - `paperclip-bundles/productivity-radar` — **pristine generated output.** All eight crons verified
    to match `slot_for(slug)` exactly, so nothing here has been hand-edited. This is the copy to read
    when the question is "what did the generator produce".
  - `paperclip-blueprints-pro/examples/generated-companies/productivity-radar` — **hand-edited.**
  - The **deployed Paperclip company** — carries the operator's corrected schedules.

  The corrected schedules exist only in the deployment. Verifying against a corrected copy and
  concluding the loss was already fixed is the specific error this note prevents.

## Requirements *(mandatory)*

### Functional Requirements

**Structured cadence**

- **FR-001**: The task stub the planner emits MUST be able to carry a cadence as structured parts: a
  frequency, and optionally a day of the week, a day of the month, and a set of months.
- **FR-002**: The planner MUST be instructed to emit every schedule detail the brief states, rather
  than normalising it away. Where the brief names a day, the day MUST appear in the plan.
- **FR-003**: A structured cadence MUST determine the emitted day pattern in full.
- **FR-004**: A cadence with no stated day MUST produce exactly the day pattern it produces today.
- **FR-005**: The time of day MUST continue to come from the existing deterministic derivation. This
  feature adds no clock times.
- **FR-006**: An internally inconsistent cadence MUST be rejected before rendering, naming the
  inconsistency.
- **FR-007**: The system MUST NOT silently degrade an unrepresentable cadence. Today an unrecognised
  cadence becomes a weekly-Monday routine with no signal; that behaviour MUST NOT survive for
  structured input.

**Dependencies**

- **FR-008**: The task stub MUST be able to record which other tasks a task consumes the output of.
- **FR-009**: The planner MUST record a dependency it relied on when ordering work, rather than
  leaving it only in prose.
- **FR-010**: The producer/consumer ordering check MUST use the recorded dependencies as its signal.
- **FR-011**: The ordering check MUST NOT infer dependencies from objective prose. The textual match
  is replaced, not supplemented — two signals for one fact would disagree with no principled winner.
- **FR-012**: A recorded dependency naming a task that does not exist MUST produce an advisory
  finding.
- **FR-013**: A dependency cycle MUST be reported and MUST NOT cause a crash or non-termination.

**Ordering comparison**

- **FR-014**: Ordering MUST be compared wherever two schedules' firing moments can **intersect**, not
  only where their day patterns are identical. A daily consumer of a weekly producer is comparable on
  the producer's day.
- **FR-015**: Where two schedules cannot intersect, no ordering finding is emitted.

**Coherence and compatibility**

- **FR-016**: Budget wake-frequency weighting MUST derive from the same cadence the schedule derives
  from. There MUST remain exactly one source of truth for an activity's frequency.
- **FR-017**: A plan carrying only the coarse cadence token MUST continue to work unchanged.
- **FR-018**: A brief that states no day and no dependency MUST produce output identical to today's.
- **FR-019**: All findings introduced here MUST be advisory and routed to the existing warning
  channel, except the plan-validation rejections in FR-006, which occur before rendering.

### Key Entities

- **Structured cadence**: Frequency plus the optional day and month parts a brief may state. Replaces
  a coarse token that could not hold them.
- **Dependency record**: A task's declaration of which tasks it consumes. Written by the planner
  because the planner is what knows; read by the ordering check.
- **Ordering finding**: An advisory report that a consumer is scheduled at or before its producer on
  schedules that can intersect.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a brief stating a weekly cadence on a named weekday, the emitted routine fires on
  that weekday in 100% of cases — where today it falls on Monday.
- **SC-002**: For a brief stating a day of the month, the emitted routine fires on that day — where
  today no input can produce any day but the 1st.
- **SC-003**: For a bundle shaped like the reference one, the ordering check reports the
  consumer-before-producer inversion — where today it reports **zero** findings on that bundle.
- **SC-004**: Zero dependencies are missed because the consumer's objective does not name the
  producer.
- **SC-005**: For a brief stating no days and no dependencies, the generated bundle is byte-identical
  to its pre-feature output.
- **SC-006**: Zero cadences are silently degraded — every unrepresentable cadence is either rejected
  or reported.
- **SC-007**: For every activity, the frequency used for budgeting equals the frequency used for
  scheduling.
- **SC-008**: Regenerating an unchanged plan produces byte-identical triggers across separate runs.

## Non-Goals

The scope guard. If a task appears to need something below, the task is wrong.

- **No brief-format change.** No new section, no grammar, no operator-facing schedule syntax. That is
  019, and it must be argued against this feature's baseline.
- **No clock times.** Time of day stays derived. A structured cadence carries days, not hours.
- **No operator-stated dependencies.** The planner records what it decided; the operator does not
  re-declare it. Two channels for one fact can contradict each other.
- **No task-identity channel.** Task identifiers stay freely chosen by the planner.
- **No retry or repair** when the planner emits an inconsistent cadence — reject, name it, stop.
- **No change to the time-of-day spread**: window, granularity and derivation are untouched.
- **No change to the company timezone** (feature 017) beyond carrying it unchanged.
- **No repair of the existing biweekly cadence**, which is already lossy. Pre-existing, out of scope.
- **No dependency semantics beyond ordering** — no scheduling *from* dependencies, no automatic
  time adjustment, no blocking. The finding is advisory and the operator decides.

## Assumptions

- The planner reads the brief's stated schedule and discards it to satisfy the output contract.
  Widening the contract recovers the stated values only insofar as the planner then emits them; the
  probe (plan D5) is what establishes whether it does.
- Prompt steering matters as much as field width for the weekday case: the coarse form is listed
  first and the only weekday example is multi-day, which biases a single-day cadence toward the
  coarse token. The instruction is corrected alongside the field.
- The ordering check's design is sound and only its input signal is unreliable; replacing the signal
  makes it fire without other changes.
- Emitted trigger format already accommodates arbitrary days of the month and month lists, verified
  against the renderer. This feature changes which trigger is produced, not what a trigger is.
