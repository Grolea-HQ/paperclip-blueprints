# Feature Specification: Company-level routine timezone

**Feature Branch**: `017-routine-timezone`

**Created**: 2026-08-06

**Status**: Draft

**Input**: User description: "Company-level routine timezone. The brief gains one company-level timezone field (an IANA zone name, e.g. Europe/Helsinki); it flows to every emitted routine's schedule trigger, replacing the hardcoded UTC. Default remains UTC when the brief states none. Scope is strictly the timezone: no change to task recurrence, no schedule grammar, no change to the time-of-day spread or to any collision check. An invalid or unknown zone name must be rejected before generation."

## Context

Feature 015 spread routine times across a 6–17 window, justified in its own source as the hours
during which an operator plausibly supervises work. That window is applied in the routine's
timezone, and the timezone is a hardcoded constant with no channel from the brief — so for an
operator in Europe/Helsinki the real window is 09:00–20:00 local, and a routine whose purpose is
a morning liveness heartbeat can land at 20:00 local. Feature 015 knew this and shipped it as a
documented limitation, and recorded the timezone default as explicitly out of its scope. This
feature discharges that deferral.

This is the narrow half of a larger finding. The brief also states clock times, days-of-month and
an intended ordering in prose that no field captures, and binding those requires a structured
schedule channel and a change to how a task's cadence is represented. That work is settled in
design and deliberately **not** in this feature (see Out of Scope).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Routines fire at the operator's local hours (Priority: P1)

An operator who works in Europe/Helsinki states their timezone in the brief. Every routine in the
generated bundle is scheduled in that zone, so a routine placed at hour 8 by the spread fires at
08:00 for the operator rather than 11:00. The window the spread targets means what its rationale
says it means.

**Why this priority**: It is the whole feature. Every other story is a boundary condition on it.

**Independent Test**: Generate a bundle from a brief stating a timezone and confirm every emitted
routine trigger carries that zone; confirm the day and time-of-day fields are unchanged from a
run of the same brief without the field.

**Acceptance Scenarios**:

1. **Given** a brief stating a valid timezone, **When** the bundle is generated, **Then** every
   routine's schedule trigger declares that timezone.
2. **Given** a brief stating a timezone, **When** the bundle is generated, **Then** each routine's
   day pattern and time-of-day are byte-identical to what the same brief produces without the
   field — only the declared zone differs.
3. **Given** a brief stating a timezone, **When** the same brief is generated twice, **Then** the
   emitted schedules are byte-identical between runs.
4. **Given** a bundle with several routines, **When** it is generated, **Then** all routines carry
   the same timezone — the value is a company-level property, not a per-routine one.

---

### User Story 2 - A brief that says nothing behaves exactly as today (Priority: P1)

An operator regenerating an existing brief that has no timezone stated gets the bundle they got
before this feature, unchanged.

**Why this priority**: Equal to Story 1. Every brief written to date omits the field, and this
feature must not alter a single one of them. A silent schedule shift on regeneration would be the
same class of defect this work exists to correct.

**Independent Test**: Generate a bundle from a brief with no timezone field and diff the emitted
schedule triggers against the pre-feature output — no difference.

**Acceptance Scenarios**:

1. **Given** a brief that omits the timezone field, **When** the bundle is generated, **Then**
   every routine declares the same default zone emitted before this feature.
2. **Given** a brief that omits the field, **When** the bundle is generated, **Then** the full
   generated output is identical to the pre-feature output for that brief.
3. **Given** a brief whose timezone field is present but left as the template's unfilled
   placeholder or blank, **When** the bundle is generated, **Then** it is treated as omitted, not
   as an invalid value.

---

### User Story 3 - A misspelled zone stops the run (Priority: P2)

An operator writes `Europe/Helsinky`. Generation fails before any content is produced, naming the
rejected value.

**Why this priority**: The failure this prevents is silent and expensive. Falling back to the
default on an unrecognised zone would schedule an entire company several hours from where the
operator intended, with no signal anywhere in the bundle — the operator asked for a zone and the
tool would quietly ignore them. There is no safe fallback, so rejection is the only correct
behaviour. It is a boundary condition rather than the feature itself, hence P2.

**Independent Test**: Supply a brief with an unrecognised zone name and confirm generation is
refused with a message naming the value, before any generation cost is incurred.

**Acceptance Scenarios**:

1. **Given** a brief stating a zone name the system does not recognise, **When** generation is
   attempted, **Then** it is refused with a message identifying the offending value.
2. **Given** such a brief, **When** generation is refused, **Then** no content-generation work has
   been performed and no bundle files have been written.
3. **Given** a brief stating a valid zone in different letter casing than the canonical spelling,
   **When** the bundle is generated, **Then** it is accepted and the canonical spelling is emitted.
4. **Given** a brief stating a fixed-offset value (e.g. `+03:00`) rather than a zone name, **When**
   generation is attempted, **Then** it is refused — the same as any other unrecognised value.
5. **Given** a brief stating a value the zone database recognises but which is not a
   Region/City name (e.g. a legacy abbreviation the database still carries), **When** the bundle is
   generated, **Then** it is accepted. The recognition set is the zone database, not a curated
   subset of it — see Assumptions.

---

### Edge Cases

- **A bundle with no recurring tasks** (including the single-agent path): no routines are emitted,
  so the field has no observable effect. The value is still validated, because an invalid value is
  an error in the brief regardless of whether it happens to be used.
- **A zone that observes daylight saving** (Europe/Helsinki): the routine's stated local time is
  what stays fixed across a DST transition; the corresponding absolute instant shifts by an hour.
  This is the intended behaviour and the reason a zone name is bound rather than a fixed offset.
- **A deprecated or alias zone name** the zone database still resolves: accepted. The system's
  recognition set is the zone database, not a curated list.
- **Case handling must not depend on the host machine.** On a case-insensitive filesystem, a
  lowercase zone name may resolve while on a case-sensitive one it does not — so a naive resolution
  order would canonicalise differently on the operator's machine than on another, and the same brief
  would emit different bundles on different hosts. Resolution MUST be host-independent (FR-013).
- **A zone whose local working hours differ from the spread window's assumption**: out of scope.
  The window remains a fixed policy default; this feature only makes the window mean local hours.
- **The validation command** (`validate`, which checks a brief without generating): must reject an
  invalid zone on the same terms as a generation run, so the error surfaces at the cheapest point.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The brief MUST provide one optional company-level timezone field, stated as an IANA
  zone name.
- **FR-002**: The field MUST be a single company-level value. It MUST NOT be expressible per
  routine, per agent, or per task.
- **FR-003**: Every emitted routine's schedule trigger MUST declare the brief's stated timezone.
- **FR-004**: When the brief states no timezone, the system MUST emit the same default zone it
  emits today, and the generated output MUST be otherwise identical to today's for that brief.
- **FR-005**: A stated value that is blank, or left as the template's unfilled placeholder, MUST be
  treated as if the field were absent.
- **FR-006**: A stated value that the system does not recognise as a zone name MUST be rejected,
  aborting the run with a message that names the rejected value.
- **FR-007**: Rejection under FR-006 MUST occur before any content generation begins and before any
  bundle file is written, so no generation cost is incurred on a bad value.
- **FR-008**: Brief validation performed without generating a bundle MUST apply the same rejection.
- **FR-009**: A recognised zone name given in non-canonical letter casing MUST be accepted and
  emitted in its canonical spelling.
- **FR-010**: This feature MUST NOT change how a task's cadence binds to a day pattern, MUST NOT
  change how a routine's time-of-day is derived, and MUST NOT change the behaviour of any existing
  advisory check.
- **FR-011**: The stated timezone MUST NOT alter which hours the time-of-day spread selects from;
  it changes only the zone in which those hours are interpreted.
- **FR-012**: Adding this field MUST NOT change the meaning, position, or parsing of any other
  brief field, and MUST NOT invalidate any brief written before this feature.
- **FR-013**: Recognition and canonicalisation of a stated zone name MUST be host-independent: the
  same brief MUST be accepted-or-rejected identically, and MUST emit the identical zone spelling, on
  any machine whose zone database contains the zone. This extends the existing cross-machine
  determinism guarantee for schedules to the zone they are expressed in.

### Key Entities

- **Company timezone**: One optional, company-level zone name stated in the brief. Absent means the
  existing default.
- **Routine schedule trigger**: The emitted schedule a routine fires on. It already carries a
  timezone; today that timezone is a fixed constant and after this feature it is the company's.
- **Spread window**: The fixed range of hours from which a routine's time-of-day is drawn. Unchanged
  here; this feature changes the zone the window is expressed in, not the window.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a brief stating a timezone, 100% of emitted routines declare that zone, and zero
  declare the default.
- **SC-002**: For a brief stating a timezone, the emitted local time-of-day of every routine falls
  within the spread window as measured in the operator's own zone — where today, for an operator
  three hours from the default, none of them reliably do.
- **SC-003**: For every brief written before this feature, the generated bundle is byte-identical
  to its pre-feature output — zero briefs change.
- **SC-004**: An unrecognised zone name is reported to the operator in 100% of cases, with zero
  cases falling back silently to the default.
- **SC-005**: Rejection of an unrecognised zone name costs nothing in content generation — zero
  generation calls are made on a brief that fails this check.
- **SC-006**: Regenerating an unchanged brief that states a timezone produces byte-identical
  schedules across separate program runs, matching the determinism guarantee already in force.
- **SC-007**: The same brief produces the identical emitted zone spelling on a case-sensitive and a
  case-insensitive filesystem — zero host-dependent differences.

## Out of Scope

Named explicitly because the analysis that produced this feature identified them, and because the
next feature to touch this area should not have to rediscover why they were left out.

- **A structured schedule channel.** Binding the brief's stated clock times, days-of-month and
  intended ordering requires a strict line grammar and a change to how a task's cadence is
  represented — a task's cadence today cannot hold a clock time, a day-of-month or a zone
  regardless of what is threaded to it. Settled in design, specified separately.
- **Any change to how a cadence binds to days.** A cadence naming a weekday still binds that
  weekday; a monthly cadence still lands on the day-of-month it lands on today, including its
  inability to express any other. Correcting that is part of the deferred work above.
- **Any change to the time-of-day spread.** The deterministic derivation, the window bounds and the
  granularity are all untouched.
- **Any change to the advisory checks.** The shared-trigger, split-activity and producer/consumer
  ordering checks are unmodified. In particular, the ordering check's textual-reference gate is
  known to miss dependencies expressed without naming the upstream task; that is recorded against
  the decision that introduced it, not repaired here.
- **Per-agent or per-routine zones.** A company operating across zones is a real thing and not this
  operator's situation; the single value is deliberate, and widening it later is additive.

## Assumptions

- The zone names the system recognises are those in the platform's zone database, rather than a
  list maintained in this repository. A curated list would drift from the real database and would
  reject valid zones as the database evolves.
- The target platform interprets a routine's schedule in the declared zone, including across
  daylight-saving transitions. The trigger format and the platform's handling of it remain
  provisional pending live-import confirmation, exactly as they are today — this feature changes
  which zone is declared, not the contract for what a trigger is.
- A single company-level value is sufficient. Every agent in a generated company is scheduled for
  one operator's attention, so one zone describes the whole company.
- The field belongs with the brief's existing operator-working-pattern content, which already
  collects when and how much the operator works. Placing it there also avoids renumbering the
  brief's later sections, which existing briefs and the brief parser both depend on.
- The spread window's bounds remain a policy default, documented and adjustable, not a correctness
  property — unchanged from the feature that introduced them. This feature makes the existing
  rationale true rather than proposing a new one.
