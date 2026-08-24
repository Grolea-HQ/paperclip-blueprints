# Feature Specification: Handoff targets are drawn from a closed set

**Feature Branch**: `023-closed-set-handoffs`

**Created**: 2026-08-23

**Status**: Draft

**Input**: A generation run was rejected by validator I8 because one agent's `AGENTS.md` named a
handoff to `qa-led` where the agent is `qa-lead`. One character, one line; the same agent was named
correctly everywhere else in the bundle, including twice more in the same file. The validator did
its job — but it did it after roughly eighty model calls had been paid for, and it rejected the
whole run for a value whose legal set was fully known before the call was made.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A handoff cannot name an agent that does not exist (Priority: P1)

The agents generator is given the org plan before it writes anything. The set of agent slugs is
therefore closed and known at prompt time. Today the generator asks for that slug as free text
inside a sentence and checks it afterwards; the model authors the slug character by character, and
a near-miss is indistinguishable to it from a hit.

After this feature the handoff target is chosen from a stated, closed set rather than typed. The
near-miss stops being an available output.

**Why this priority**: This is the difference between a class of failure that cannot occur and one
that is merely detected. Every other agent-slug field in the generator already works this way — a
project's `owner` and a task's `assignee` are taken from the planner stub, never from model prose.
Handoffs are the sole remaining place where a known-set value is authored as free text, and they
are the only place this failure has ever come from.

**Independent Test**: Generate one agent against a stubbed transport and inspect the request that
was sent. Deliverable on its own: the request states the legal targets, so the constraint is
present whether or not any particular model honours it.

**Acceptance Scenarios**:

1. **Given** an org plan naming agents `ceo`, `qa-lead`, `writer`, **When** the mandate for `ceo` is
   requested, **Then** the request declares the legal handoff targets as an explicit set of those
   slugs rather than asking for a slug as free text.
2. **Given** the same org plan, **When** the model returns a handoff naming `qa-lead`, **Then** the
   assembled `AgentDefinition` carries it in exactly the form the renderers consume today.
3. **Given** a single-agent company, **When** the mandate is requested, **Then** no handoff target
   is asked for at all, and both handoff lists are empty.

---

### User Story 2 - A near-miss costs one call, not a run (Priority: P1)

Constraining the request does not by itself guarantee the constraint binds: the project's structural
model may decline the constrained-output request, in which case the existing resilience path drops
the constraint and retries unconstrained (ADR-014). The operator must not be able to lose a run to a
bad slug because a constraint silently stopped applying.

So the check that the target is in the closed set is made where the answer arrives — at that one
leaf call — and it is made every time, regardless of whether the constraint was accepted. A failure
there re-samples one call. A failure at the end of the run costs the run.

**Why this priority**: This is the half of the work that actually delivers the operator's stated
outcome. It is also the half that holds when the platform's model support changes underneath the
project, which it has done before.

**Independent Test**: Drive the generator with a transport that returns an out-of-set target on its
first response and a valid one on its second, with no constraint honoured at all. The generator
returns a valid definition, having made two calls rather than failing the run.

**Acceptance Scenarios**:

1. **Given** a transport that returns the handoff target `qa-led` when `qa-lead` is the agent,
   **When** the mandate is generated, **Then** that response is rejected and re-sampled, and the
   rejection message names both the agent and the offending target.
2. **Given** a transport that returns `qa-led` on every attempt, **When** the mandate is generated,
   **Then** generation fails at that agent naming the offending target — and no other agent's
   mandate is requested as a result of that failure.
3. **Given** a transport that never honours the output constraint, **When** it returns an out-of-set
   target, **Then** it is still rejected — the check does not depend on the constraint having been
   accepted.

---

### User Story 3 - Nothing quietly repairs a near-miss (Priority: P1)

`qa-led` is one edit away from `qa-lead`, and there will be a temptation to close that gap
automatically. The feature must make that permanently unavailable.

A repaired near-miss is worse than the failure it replaces: the run succeeds, the operator sees
nothing, and the bundle ships an agent handing work to whichever role the repair guessed. The
current behaviour is loud and correct about the fact that something is wrong; only its *timing* is
the defect.

**Why this priority**: It is the requirement most likely to be violated later by someone reading
only the ticket title. Stating it as a testable requirement rather than a comment is what keeps it
out.

**Independent Test**: Assert that an out-of-set target which differs from a real slug by a single
character produces a rejection, not a substitution.

**Acceptance Scenarios**:

1. **Given** a returned target one character away from a real agent slug, **When** it is checked,
   **Then** it is rejected; no output contains the corrected slug as a result of the near-miss.
2. **Given** a returned target differing from a real slug only by surrounding whitespace, case, or
   backticks, **When** it is checked, **Then** the outcome is decided by normalisation rules stated
   in this spec (FR-011) and never by similarity to a real slug.

---

### Edge Cases

- **The model returns the right slug with decoration** — wrapping backticks, stray whitespace. This
  is a formatting difference, not a different agent; normalisation of formatting is not repair
  (FR-011).
- **The model returns an empty or absent target.** Today `_handoff_head` treats an empty head as
  nothing to check, so an empty handoff passes I8 silently. It must be rejected at the call.
- **The model returns a handoff naming the agent itself.** Legal under the closed set (the agent
  exists) but meaningless; out of scope for this feature and left to existing behaviour.
- **A single-agent company** has no legal target at all — the closed set is empty. An empty set
  cannot be expressed as a choice, so the fields must not be requested.
- **The constrained-output request is declined by the model.** Covered by FR-007: the check is
  unconditional.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The mandate request for an agent MUST state the legal handoff targets as an explicit
  closed set of agent slugs, drawn from the org plan already available at that point.
- **FR-002**: The legal set MUST be the slugs of all agents in the company other than the agent
  being generated — the same population validator I8 checks against, so that generation and
  validation cannot disagree about what is legal. (See Assumptions for why not the narrower
  manager/reports/peers set the prompt currently describes in prose.)
- **FR-003**: The request MUST separate the handoff *target* from the prose describing what flows
  across the handoff, so the target can be constrained without constraining the prose.
- **FR-004**: A returned handoff whose target is not in the legal set MUST be rejected at the call
  that produced it.
- **FR-005**: A rejection MUST re-sample that single call, feeding back what was wrong, within the
  existing per-leaf attempt budget. A subsequent valid response MUST let the run continue normally.
- **FR-006**: When the attempt budget is exhausted, generation MUST fail naming the agent and the
  offending target.
- **FR-007**: The check in FR-004 MUST be unconditional — it MUST NOT be skipped, weakened, or made
  contingent on the output constraint having been accepted by the model.

  **Why both mechanisms exist, and why neither is redundant.** FR-001 and FR-007 will read to a
  later reviewer as two mechanisms doing one job, with an obvious simplification available. They are
  not doing one job. The constraint in FR-001 makes the near-miss *unavailable to the model*, which
  is the only thing that prevents the failure rather than detecting it — but it binds only when the
  model accepts a constrained-output request, and when it is declined the existing resilience path
  drops it and retries unconstrained (ADR-014). That drop is silent by design: it exists so a
  model without constrained-output support does not abort a run. The consequence is that a
  guarantee resting on the constraint alone would disappear without any signal, on a model change
  nobody made deliberately — and the run would go back to failing at I8 after eighty calls, which
  is the exact defect this feature exists to remove. The check in FR-007 is therefore not a
  redundant second opinion; it is the only part of this feature that is load-bearing under model
  substitution. Removing either one is a real loss: removing the constraint gives up prevention and
  keeps only detection; removing the check gives up the guarantee whenever the constraint does not
  bind. **Do not collapse them.**
- **FR-008**: The system MUST NOT alter a rejected target to any valid value. Fuzzy matching,
  nearest-neighbour resolution, edit-distance repair, and "did you mean" substitution are prohibited
  in generation, rendering, and validation.
- **FR-009**: For a single-agent company the handoff fields MUST NOT be requested from the model,
  and both MUST be empty in the result.
- **FR-010**: The assembled `AgentDefinition` and every file rendered from it MUST be unchanged in
  shape by this feature — the handoff entries keep the form the renderers and validator consume
  today.
- **FR-011**: Normalisation applied before the membership check MUST be limited to formatting that
  carries no identity: surrounding whitespace and enclosing backticks. It MUST NOT include case
  folding, punctuation substitution, or any transformation that could map one agent's slug onto
  another's.
- **FR-012**: Validator I8 MUST remain in force, unchanged in behaviour. This feature adds a
  constraint upstream of it; it does not replace it.
- **FR-013**: An empty or missing handoff target MUST be rejected under FR-004 rather than passing
  as "nothing to check".

### Key Entities

- **Legal target set**: the closed set of agent slugs a given agent may hand to or receive from,
  derived from the org plan before the call and carried into both the request and the check.
- **Handoff entry**: a pairing of a target drawn from the legal set with free prose describing what
  crosses the handoff. Its rendered form is unchanged; only its authored form is separated.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An out-of-set handoff target costs at most the per-leaf attempt budget of one agent's
  mandate — never a whole bundle's generation. Measured as calls made when a transport returns a bad
  target once: the run completes.
- **SC-002**: When the target is unrecoverable, the run stops at the agent that produced it, with no
  further agents' mandates requested because of it.
- **SC-003**: No code path in the repository maps an invalid agent slug to a valid one. Verified by a
  test asserting a single-character near-miss rejects, and by the absence of any similarity or
  edit-distance comparison over agent slugs.
- **SC-004**: The rejection is reproduced with the output constraint disabled entirely, proving the
  guarantee does not rest on model support for constrained output.
- **SC-005**: For inputs where the model returns valid targets, every generated file is byte-identical
  to what the pre-change code produced from the same responses.
- **SC-006**: The I8 violation that motivated this work can no longer be produced by the generator
  path: a transport returning `qa-led` for a company containing `qa-lead` never yields a bundle.

## Assumptions

- **The legal set is all other agents, not the adjacent set.** The prompt currently tells the model
  to use only its manager, direct reports, and peers. That prose stays as guidance, but the *enforced*
  set is wider — every other agent — so that the hard constraint matches exactly what I8 accepts. Two
  checks over the same value with different populations is a defect generator: a legitimate
  cross-branch handoff would be rejected at generation while passing validation, and the two would
  have to be kept in step forever. This choice cannot newly reject anything that is valid today. See
  Rejected Alternatives for the narrow reading and what it would actually cost.

- **The project's structural model may not honour constrained output.** `claude-sonnet-4-6` is not in
  the documented support list for constrained output, and the existing resilience path silently drops
  the constraint when it is declined. The spec therefore treats the constraint as a defence and the
  check as the guarantee, rather than assuming either alone.
- **The existing per-leaf retry mechanism is the right place for the re-sample.** It already
  re-samples a single call on a malformed response and feeds the error back; an out-of-set target is
  the same kind of failure — a response that did not meet the stated contract.
- **Project owner and task assignee are out of scope.** Both already take their slug from the planner
  stub rather than model prose, so they cannot exhibit this failure.
- **Souls, skills, projects, tasks, and operations generators are untouched.** No other generator
  authors an agent slug as free text.

## Rejected Alternatives

### Enforce the adjacent set (manager, direct reports, peers) as the closed set

**Rejected.** Recorded here so the wide set is not read as a default nobody examined, and so this is
not re-proposed as a variant of this feature — because it is not one.

The narrow set is the population the prompt already describes in prose, and enforcing it would catch
a real class of org-design drift: a handoff reaching across the reporting structure is often a
span-of-control error rather than a legitimate flow. That is a defensible thing to want.

It is rejected on scope, not on merit. Enforcing it as a tighter set on this one call would make
generation stricter than validation: a cross-branch handoff would be rejected at generation while
passing I8 and every check downstream of it. That is the same divergence this feature exists to
remove, pointed the other way.

**What it would actually cost, if it is ever wanted.** The rule would have to hold in *both* places
— generation and validation — or the divergence simply changes direction. So it is a new shared
definition of adjacency, applied by the generator's constraint and by a bundle-level check, with one
implementation and one set of tests governing both. It is a span-of-control feature with its own
spec, not an enum narrowed on one call. Anyone proposing it as a small change to this feature has
mistaken its size.
