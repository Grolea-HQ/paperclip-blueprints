# ADR-044 — A bundle may not assert a rhythm it carries no routine for

**Status:** Accepted
**Date:** 2026-08-24
**Relates to:** ADR-022 (object model; the idle-state protocol and its delivery to agents),
ADR-038 (stated schedules bind only through a machine channel), ADR-043 (no post-hoc repair of
generated content; the `check` seam this reuses), ADR-036 (routine scheduling and collisions)

---

## Context

A generated bundle's `OPERATIONS.md` referred to scheduled runs and cadence thirteen times,
including instructions of the form *"on each scheduled run, audit that no gate is unowned"*. The
bundle contained zero routines.

**The larger finding is the distribution, not the document.** The idle-state protocol is rendered
from a single source — `OperationsDefinition.idle_state_protocol` — into `OPERATIONS.md` *and*
verbatim into every agent's `AGENTS.md`, where validator V-gov requires it to be. Its mandated
content states that the routine schedule is the agent's liveness and that the agent waits for the
next scheduled run. So on a zero-routine bundle each agent individually carries an instruction to
wait for a trigger that does not exist; the occurrences in `OPERATIONS.md` are the visible share of
something already propagated per-agent.

**This is observed, not hypothesised.** It was found on a bundle this engine produced: every agent
in it carried the protocol, and the bundle contained no routine for any of them to wait on.

**The mechanical root.** `generate_operations` was passed the company, the brief and the agent list
— no tasks, no routines. Routines do not exist at that point; they are derived at render time from
tasks carrying `recurrence`. The generator was structurally incapable of knowing whether a routine
would exist, and filled its `routine_slots` from the agent list alone. It was a generator asked to
describe a mechanism it could not see.

## Decision

### 1. A cross-file rule (I16), because the rule is what closes the class

When the rendered `.paperclip.yaml` carries no `routines` entry, it is a validation violation for
any governance carrier to assert that a scheduled or recurring trigger exists. Threading facts into
the generator would prevent the reported instance and leave the class open; a rule catches instances
nobody has thought of.

### 2. Checked per carrier, not on the source field

`OPERATIONS.md` and every `agents/<slug>/AGENTS.md`. An agent reads its own `AGENTS.md`, so that is
where the defect lands and where the finding must point. Enumerating carriers also covers a future
carrier without anyone remembering to extend a source-side check.

### 3. Zero is read from the shipped artifact

From the rendered `.paperclip.yaml`, not re-derived from `config.tasks`. The rule is about what the
bundle carries, and that is the file the platform reads. S15 already asserts the two agree, so a
disagreement surfaces there with a clear message instead of here with a misleading one.

### 4. The line is drawn at the mechanism, and the omission is deliberate

The term set is multi-word phrases naming a platform-provided trigger — `scheduled run`,
`routine run`, `routine schedule`, `routine-driven`, `recurring cadence`, `on a schedule`, `cron`.

Bare `routine` and bare `recurring` are **excluded**: both have ordinary adjectival senses that are
true with no routine behind them, and the agents prompt writes exactly one of them ("approves
routine, low-consequence work"). Cadence adjectives — `weekly`, `daily`, `each morning` — are
**excluded** for the mirror reason: an operator-driven rhythm is legitimate in a company with no
routines at all, and rejecting *"the operator reviews output weekly"* would make the rule wrong in
the case an operator most likely wrote on purpose.

**The accepted cost:** an adjective-only over-claim is not caught. That is a narrower miss than the
false rejection it avoids. Recorded so the gap is a decision rather than an oversight.

**A hard constraint on editing that set:** no phrase in it may match text a template emits
unconditionally. If one did, the rule would fire on every zero-routine bundle and no regeneration
could clear it. A test holds that line.

### 5. The generator is told whether a routine will exist — reversing an earlier decision

`generate_operations` now receives the agent slugs owning recurring work. Empty means no routine will
be emitted, and the prompt then requires prose claiming none and empty routine slots.

**This reverses a decision made earlier the same day** — to build the validator and change nothing
about the generator's inputs — and the reversal is recorded because the original rested on a premise
that turned out to be false. That premise was: *a brief that genuinely declares no cadence produces
operations prose that does not claim one, so the rule never fires.* It cannot. The operations prompt
**mandated** the scheduled-run language unconditionally, and the generator had no way to know the
mandate was wrong for a given bundle. A rule of this shape would have fired on every zero-routine
bundle, and no re-prompting could have cleared it, because every re-sample is drawn from the same
blind distribution.

**The general principle worth keeping:** a validator-triggered regeneration is only clearable by a
generator that could have seen the fact being validated. The task-shaped-goal precedent does not
transfer — that generator *can* emit a passing goal and merely sometimes doesn't. Threading the fact
is therefore not an alternative to the rule; it is what makes the rule satisfiable rather than a
permanent rejection.

Owners rather than a bare boolean, because a boolean would have made the rule satisfiable while
leaving the mechanical root — slots filled from the agent list alone — in place.

### 6. Rejected at the call as well as at the gate

Via the `check` seam from ADR-043, active only when there are no routine owners. The gate closes the
class and covers hand-authored bundles; the call check turns a discarded run into one re-sampled
leaf. Unlike ADR-043's case, the call check only became *meaningful* once the generator could see the
fact.

### 7. An advisory for the design consequence, never blocking

A bundle emitting no routine produces one warning through the existing `warn` sink: no routine is
emitted, so no agent has a trigger from this bundle. It reports and does not grade.

It deliberately does **not** say the agents are inert. `heartbeatEnabled` is a brief-only field,
unset by default, so the bundle asserts nothing about heartbeats and the stronger claim would be
false.

## Rejected

**Making the operations prose authoritative over emitted routines.** Dead: routines derive from task
recurrence and ADR-038 holds that stated schedules bind only through a machine channel. Prose cannot
produce a cron; this branch inverts the ADR.

**Suppressing or rewriting the routine language at render time.** Post-hoc correction of generated
prose — the run would succeed, the operator would see nothing, and the document would differ from
what the generator produced. Same family as the repair prohibited in ADR-043, and it would silently
contradict V-idle by editing a field V-idle validates.

## Consequences

- A zero-cadence brief now generates a coherent bundle instead of one whose every agent waits on a
  phantom schedule. Any bundle produced before this change from a brief with no recurring work
  carries the defect and should be regenerated.
- The shared test fixture carried the defect (`routine_slots` populated on a bundle whose only task
  had no cadence) and was corrected to what that bundle actually is. The rule found its first
  instance inside the test suite.
- V-idle was verified to require no schedule wording before this was designed — only that
  `in_progress` is not used as a liveness marker — so a zero-routine protocol is expressible. Had it
  required the wording, the prompt branch and V-idle would have been in direct conflict and this
  feature would have been impossible as specified.
- `generate_operations` grows one argument. Callers passing nothing keep the previous behaviour
  exactly, and the with-routines prompt is byte-identical to its pre-change text.
