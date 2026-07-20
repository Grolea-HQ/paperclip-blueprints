# Feature Specification: Per-agent run-policy override from the brief

**Feature Branch**: `014-run-policy-override`

**Created**: 2026-07-20

**Status**: Draft

**Input**: User description: "Per-agent run-policy override from the brief — the generator lets the operator's brief specify per-agent run-policy values (a maximum-turns-per-run cap, a maximum-concurrent-runs limit, and a heartbeat on/off toggle) and emits them into the bundle so the deployer applies them. Layers on top of the existing role-derived run-policy: a brief-specified value overrides the role-derived value for that agent and field. The heartbeat toggle is a new brief-only field emitted only when the brief states it. Adds no new defaults, heuristics, or inference — a pure carrier that passes brief-stated values through, following the per-agent budget precedent (a pure, deterministic, brief-driven renderer). Backward compatible: a brief with no run-policy values generates exactly what the generator produces today. Carrier/emit side only — the deployer that consumes it is out of scope."

## Overview

An agent wake with no bound on turns or concurrency can loop and burn budget before anything
stops it. Today the generator emits per-agent run-policy caps that are chosen for the operator by
a fixed role rule — the operator has no way to say "this specific agent should be bounded to N
turns" or "do not run this agent on a heartbeat" from the brief. This feature gives the operator
that direct control: the brief can state run-policy values for specific agents, and the generator
carries those exact values into the bundle so the deployer applies them.

The feature is a **pure carrier**. It does not decide what any value should be, does not infer
values from company shape, role, or risk, and adds no defaults. It only passes through what the
operator wrote. Where the brief is silent, the generator's existing behavior is untouched.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bound a specific agent's turns and concurrency from the brief (Priority: P1)

An operator authoring a company brief knows that one particular agent — say a research or
watcher-style role — should never run more than a small number of turns per wake, and should not
fan out into several concurrent runs. In the brief, the operator names that agent and states a
maximum-turns-per-run and a maximum-concurrent-runs value. After generation, the bundle carries
those exact values for that agent, overriding whatever value the generator would otherwise have
emitted for it.

**Why this priority**: This is the core of the feature — the operator's ability to bound turns and
concurrency for named agents is the whole point (an unbounded wake can loop and burn budget). It is
independently valuable and testable on its own, without the heartbeat toggle.

**Independent Test**: Provide a brief that names one agent with an explicit turns cap and
concurrency limit; generate the bundle; confirm that agent's emitted run-policy values equal the
brief-stated values, and that every other agent's values are unchanged from a no-override run.

**Acceptance Scenarios**:

1. **Given** a brief that states a maximum-turns-per-run value for a named agent, **When** the
   bundle is generated, **Then** that agent's emitted turns cap equals the brief-stated value and
   is not the value the generator would otherwise have chosen.
2. **Given** a brief that states a maximum-concurrent-runs value for a named agent, **When** the
   bundle is generated, **Then** that agent's emitted concurrency limit equals the brief-stated
   value.
3. **Given** a brief that states a run-policy value for one agent only, **When** the bundle is
   generated, **Then** every other agent's run-policy values are identical to what they would be
   with no override in the brief.
4. **Given** a brief that states a run-policy value referencing an agent that does not exist in the
   generated company, **When** the bundle is generated, **Then** the operator is warned that the
   reference matched no agent, and no run-policy value is invented for a non-existent agent.

---

### User Story 2 - Disable heartbeat for a specific agent from the brief (Priority: P2)

An operator wants a specific agent to run only when it is explicitly given work, never on a
recurring heartbeat wake. In the brief, the operator names that agent and sets its heartbeat to
off. After generation, the bundle carries a heartbeat-disabled signal for that agent. For every
agent the operator does not mention, nothing about heartbeat is emitted and behavior is unchanged.

**Why this priority**: Valuable and operator-requested, but secondary to bounding turns/concurrency.
Unlike turns/concurrency (which the generator already emits a base value for), heartbeat is a new
brief-only signal, so it must be emitted only on explicit operator instruction and never implied.

**Independent Test**: Provide a brief that sets heartbeat off for one named agent; generate the
bundle; confirm a heartbeat-disabled signal appears for that agent and for no other agent, and that
a brief which mentions no heartbeat produces no heartbeat signal anywhere.

**Acceptance Scenarios**:

1. **Given** a brief that sets heartbeat off for a named agent, **When** the bundle is generated,
   **Then** that agent carries a heartbeat-disabled signal in its run-policy.
2. **Given** a brief that sets heartbeat on for a named agent, **When** the bundle is generated,
   **Then** that agent carries a heartbeat-enabled signal in its run-policy.
3. **Given** a brief that says nothing about heartbeat for any agent, **When** the bundle is
   generated, **Then** no heartbeat signal is emitted for any agent, and behavior is unchanged.

---

### User Story 3 - A brief with no run-policy values changes nothing (Priority: P1)

An operator who does not care about run-policy tuning writes a brief with no run-policy values at
all. Generation produces exactly the bundle it produces today — byte-for-byte the same run-policy
output as before this feature existed.

**Why this priority**: Backward compatibility is a hard requirement and a release gate. It shares
P1 with User Story 1 because a regression here silently changes every existing operator's output.

**Independent Test**: Generate a bundle from a brief with no run-policy values, both before and
after this feature; diff the two bundles; confirm they are identical.

**Acceptance Scenarios**:

1. **Given** a brief with no run-policy values, **When** the bundle is generated, **Then** the
   emitted run-policy output is identical to the pre-feature output for the same brief.
2. **Given** a brief with no run-policy values, **When** the bundle is generated, **Then** no
   heartbeat signal is emitted for any agent (there is no base heartbeat behavior to carry).

---

### Edge Cases

- **Reference matches multiple agents**: a brief line whose agent reference legitimately names more
  than one agent applies the stated values to each matched agent (mirrors how existing per-role
  brief overrides fan out). The most-specific match wins when one reference nests inside another.
- **Partial value set for one agent**: a brief that states only a turns cap for an agent (and not a
  concurrency limit) overrides only turns; the un-stated field keeps its existing generator-chosen
  value. Fields are independent.
- **Out-of-range or non-numeric value**: a stated value that is not a usable positive whole number
  (for turns/concurrency) is rejected at brief-validation time with a clear message, rather than
  silently emitting a broken bundle.
- **Same agent referenced twice with conflicting values**: the brief is reported as ambiguous at
  validation time rather than one line silently winning.
- **Reference matches no agent**: reported as a non-blocking warning naming the unmatched
  reference (mirrors the existing unmatched-override warning); generation still proceeds.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The brief MUST provide a channel through which the operator can state, for a named
  agent, any subset of three run-policy values: a maximum-turns-per-run cap, a maximum-concurrent-
  runs limit, and a heartbeat on/off toggle.
- **FR-002**: An agent named in the brief MUST be resolved to a generated agent by the same
  boundary-safe reference matching already used for per-role brief overrides (matching against the
  agent's slug, title, and name), so the operator can name agents without knowing generated slugs.
- **FR-003**: A brief-stated maximum-turns-per-run value MUST override, for the referenced agent,
  the turns value the generator would otherwise emit; a brief-stated maximum-concurrent-runs value
  MUST likewise override the concurrency value for that agent.
- **FR-004**: The three run-policy fields MUST be independent: stating one field for an agent MUST
  NOT change the other fields for that agent.
- **FR-005**: The heartbeat toggle MUST be emitted for an agent only when the brief explicitly
  states it for that agent; when the brief says nothing about heartbeat, no heartbeat signal is
  emitted for any agent.
- **FR-006**: When the brief states no run-policy values at all, the generated bundle MUST be
  identical to what the generator produces today for the same brief (no new fields, no changed
  values, no heartbeat signal).
- **FR-007**: The feature MUST NOT introduce any default, heuristic, or inference that chooses a
  run-policy value from company shape, role, risk, or any signal — it emits only values the
  operator stated. (Existing role-derived turns/concurrency values remain the base and are
  unchanged by this feature; this feature only overrides them where the brief speaks.)
- **FR-008**: The derivation from brief to emitted values MUST be deterministic and free of any
  model call or external I/O — the same brief always yields the same run-policy output.
- **FR-009**: A brief run-policy value that references an agent matching no generated agent MUST
  produce a non-blocking warning that names the unmatched reference; generation proceeds and no
  value is emitted for a non-existent agent.
- **FR-010**: A brief run-policy value that is malformed (a turns or concurrency value that is not a
  usable positive whole number, an unrecognized heartbeat state, or the same agent given
  conflicting values) MUST be rejected at brief-validation time with a message identifying the
  problem, before any generation work is done.
- **FR-011**: The emitted run-policy values MUST travel in the bundle's existing per-agent run-
  policy carrier alongside the role-derived turns and concurrency values, so the deployer consumes
  them through one carrier.
- **FR-012**: The scope of this feature is the emit/carrier side only; how the deployer applies the
  emitted values (including the heartbeat toggle) is out of scope and lives outside this repository.
- **FR-013**: The input template MUST document the run-policy channel — the three values, that they
  are optional, that they name specific agents, and that omitting them leaves behavior unchanged —
  so an operator can discover and use it without reading code.

### Key Entities *(include if feature involves data)*

- **Run-policy override**: an operator-stated, per-agent set of up to three optional values —
  maximum turns per run, maximum concurrent runs, heartbeat on/off — attached to a named agent
  reference. Absent for any agent the operator does not mention.
- **Resolved per-agent run policy**: the values actually emitted for an agent — the existing role-
  derived turns and concurrency values, with any brief-stated value substituted in, plus a
  heartbeat signal only when the operator stated one.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a brief that states run-policy values for a named agent, 100% of the stated
  values appear unchanged on that agent in the generated bundle.
- **SC-002**: For a brief with no run-policy values, the generated bundle is byte-for-byte
  identical to the pre-feature output for the same brief (zero diff).
- **SC-003**: Stating a run-policy value for one agent changes the run-policy output of zero other
  agents.
- **SC-004**: A heartbeat signal appears in the bundle only for agents the operator explicitly set
  it on, and for zero agents otherwise.
- **SC-005**: Every malformed run-policy value in a brief is reported at validation time; zero
  malformed values reach the generated bundle.
- **SC-006**: An operator can discover and correctly use the run-policy channel from the input
  template alone, without reading source code.

## Assumptions

- The brief expresses per-agent run-policy values through free-text override lines that name an
  agent, following the established per-role override convention (the same channel and boundary-safe
  matching used for adapter/model preferences). The exact line grammar is an implementation detail
  resolved in planning; this spec fixes only the operator-visible behavior.
- "What the generator produces today" is the current `main` output, in which the existing role rule
  emits a turns cap and concurrency limit for every agent. This feature layers over that base; it
  does not remove or alter the base rule.
- The bundle already has a per-agent run-policy carrier (turns and concurrency). Adding the
  heartbeat toggle extends that carrier with one optional field; the field is absent unless the
  operator states it.
- Choosing *appropriate* run-policy values (by role, risk, or company shape) is deliberately out of
  scope for this repository. This feature only transports operator-stated values.
- The deployer that reads the emitted run-policy and applies it (including mapping the heartbeat
  toggle to runtime behavior) lives outside this repository and is unchanged by this work.
