# Contract: Company-level routine timezone

Postconditions the test suite asserts. Each cites the spec requirement it discharges.

## C1 — Brief field: acceptance and canonicalisation

Given a brief whose section 9 states a timezone:

- **C1.1** A value the zone database recognises, in its canonical spelling, is accepted and stored
  unchanged. *(FR-001)*
- **C1.2** A recognised value in any other letter casing is accepted and stored in its **canonical**
  spelling. `europe/helsinki` stores `Europe/Helsinki`. *(FR-009)*
- **C1.3** Surrounding whitespace is ignored. *(FR-001)*
- **C1.4** Recognition is by membership of the platform's enumerated zone set, not by filesystem
  lookup, so acceptance and stored spelling are identical on a case-sensitive and a
  case-insensitive host. *(FR-013, SC-007)*
- **C1.5** A value the zone database does not recognise raises a brief-validation error whose message
  contains the rejected value. `Europe/Helsinky` and `+03:00` are both rejected. *(FR-006, SC-004)*
- **C1.6** A value the zone database recognises but which is not a Region/City name is accepted;
  the recognition set is the database, not a curated subset. *(spec US3.5)*
- **C1.7** An absent field, a blank value, or the template's unfilled bracketed placeholder all
  yield `None`, indistinguishably. *(FR-005)*
- **C1.8** The canonical spelling is the zone set's own member, never a string transformation of the
  input. A **non-title-case** database entry (e.g. `Etc/GMT-3`, `US/Eastern`) MUST round-trip
  unchanged from any casing, and MUST NOT be re-cased. This is asserted on a non-title-case zone
  specifically: a "capitalise each segment" implementation passes every test written only against
  `Region/City` names, and breaks silently on the entries that are not shaped that way.
  *(FR-009, FR-013)*

## C2 — Rejection happens before any generation

- **C2.1** A brief with an unrecognised zone fails validation at `CompanyBrief` construction, which
  precedes every Anthropic call and every file write on both the `generate` and the `validate`
  paths. Zero generation calls are made. *(FR-007, SC-005)*
- **C2.2** The `validate` command rejects such a brief on the same terms as `generate`. *(FR-008)*

## C3 — Emission

Given a rendered bundle:

- **C3.1** When the brief states a timezone, every emitted routine declares that canonical zone, and
  none declares the default. *(FR-003, SC-001)*
- **C3.2** All routines in one bundle declare the same zone; a per-routine divergence is not
  representable. *(FR-002)*
- **C3.3** When the brief states no timezone, every emitted routine declares `UTC`. *(FR-004)*
- **C3.4** For a given brief, each routine's cron day-pattern and time-of-day fields are identical
  whether or not a timezone is stated — only the declared zone differs. *(FR-010, FR-011)*
- **C3.5** A bundle with no recurring tasks emits no routines and no timezone, whether or not the
  brief states one. *(spec Edge Cases)*

## C4 — No regression

- **C4.1** For a brief that omits the field, the full rendered file set is byte-identical to the
  pre-feature output. *(FR-004, SC-003)*
- **C4.2** Adding the section-9 line changes no other section-9 value: `hours_per_week`,
  `capital_monthly_eur` and `capital_setup_eur` still parse from a brief that also states a
  timezone. *(FR-012)*
- **C4.3** A brief written before this feature — with no timezone line anywhere — parses without
  error. *(FR-012)*
- **C4.4** The existing routine advisory checks (shared-trigger, split-activity, producer/consumer
  ordering) produce identical findings with and without a stated timezone. *(FR-010)*
- **C4.5** Regenerating an unchanged brief that states a timezone produces byte-identical schedules
  across separate program invocations. *(SC-006)*
