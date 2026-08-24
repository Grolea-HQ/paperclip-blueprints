# Feature Specification: A bundle may not assert a rhythm it carries no routine for

**Feature Branch**: `024-routine-claim-coherence`

**Created**: 2026-08-23

**Status**: Draft

**Input**: A generated bundle's `OPERATIONS.md` referred to scheduled runs and cadence thirteen
times, including instructions of the form *"on each scheduled run, audit that no gate is unowned"*.
The bundle contained zero routines. Investigating that turned up something larger, and the larger
finding is what this feature is about.

## The finding that leads

**Every agent is told this individually, not just the operations document.**

`OPERATIONS.md` is one carrier. The idle-state protocol is rendered from a single source —
`OperationsDefinition.idle_state_protocol` — into `OPERATIONS.md` *and* verbatim into every agent's
`AGENTS.md`, where validator V-gov requires it to be. Its mandated content states that the routine
schedule is the agent's liveness and that the agent waits for the next scheduled run.

So on a zero-routine bundle, each agent individually carries an instruction to wait for a trigger
that does not exist. The thirteen occurrences in `OPERATIONS.md` are the visible share of something
already distributed per-agent.

**This is observed, not reasoned about in principle.** It was found on a bundle this engine
produced: every agent in it carried the protocol, and the bundle contained no routine for any of
them to wait on.

One source, N carriers, is also the shape of the fix: correcting the source corrects every copy.

## The mechanical root

`generate_operations` is passed the company, the brief, the agent list, and the client. It is passed
no tasks and no routines. Routines do not exist at that point — they are derived at render time from
tasks carrying `recurrence`.

The generator is therefore structurally incapable of knowing whether a routine will exist, and fills
its `routine_slots` from the agent list alone. It is a generator asked to describe a mechanism it
cannot see.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - No agent is told to wait for a trigger that does not exist (Priority: P1)

An operator generates a company from a brief that declares no cadence. Today every agent's
`AGENTS.md` tells it the routine schedule is its liveness, and `OPERATIONS.md` instructs work "on
each scheduled run". Nothing will ever fire.

After this feature, a bundle carrying no routines contains no claim that one exists — in
`OPERATIONS.md` or in any agent's `AGENTS.md`.

**Why this priority**: It is the observed defect, and it lands on every agent in the bundle rather
than in one document.

**Independent Test**: Render a full bundle from a fixture whose tasks carry no recurrence, and read
every generated file for a claim of a scheduled rhythm.

**Acceptance Scenarios**:

1. **Given** a bundle whose tasks carry no recurrence, **When** it is validated, **Then** an
   `OPERATIONS.md` asserting scheduled runs is a violation naming the offending terms.
2. **Given** the same bundle, **When** it is validated, **Then** the same assertion inside any
   agent's `AGENTS.md` is a violation naming that agent's file.
3. **Given** a bundle that carries routines, **When** it is validated, **Then** the rule does not
   fire, whatever the prose says.

---

### User Story 2 - The rule is clearable, because the generator can see the fact (Priority: P1)

A rule the generator cannot satisfy is a permanent rejection, not a regeneration trigger. The
operations generator cannot currently produce a passing zero-routine bundle at any sampling
temperature, because its prompt mandates the scheduled-run language unconditionally and it has no
way to know the mandate is wrong for this bundle.

So it is told the one fact it lacks: which agents own recurring work. Empty means no routine will
exist, and the prompt then requires prose that claims none.

**Why this priority**: Without it, User Story 1 makes every zero-cadence brief ungenerable. The two
ship together or the feature is a regression.

**Independent Test**: Generate operations against a stubbed transport with no recurring owners and
confirm the request tells the generator so, and asks for prose that claims no schedule.

**Acceptance Scenarios**:

1. **Given** no task carries recurrence, **When** the operations mandate is requested, **Then** the
   request states that no routine will exist and asks for an idle-state protocol that does not
   claim a schedule, and for empty routine slots.
2. **Given** tasks that recur, **When** the request is made, **Then** it names the agents that own
   recurring work, and the routine slots are drawn from those agents rather than from the whole
   agent list.
3. **Given** a zero-routine response that still claims a schedule, **When** it is checked, **Then**
   it is rejected at that call and re-sampled — the generator can now produce a passing answer, so
   the re-sample has somewhere to land.

---

### User Story 3 - The operator learns what a no-cadence design produces (Priority: P2)

A brief that declares no cadence produces a company where nothing in the bundle triggers any agent.
That is a legitimate design. It is also a consequence the operator cannot derive from the brief and
did not knowingly choose.

**Why this priority**: Advisory, never blocking. Separable from US1 and US2 — it reports a property
of a *valid* bundle.

**Independent Test**: Render a bundle with no recurring tasks and read the warning sink.

**Acceptance Scenarios**:

1. **Given** a bundle that emits no routine, **When** it is rendered, **Then** the warning sink
   carries one advisory stating that no routine is emitted and no agent has a trigger from this
   bundle.
2. **Given** a bundle that emits at least one routine, **When** it is rendered, **Then** no such
   advisory appears.
3. **Given** the advisory, **When** it is read, **Then** it reports what the design produces and
   does not grade it, recommend a change, or call the company inert.

---

### Edge Cases

- **A bundle with routines whose prose over-claims** — e.g. two routines but prose implying daily
  runs for everyone. Out of scope: the rule keys on zero, where the claim is unambiguously false.
- **`--single-agent` bundles** carry no `OPERATIONS.md` and no `OperationsDefinition`, so neither
  the rule nor the advisory applies.
- **An operator-driven rhythm** — "the operator reviews output weekly" — needs no routine and must
  not trip the rule. See FR-004.
- **A brief that declares cadence but whose tasks lose it** — the rule keys on emitted routines, not
  on the brief, so it fires correctly.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `generate_operations` MUST be told which agent slugs own recurring work. An empty set
  MUST mean no routine will be emitted.
- **FR-002**: When no agent owns recurring work, the request MUST ask for an idle-state protocol that
  claims no schedule, and for empty routine slots.
- **FR-003**: When agents do own recurring work, routine slots MUST be drawn from those agents rather
  than from the whole agent list.
- **FR-004**: When a bundle emits zero routines, it MUST be a validation violation for `OPERATIONS.md`
  or any agent's `AGENTS.md` to assert that a scheduled or recurring trigger exists. The rule MUST key
  on terms naming the *mechanism* — a platform-provided trigger — and MUST NOT fire on cadence
  adjectives alone, because an operator-driven rhythm is legitimate and needs no routine.
- **FR-005**: The violation MUST name the file and the offending term, so the failure is actionable
  without reading the bundle.
- **FR-006**: The rule MUST fire per carrier: `OPERATIONS.md` and every agent's `AGENTS.md` are
  checked, because the protocol is propagated to all of them.
- **FR-007**: The rule MUST NOT fire when the bundle emits at least one routine.
- **FR-008**: "Emits zero routines" MUST be determined from what the bundle actually ships — the
  rendered `.paperclip.yaml` routines block — not from the brief.
- **FR-009**: A zero-routine response that still claims a schedule MUST be rejected at the operations
  call and re-sampled within the existing per-leaf attempt budget, so the run does not reach
  validation with a known-bad document.
- **FR-010**: Nothing MUST rewrite, strip, or otherwise repair generated prose to satisfy the rule.
- **FR-011**: When a bundle emits zero routines, an advisory MUST be surfaced through the existing
  warning sink, never as a validation error, stating that no routine is emitted and no agent has a
  trigger from this bundle.
- **FR-012**: The advisory MUST NOT claim agents are inert. `heartbeatEnabled` is a brief-only field,
  unset by default, so the bundle asserts nothing about heartbeats and the stronger claim would be
  false.
- **FR-013**: V-idle and V-gov MUST continue to hold. A zero-routine idle-state protocol still must
  not use `in_progress` as a liveness marker, and must still appear in every `AGENTS.md`.
- **FR-014**: For bundles that emit routines, every generated file MUST be unchanged by this feature.

### Key Entities

- **Routine owners**: the agent slugs owning tasks that carry recurrence — the one fact the
  operations generator lacks. Empty is the meaningful case.
- **Schedule-mechanism claim**: a statement in a governance carrier that a platform-provided
  recurring trigger exists. False, by construction, in a zero-routine bundle.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A zero-routine bundle whose prose claims a schedule does not reach disk.
- **SC-002**: A zero-cadence brief generates successfully end to end. Verified by generating a full
  bundle with no recurring tasks and asserting it validates — the regression US1 would cause on its
  own.
- **SC-003**: The rule fires on an agent's `AGENTS.md`, not only on `OPERATIONS.md`, since that is
  where the defect is distributed.
- **SC-004**: A bundle emitting at least one routine is byte-identical to its pre-change output.
- **SC-005**: The re-sample path is exercised: a first response claiming a schedule with no routines
  is rejected and a second, clean response completes the run.
- **SC-006**: The advisory appears exactly once for a zero-routine bundle and not at all otherwise,
  and contains no word grading the design.

## Assumptions

- **Threading one fact does not replace the validator.** The validator is what closes the class,
  including instances nobody has thought of; the input is only what makes the rule satisfiable rather
  than a permanent rejection. Both are required — the original decision to build only the validator
  rested on a premise about the generator that turned out to be false.
- **The mechanism/adjective split is where false positives live.** "Weekly" in "the operator reviews
  weekly" is legitimate; "scheduled run" and "routine" name a platform trigger and are not. The rule
  is drawn at the mechanism, accepting that it will miss an adjective-only over-claim rather than
  reject a legitimate operator rhythm.
- **V-idle does not require schedule wording.** It is a sentence-level check that `in_progress` is not
  used as a liveness marker, so a zero-routine protocol is expressible without violating it. This was
  verified, not assumed; had it required the wording, FR-002 and FR-013 would be in direct conflict.
- **`--single-agent` is untouched** — no `OPERATIONS.md`, no `OperationsDefinition`.

## Rejected Alternatives

### Make the operations prose authoritative over emitted routines

**Rejected, and dead.** Routines derive from task recurrence, and ADR-038 holds that stated schedules
bind only through a machine channel — prose cannot produce a cron. This branch inverts that ADR.

### Suppress or rewrite the routine language at render time when zero routines exist

**Rejected.** It is post-hoc correction of generated prose: the run would succeed, the operator would
see nothing, and the document would differ from what the generator actually produced. That is the
family prohibited in ADR-043, and it would additionally contradict V-idle silently by editing a field
V-idle validates.

### Build the validator without changing the generator's inputs

**Rejected after investigation** — this was the original decision, and it rests on a premise that
turned out to be false. The operations prompt *mandates* the scheduled-run language unconditionally,
and the generator cannot know the mandate is wrong for a given bundle. A rule of this shape would fire
on every zero-routine bundle, and no amount of re-prompting could clear it, because every re-sample is
drawn from the same blind distribution. A validator-triggered regeneration is only clearable by a
generator that could have seen the fact. The task-shaped-goal precedent does not transfer: that
generator *can* emit a passing goal and merely sometimes doesn't.
