# Feature Specification: Routine scheduling defaults and collision detection

**Feature Branch**: `015-routine-schedule-collisions`

**Created**: 2026-08-05

**Status**: Draft

**Input**: User description: "Routine scheduling defaults and collision detection — replace the single hardcoded 09:00 default with a deterministic spread derived from a stable hash of the task slug, and add collision warnings for recurring tasks that share a trigger expression (plus a narrow dependency-aware variant)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Scheduled work does not all fire at once (Priority: P1)

An operator writes a brief stating eight cadences — some daily, some weekly on a named day,
some monthly, some quarterly — without stating any clock times, because the brief format never
asked for them. The generated bundle currently schedules all eight at the same minute of the
day. The operator wants routines spread across the working day by default, so a bundle is
usable without hand-editing every schedule after import.

**Why this priority**: This is the defect the operator observed, it affects every bundle with
more than one routine, and it is the only story that changes generated output. The two
detection stories below add warnings; without this one they would fire constantly on every
bundle, describing a problem the generator itself created.

**Independent Test**: Generate a bundle from a brief with several cadences and confirm the
emitted trigger expressions differ in time-of-day while their days/frequencies are unchanged.
Delivers immediate value with no other story implemented.

**Acceptance Scenarios**:

1. **Given** a bundle whose recurring tasks state cadences but no clock times, **When** the
   bundle is generated, **Then** the routines are distributed across the available hours rather
   than sharing one hour.
2. **Given** the same brief generated twice, **When** the two bundles are compared, **Then**
   every trigger expression is byte-identical between runs.
3. **Given** a recurring task, **When** its cadence states a frequency or named days, **Then**
   the generated frequency and days are exactly what the cadence stated — only time-of-day is
   defaulted.
4. **Given** two bundles that differ only in a task's slug, **When** both are generated, **Then**
   the differing task may receive a different time-of-day, and unrelated tasks do not shift.

---

### User Story 2 - Simultaneous routines are surfaced (Priority: P2)

An operator reviewing a generated bundle wants to be told when two recurring tasks are
scheduled to fire at exactly the same moment, regardless of which agent owns them, so that
self-inflicted contention on a shared subscription is visible before import rather than
discovered in production.

**Why this priority**: This is the durable safeguard. Story 1 fixes today's defaulting; this
catches the next collision whatever its cause — a stated time, a cadence coincidence, or a
future change to the spreading rule.

**Independent Test**: Construct a bundle with two recurring tasks that resolve to the same
trigger expression and confirm a warning names both. Testable without Story 1.

**Acceptance Scenarios**:

1. **Given** two recurring tasks with the same trigger expression and different assignees,
   **When** the bundle is rendered, **Then** a warning names both tasks and their shared trigger.
2. **Given** two recurring tasks with different trigger expressions, **When** the bundle is
   rendered, **Then** no collision warning is emitted for them.
3. **Given** a colliding pair, **When** the bundle is validated, **Then** the bundle still
   renders and validates successfully — the finding is advisory, never an error.
4. **Given** two recurring tasks with the same trigger AND the same assignee, **When** the
   bundle is rendered, **Then** the existing split-activity warning and this collision warning
   are both emitted, each describing its own concern without replacing the other.

---

### User Story 3 - Consumer-before-producer scheduling is called out (Priority: P3)

An operator wants a stronger warning when one task appears to consume another's output but is
not scheduled to run after it — a recap scheduled at the same minute as the scan it summarises,
or, once routines are distributed across the day, a recap scheduled hours *earlier* than that
scan. Either way the recap reports on stale work every time it runs, and never errors.

**Why this priority**: The highest-value finding when it fires, but deliberately narrow. It
depends on one task referring to another by name, so it will miss dependencies expressed
without naming the upstream task. Shipped last because Story 2 already surfaces the simultaneous
case; this one covers the ordering the distribution in Story 1 can introduce.

**Independent Test**: Construct two recurring tasks on one day-pattern where one names the other
in its objective and is scheduled no later than it, and confirm the emitted warning distinguishes
the ordering problem from a plain collision.

**Acceptance Scenarios**:

1. **Given** two recurring tasks on the same day-pattern where one task's objective names the
   other and both are scheduled at the same time, **When** the bundle is rendered, **Then** a
   warning identifies the apparent producer/consumer ordering problem.
2. **Given** two recurring tasks on the same day-pattern where one names the other and the
   referencing task is scheduled *earlier* in the day, **When** the bundle is rendered, **Then**
   the same ordering warning is emitted — distribution has not resolved the dependency, only
   changed its shape.
3. **Given** two recurring tasks on the same day-pattern where one names the other and the
   referencing task is scheduled strictly *later*, **When** the bundle is rendered, **Then** no
   ordering warning is emitted — the consumer follows its producer.
4. **Given** two recurring tasks sharing a trigger with no textual reference between them,
   **When** the bundle is rendered, **Then** only the plain collision warning is emitted.
5. **Given** two tasks where one names the other but they recur on different day-patterns,
   **When** the bundle is rendered, **Then** no ordering warning is emitted (FR-008b).

---

### Edge Cases

- A bundle with exactly one recurring task: no collisions are possible; exactly one trigger is
  emitted and no warning fires.
- A bundle with no recurring tasks at all (including the single-agent path): no routines, no
  warnings, unchanged output.
- More than two recurring tasks sharing one trigger: reported as a single finding naming all of
  them, not as one finding per pair.
- Two recurring tasks whose cadences differ but whose expressions coincide anyway (e.g. a
  weekly and a monthly cadence landing on the same expression): treated as a collision, because
  the operator-visible consequence is identical.
- A task whose name is a common word that appears incidentally in another task's objective: may
  produce a false dependency finding. Accepted — the check is advisory and precision is favoured
  over recall, but the matching must be word-boundary aware so unrelated substrings do not trip
  it.
- Cadences that cannot spread: a cadence pinning both the day and the moment leaves nothing to
  distribute; the collision warning is the remaining safeguard.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST distribute recurring tasks' time-of-day across a range of hours
  rather than assigning every routine the same hour.
- **FR-002**: The assigned time-of-day MUST be derived deterministically from the task's own
  stable identity, so that regenerating an unchanged brief produces byte-identical schedules.
- **FR-003**: Determinism MUST hold across separate program runs and machines, not merely
  within a single run.
- **FR-004**: The system MUST NOT alter how a cadence's frequency or named days are bound; only
  the previously-unstated time-of-day is affected.
- **FR-005**: The system MUST emit an advisory finding when two or more recurring tasks share an
  identical trigger expression, naming every task involved and the shared expression.
- **FR-006**: The shared-trigger finding MUST be independent of task ownership — it fires
  whether or not the colliding tasks share an assignee.
- **FR-007**: The existing same-cadence-same-assignee finding MUST continue to operate unchanged
  and independently; the two findings answer different questions and may both fire on one pair.
- **FR-008**: The system MUST emit a distinct, stronger advisory finding when two recurring tasks
  show a textual producer/consumer relationship — one task's name or identifier appearing in the
  other's objective — they recur on the same day-pattern, and the apparent consumer is scheduled
  **at or before** the apparent producer rather than after it.
- **FR-008a**: FR-008 MUST NOT be limited to tasks sharing an identical schedule. Firing
  simultaneously is one way for a consumer to fail to follow its producer; being scheduled
  earlier in the day is another, and the second becomes *more* likely once FR-001 distributes
  routines. A check keyed on schedule equality alone would fall silent precisely when
  distribution introduced the ordering problem.
- **FR-008b**: FR-008 MUST NOT fire for tasks on different day-patterns. There is no single
  well-defined "before" to compare across differing patterns, and inferring one would require
  expanding the schedules. Recall is deliberately sacrificed here to keep the finding
  trustworthy when it does fire.
- **FR-009**: Textual matching for FR-008 MUST be word-boundary aware, so an identifier that is
  a substring of an unrelated word does not trigger a finding.
- **FR-010**: All findings introduced here MUST be advisory and routed to the existing warning
  channel; none may fail validation or block bundle generation.
- **FR-011**: Findings MUST be emitted in a stable order so that repeated runs on one bundle
  produce identical output.
- **FR-012**: A bundle containing no recurring tasks MUST produce output identical to today's.

### Key Entities

- **Recurring task**: A task carrying a cadence. It owns the identity used to derive its
  time-of-day, the objective text scanned for producer/consumer references, and an assignee.
- **Trigger expression**: The schedule a routine fires on. Two recurring tasks whose expressions
  are equal fire simultaneously.
- **Advisory finding**: A human-readable message routed to the operator through the existing
  warning channel, never a validation failure.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a bundle with eight recurring tasks and no stated clock times, no more than
  two share any single time-of-day, where today all eight share one.
- **SC-002**: Regenerating an unchanged brief produces schedules identical to the previous run,
  in 100% of runs and across separate program invocations.
- **SC-003**: For every recurring task, the generated frequency and days match the brief's
  stated cadence exactly — 100% agreement, unchanged from today.
- **SC-004**: Any pair of recurring tasks sharing a trigger expression is reported to the
  operator before import, with zero such pairs going unreported.
- **SC-007**: For every pair where one recurring task names another on the same day-pattern, the
  operator is told whether the referencing task runs after the one it names — reported in 100%
  of such pairs where it does not, whether they collide or merely run out of order.
- **SC-005**: A bundle with no recurring tasks, and a bundle whose recurring tasks do not
  collide, produce zero new warnings.
- **SC-006**: Bundle generation continues to succeed for every input that succeeds today; no
  finding introduced here converts a passing bundle into a failing one.

## Assumptions

- The brief format does not collect clock times for cadences, and this feature does not add
  such a field. Should a brief ever state a time, honouring it would be a separate change; this
  feature governs only the unstated case.
- Spreading across ordinary working hours is preferable to spreading across all 24, so that
  scheduled work stays within a window an operator would plausibly supervise. The exact window
  is a policy default, documented and adjustable, not a correctness property.
- Distributing by hour is sufficient granularity for the observed problem; finer distribution
  is available if hour-level spreading proves insufficient for a bundle with many routines on
  one cadence.
- The existing timezone default is out of scope and unchanged; this feature does not introduce
  timezone selection.
- The trigger expression's own format and validity remain provisional pending live-import
  confirmation, as they are today. This feature changes which expression is emitted, not the
  contract for what an expression is.
- Both detection stories operate on the generated bundle's own content, using the same advisory
  channel as the existing coherence checks — no new reporting surface.
