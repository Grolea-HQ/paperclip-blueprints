# Phase 0 Research: Per-agent run-policy override from the brief

All decisions are deterministic-carrier decisions. None involve model behavior or value-choosing —
the recurring constraint is that the feature transports what the operator wrote and invents nothing.

## D1 — Layering mechanics over the role-derived base (ADR-027)

**Decision**: The role rule (`derive_run_policy`) remains the base and is emitted for every agent
exactly as today. A brief override substitutes values **per agent and per field**: if the brief
states `maxTurnsPerRun` for an agent, only that agent's turns value changes; concurrency keeps its
role-derived value unless the brief also states it. The merge is a field-level overlay, not a
whole-object replacement.

**Rationale**: Matches the spec's "override the role-derived value for that agent and field"
(FR-003) and field independence (FR-004). Keeps backward-compat trivially true: with no overrides,
the overlay is empty and output is byte-identical (FR-006, SC-002). Mirrors how
`parse_model_preferences` overlays only the *model* onto the role-default `AdapterChoice`.

**Alternatives considered**:
- *Replace the whole role-derived `RunPolicy` when any field is stated.* Rejected: violates field
  independence — stating turns would wipe the role-derived concurrency.
- *Remove the role rule and emit only brief-stated values (supersede ADR-027).* Rejected: this was
  the explicit fork decision — the operator chose "layer on top," keeping ADR-027 as the base.

## D2 — Where the heartbeat toggle lives, and why it differs from the other two fields

**Decision**: `heartbeat_enabled` is a new, **brief-only** field with no role heuristic. It is
`None` (absent) unless the brief states it, and is emitted into the carrier only when set. Turns and
concurrency, by contrast, always have a role-derived base value.

**Rationale**: FR-005 / SC-004 — a heartbeat signal must appear only for agents the operator
explicitly toggles, and for zero agents otherwise. There is no base heartbeat value to carry, so
`None` must be representable and must render nothing. Making it a tri-state (`None` / `True` /
`False`) keeps "off" distinct from "unstated."

**Alternatives considered**:
- *Default heartbeat to enabled and always emit it.* Rejected: that is an inferred default (a value
  the operator did not state), which FR-007 forbids, and it would change today's output (breaks
  SC-002).

## D3 — Brief line grammar

**Decision**: Run-policy overrides live in a new optional input-template section as free-text
lines, one override per line, in the form:

```
<agent reference>: <clause>[, <clause>]...
```

where `<clause>` is one of (case-insensitive, tolerant of hyphen/space):
- `max turns <N>` (aliases: `turns`, `max-turns`) — `N` a positive integer
- `max concurrent <N>` (aliases: `concurrent`, `max-concurrent`, `concurrency`) — `N` a positive integer
- `heartbeat <on|off>` (aliases for on: `on`, `enabled`, `true`; for off: `off`, `disabled`, `false`)

`<agent reference>` is the text left of the first colon; it is slugified and boundary-matched to an
agent's slug / title-slug / name-slug — the **same matcher** `parse_model_preferences` uses, so an
operator names agents the way they already do for adapter preferences (FR-002).

**Rationale**: Adapter preferences carry a single tier keyword and can slugify the whole line;
run-policy carries three typed values, so it needs a reference-vs-values separator. A leading
`reference:` colon is the least surprising delimiter and keeps the reference matcher reusable
verbatim on the left side. Keyword clauses (not positional) keep partial statements natural (an
operator can give just `heartbeat off`).

**Alternatives considered**:
- *Reuse the whole-line slug match like adapter, with values as trailing keywords.* Rejected:
  ambiguous — a bare integer in a slugified line can't be attributed to turns vs concurrency.
- *A structured YAML/JSON block in the brief.* Rejected: the brief is prose-shaped Markdown
  (ADR-003); a structured block breaks the input-template idiom the parser is built around.

## D4 — Split of validation: syntactic (error) vs semantic (warning)

**Decision**:
- **Syntactic** faults are rejected at **brief-validation time** (`BriefValidationError`, before any
  generation): a non-positive / non-integer turns or concurrency value; an unrecognized clause
  keyword; an unrecognized heartbeat state; the **same agent reference** stated twice with
  conflicting values for a field. These need no knowledge of the generated agents.
- **Semantic** faults are **advisory warnings** at render time via the existing `warn` sink: a
  reference that matches **no** generated agent (FR-009), mirroring the adapter unmatched-preference
  warning. Generation proceeds; no value is emitted for a non-existent agent.

**Rationale**: The brief is validated before the (expensive) generation runs; catching malformed
*values* there is cheap and honors "no malformed value reaches the bundle" (FR-010, SC-005). But
whether a reference matches an agent depends on the *generated* org, which doesn't exist at brief-
parse time — so unmatched is necessarily a render-time concern, and the established precedent
(adapter) already treats it as a non-blocking warning, not an error (an org can legitimately differ
from what the operator guessed).

**Edge — two distinct references collide onto one agent with conflicting field values**: detectable
only at match time. Handled deterministically: apply field overlays in brief line order; if a later
matched line sets a field a different earlier-matched line already set to a different value for the
same agent, emit a render-time warning naming the agent and field, and take the last write (stable,
order-defined). This keeps determinism (FR-008) without failing the whole run on an ambiguity the
operator may have intended (broad reference + a specific one).

## D5 — Carrier key and shape

**Decision**: Emit under each agent's existing `.paperclip.yaml` `runPolicy` block:

```yaml
runPolicy:
  maxTurnsPerRun: <int>        # role-derived, or brief override
  maxConcurrentRuns: <int>     # role-derived, or brief override
  heartbeatEnabled: <bool>     # ONLY when the brief states it; omitted otherwise
```

The deployer maps `heartbeatEnabled` to its runtime heartbeat setting (private-repo, out of scope,
FR-012), just as it already maps `maxTurnsPerRun` / `maxConcurrentRuns` (ADR-027).

**Rationale**: One carrier for one per-agent concern (FR-011); additive to a block the validators
already accept. `heartbeatEnabled` is a clear boolean name consistent with the existing camelCase
keys.

**Alternatives considered**:
- *A separate top-level `heartbeat:` block.* Rejected: splits one per-agent concern across two
  blocks; ADR-027 already argued for a single `runPolicy` block.

## D6 — No new dependency, no schema churn

**Decision**: Pure Python over existing libraries; no `pyproject.toml` change. The schema-shape
validator is extended (not loosened) to assert `heartbeatEnabled`, when present, is a boolean, so a
malformed emission is caught in-process before write (Constitution II).

**Rationale**: Constitution "adding a dependency requires operator approval"; none is needed. The
validator addition is a tightening, consistent with the NON-NEGOTIABLE schema-validity principle.
