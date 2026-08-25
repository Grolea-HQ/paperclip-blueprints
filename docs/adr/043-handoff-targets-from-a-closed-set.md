# ADR-043 — Handoff targets are drawn from a closed set, and never repaired

**Status:** Accepted
**Date:** 2026-08-23
**Relates to:** ADR-014 (resilient JSON generation — the retry this builds on), ADR-004 (prompt
architecture), ADR-013 (import fidelity — where validator I8 comes from)

---

## Context

A generation run was rejected by validator I8 because one agent's `AGENTS.md` named a handoff to
`qa-led` where the agent is `qa-lead`. One character, one line. Everything else in the bundle was
correct, including that same agent named correctly in `.paperclip.yaml`, `OPERATIONS.md`, a project
owner, a task assignee, and twice more in the same file.

The validator worked. The problem was where it worked: after roughly eighty model calls had been
paid for, rejecting the whole run for a value whose legal set was fully known before the call was
made.

The generator receives the org plan before it writes anything, so the set of agent slugs is closed
and known at prompt time. Every other agent-slug field already respects that — a project's `owner`
and a task's `assignee` are taken from the planner stub, never authored by the model. Handoffs were
the sole remaining place where a known-set value was written as free text, inside a sentence
(`"qa-lead — ships the release"`), and they are the only place this failure has ever come from.

## Decision

### 1. The wire shape splits the target from the prose

`receives_from` and `hands_to` are requested as arrays of `{"agent": …, "flow": …}` and rejoined to
today's `"<slug> — <flow>"` before `AgentDefinition` is built. Templates, renderers and I8 see
exactly what they saw before.

The split is not cosmetic — it is the precondition for any schema-level constraint existing at all.
A joined string can only be constrained by `pattern`, which the structured-output dialect does not
support and which `_strict_node` strips. Split out, the target is a field that carries an `enum`,
which the dialect does support.

### 2. The legal set is every agent but self — matching validator I8 exactly

Not the narrower "manager, direct reports and peers" set the prompt describes in prose.

Two checks over the same value with different populations is a defect generator. Enforcing the
narrow set would make generation stricter than validation: a legitimate cross-branch handoff would be
rejected at generation while passing I8 and everything downstream of it. That is the same divergence
this work exists to remove, pointed the other way, and someone would have to keep the two sets in
step forever. The adjacent-set preference stays in the prompt as guidance, which is what it
effectively already was.

**The adjacent set is rejected on scope, not merit** — enforcing span-of-control on handoffs is a
defensible thing to want. But the rule would then have to hold in *both* places, so it is a new
shared definition of adjacency applied by the generator and by a bundle-level check, with one
implementation governing both. That is a span-of-control feature with its own spec, not an `enum`
narrowed on one call. Anyone proposing it as a small amendment to this decision has mistaken its
size.

### 3. Both the constraint and the check exist, and neither may be removed

This is the part most at risk of being "simplified" later, so the reasoning is recorded rather than
left to be rediscovered.

The schema constraint makes the near-miss *unavailable to the model*, which is the only thing that
prevents the failure rather than detecting it. But it binds only when the model accepts a
constrained-output request. `STRUCTURAL_MODEL` is `claude-sonnet-4-6`, which does not appear in the
documented support list for structured output, and `complete_json` responds to a declined schema by
dropping it and retrying unconstrained (ADR-014) — silently, by design, so that an unsupported model
does not abort a run.

A guarantee resting on the schema alone would therefore disappear without any signal, on a model
change nobody made deliberately, and runs would go back to failing at I8 after every call had been
paid for. The membership check is consequently run on every response regardless of whether the schema
was sent, accepted, or dropped.

Removing either one is a real loss: without the constraint there is only detection; without the check
there is no guarantee whenever the constraint does not bind. They are not two mechanisms doing one
job.

### 4. A rejected target is never altered to a valid one

No fuzzy matching, no edit distance, no nearest-neighbour, no "did you mean" — in generation,
rendering or validation. A test asserts the absence of any similarity comparison over agent slugs by
inspection, because a behavioural assertion alone is satisfied by a repair that happens to guess
right on the sampled case.

A repaired near-miss is worse than the failure it replaces: the run succeeds, the operator sees
nothing, and the bundle ships an agent handing work to whichever role the repair guessed. The
pre-existing behaviour was correct about the fact that something was wrong; only its timing was the
defect.

Normalisation before the membership test is limited to whitespace and enclosing backticks —
formatting that cannot carry identity, and what `_handoff_head` already strips. Case folding and
punctuation collapsing are excluded specifically because they *can* map one planned agent onto
another; that is repair wearing normalisation's clothes.

### 5. Rejection is local, and re-samples

The check raises into `complete_json`'s existing retry, so a bad target costs one leaf's attempt
budget instead of a run. The retry feedback carries the check's own message rather than the
hardcoded not-valid-JSON text: the reply *was* valid JSON, and telling the model otherwise sends it
at formatting when the defect is a value.

### 6. Validator I8 is unchanged

It still runs, over the same population. This adds a constraint upstream of it; it does not replace
it. I8 also covers hand-authored bundles, which no generator-side constraint can reach.

## Consequences

- A near-miss costs at most three calls at one agent, against ~80 and a discarded run.
- An empty handoff target is now rejected at the call. It passes I8 today — `_handoff_head` returns
  `""` and the check skips it — which is the same defect class at a different value: a check that
  skips its own input reports clean on the case it exists for. I8 is deliberately left alone; with
  the generator constrained, it can no longer produce that case.
- On the unconstrained path the object wire shape rests on prompt compliance, so a model that
  ignores the instruction spends a re-sample. Accepting the old joined string as a fallback was
  considered and rejected: it would restore free-text slug authoring on exactly the path where the
  schema constrains nothing.
- `complete_json` gains an optional post-parse `check`, available to any future generator with a
  closed-set field. Its four existing callers are unaffected.

## Open

> **Closed 2026-08-24 by ADR-045 — negatively.** `claude-sonnet-4-6` accepts
> `output_config.format` and the constraint binds, verified by an instrumented call through the
> production transport (with a control case proving the probe can report a rejection).
> `strict_json_schema` was never a no-op. The inference below reasoned from a published support
> list, which is evidence about documentation rather than about behaviour. §3 stands unchanged —
> and is now the reason the schema-dropping fallback still degrades safely for a future model
> that does decline the parameter.

Whether `claude-sonnet-4-6` accepts `output_config.format` at all is unresolved and not resolvable
from the test suite, which makes no live calls (Constitution III). If it does not, then
`strict_json_schema` is currently a no-op on every structural generator — a finding wider than this
feature and worth its own investigation. This decision does not depend on the answer, which is the
point of §3.
