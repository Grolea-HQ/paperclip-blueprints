# ADR-034: Layer a brief-driven per-agent run-policy override over the role-derived base

## Status

Accepted

## Date

2026-07-20

## Context

The generator emits a per-agent `runPolicy` block in `.paperclip.yaml` (ADR-027): a role rule
derives `maxTurnsPerRun` and `maxConcurrentRuns` for every agent. The operator has no way to state
run-policy values for a specific agent from the brief — the values are chosen entirely by the role
rule. An agent wake with no bound on turns or concurrency can loop and burn budget before anything
stops it, and an operator who knows a given agent should be tightly bounded (or should never run on
a heartbeat) cannot express that in the brief.

Two established derivations already show how a brief drives a per-agent `.paperclip.yaml` value with
a pure, deterministic renderer: per-agent budgets (ADR-012, `renderers/budget.py`, keyed off
`capital_monthly_eur`) and per-agent model preferences (ADR-017, `renderers/adapter.py`,
`parse_model_preferences` overlaying the brief's stated model onto a role default). ADR-027 itself
anticipated this exact extension: "Add per-company/per-role caps to the operator brief. Deferred …
a brief knob can layer on top later (as ADR-017 layered explicit model preferences over role
defaults)."

Choosing *what values are appropriate* for a role — the enforcement reasoning — is out of scope for
this repository. This feature is a carrier: it transports operator-stated values and infers nothing.

## Decision

Add a brief-driven override that **layers on top of** the ADR-027 role-derived base. ADR-027's role
rule remains the base and is emitted for every agent unchanged; a brief-stated value substitutes for
the role-derived value **per agent and per field**.

1. **New brief channel.** `CompanyBrief.run_policy_preferences: list[str] | None`
   (`models/input.py`), parsed from a new optional input-template section (FR-013), shaped like the
   existing `adapter_preferences` free-text override lines. Each line:
   `<agent reference>: <clause>[, <clause>]...`, where a clause sets `max turns <N>`,
   `max concurrent <N>`, or `heartbeat <on|off>`.

2. **Pure renderer.** `parse_run_policy_preferences(lines, agents)` in `renderers/run_policy.py`
   resolves lines to per-slug `RunPolicyOverride`s using the same boundary-safe reference matcher as
   `parse_model_preferences`. `assign_run_policies(agents, overrides)` overlays each stated field
   onto the role-derived `RunPolicy`; unset fields keep the base. Deterministic, no LLM, no I/O.

3. **Heartbeat is brief-only.** `RunPolicy` gains `heartbeat_enabled: bool | None = None`. There is
   no role heuristic behind it; it is emitted (`runPolicy.heartbeatEnabled`) only when the brief
   states it and is absent otherwise.

4. **No new value-choosing.** This feature adds no default, heuristic, or inference — it emits only
   values the operator stated. Choosing appropriate run-policy values by role/risk/company shape
   stays out of this repository.

5. **Validation split.** Malformed *values* (non-positive/non-integer turns or concurrency,
   unrecognized clause or heartbeat token, a reference given conflicting values for one field) are
   rejected at brief-validation time. A reference matching *no* generated agent is a non-blocking
   render-time warning (the org isn't known at brief-parse time), mirroring the adapter
   unmatched-preference warning.

Scope is the emit/carrier side only. The deployer that consumes `runPolicy` (including mapping
`heartbeatEnabled` to a runtime heartbeat setting) lives in the private repo and is unchanged here.

## Consequences

### Positive consequences

- An operator can bound a specific agent's turns and concurrency, and disable its heartbeat, from
  the brief — directly addressing unbounded wakes that loop and burn budget.
- Backward compatible: a brief with no run-policy values yields byte-identical output to today's
  (`assign_run_policies(agents)` with no overrides equals the current result).
- Consistent with the two existing per-agent brief-driven derivations (budget, model preference):
  same seam, same matcher, same pure-renderer shape — low conceptual surface.
- Value-choosing stays out of the public repo; the carrier only transports what the operator wrote.

### Negative consequences

- Adds a brief channel and grammar (input-template section + parser + validation) that ADR-027 had
  deferred — more input-parsing surface to maintain.
- Two override lines with distinct references can collide onto one agent; resolved by a
  deterministic last-in-order rule plus a warning, which an operator could find surprising.

### Neutral consequences

- `RunPolicy` gains an optional third field; all existing call sites keep the two-key emission
  because the field defaults to `None` and renders nothing.
- The role rule (ADR-027) is untouched — this ADR extends it, it does not supersede it.

### Deviation from the draft contract — cross-reference collision resolves silently

The `contracts/run-policy-override.md` §5 draft specified that when two **distinct** brief lines
overlap on one agent+field, generation emits an advisory collision warning. The implementation
**deliberately does not**: a collision resolves deterministically last-in-line-order with **no
warning**, and the contract §5 has been updated to match.

Rationale: broad-then-specific overlap is a **supported, intentional pattern** — an operator can
write a broad default (`All watchers: max turns 5`) and then a specific exception
(`lead-watcher: max turns 12`) for the same agent. A collision warning would therefore fire on
*correct* usage, training operators to ignore it. The determinism guarantee (FR-008) is unaffected:
the later line wins per field, in stable brief-line order. Recorded here as a decision, not a silent
omission — the unmatched-reference warning (FR-009) is retained because a reference that matches
*no* agent is a likely typo, whereas an overlap on a real agent is not.

## Alternatives considered

- **Supersede ADR-027 — remove the role heuristics, emit only brief-stated values.** Rejected: the
  operator chose to keep the role rule as the base and layer the brief override on top; a
  silent-when-unstated pure carrier would also change today's output (pollers lose their tightened
  turns).
- **Default the heartbeat toggle to enabled and always emit it.** Rejected: that is an inferred
  value the operator did not state (violates the no-inference rule) and would change today's output.
- **Whole-object replacement when any field is stated.** Rejected: breaks field independence —
  stating turns would wipe the role-derived concurrency.
- **A structured YAML block in the brief instead of free-text lines.** Rejected: the brief is
  prose-shaped Markdown (ADR-003); free-text override lines match the established input idiom and
  reuse the adapter reference matcher verbatim.

## References

- `specs/014-run-policy-override/` — spec, plan, research, data-model, contracts, quickstart
- `src/paperclip_blueprints/renderers/run_policy.py` — role base (ADR-027) + this override layer
- `src/paperclip_blueprints/renderers/adapter.py` — `parse_model_preferences`, the boundary-safe
  reference matcher reused here
- `src/paperclip_blueprints/renderers/budget.py` — the per-agent brief-driven derivation precedent
- ADR-027 (role-derived run-policy caps; the base this layers over), ADR-017 (per-agent model
  preference over role default; the layering pattern), ADR-012 (per-agent budget), ADR-003 (brief
  input format)
