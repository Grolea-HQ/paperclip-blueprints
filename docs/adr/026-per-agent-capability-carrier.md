# ADR-026: Emit a structured per-agent capability set

## Status

Accepted

## Date

2026-07-05

## Context

A generated bundle carries no structured per-agent capability signal. The deployer's
per-agent capability step (D7 in the local gap reference) applies only explicitly-declared
capabilities and deliberately does not force-derive them from prose or role — so with the
bundle silent, D7 is a no-op for every agent. But some roles genuinely need a platform
capability their role requires: a scanner/research role needs read-only web access to fetch
external pages; a CEO or editor does not. Generation is where the role and mandate are
known, so deriving that capability set is a generation responsibility, and the bundle should
carry it in a structured form D7 already knows how to consume.

A capability grant is a permission decision, so the derivation must not over-grant. That
rules out a free-reasoning LLM (which could hand out capabilities a role does not need) and
argues for a conservative, auditable rule.

## Decision

### Derivation (deterministic, conservative)

Add `derive_capabilities(role, title, mandate)` in `patterns/capabilities.py` — a
**deterministic** keyword-reasoned mapping over the agent's role/title/mandate, applied to
the generated agents after the per-agent fan-out (where the mandate exists), via
`attach_capabilities`. A role/title/mandate that signals external web-information gathering
(whole-word signals: `web`, `scan`/`scanner`, `research`, `prospect`, `discover`,
`source`/`sourcing`, `scrape`, `crawl`, `online`, `url`, …) is granted `web-fetch`
(read-only external web access). Everything else gets nothing.

Conservative by default: grant only what the role genuinely needs, no blanket capabilities,
and when in doubt grant nothing (an empty set → D7 no-op for that agent). Word-boundary
matching keeps `resource`/`outsource` from tripping `source`. Choosing a rule over an LLM
applies the project's "LLM creativity can't overrule structural rules" principle to access
control — the grant is inspectable and stable, not model-dependent.

### Carrier

Emit the set as a structured **`capabilities:` list in each agent's AGENTS.md frontmatter**,
alongside `skills:` — the same per-agent frontmatter the deployer already parses (the skill
list travels there too). The field is a flow sequence (`[web-fetch]`, or `[]` when none).
`AgentDefinition.capabilities` defaults to empty, so the change is additive and a bundle
without it still validates; each entry must be a known capability slug
(`KNOWN_CAPABILITIES`), rejected otherwise.

## Consequences

### Positive consequences
- D7 has a real per-agent capability signal to act on; a scanner role deploys with the web
  access it needs, without the operator hand-granting it.
- Grants are conservative and auditable — a keyword rule, not an LLM, so no over-grant and
  no per-agent LLM cost.
- Additive and backward-compatible: existing bundles/agents keep working with an empty set.

### Negative consequences
- The role→capability mapping and the capability vocabulary are hard-coded; a new capability
  or signal needs a code edit.
- Keyword derivation can miss a role that phrases its web need unusually (false negative) —
  acceptable, since the conservative bias is deliberate and the operator can still grant
  explicitly.

### Neutral consequences
- Only `web-fetch` is derived today; the registry (`KNOWN_CAPABILITIES`) is open for more.
- `capabilities: []` now renders on every agent's AGENTS.md — explicit and consistent for
  the deployer, at the cost of one extra frontmatter line per agent.

## Alternatives considered

- **Derive capabilities with an LLM reasoning step.** Rejected: a permission grant must not
  be model-improvised; an LLM risks over-granting, which is exactly what "conservative, when
  in doubt omit" forbids. A deterministic rule is auditable and stable.
- **Carry capabilities in a `.paperclip.yaml` per-agent block.** Rejected: per-agent
  structured signals (skills) already live in AGENTS.md frontmatter, which the deployer
  parses; keeping capabilities next to skills is consistent and avoids splitting per-agent
  data across two files.
- **Grant a broad default capability set.** Rejected: blanket capabilities violate least
  privilege; grant only what the role genuinely needs.

## References

- `src/paperclip_blueprints/patterns/capabilities.py` — the registry + derivation
- `src/paperclip_blueprints/models/agent.py` — the `capabilities` field + known-slug validator
- `src/paperclip_blueprints/renderers/render.py` — the AGENTS.md frontmatter carrier
- `src/paperclip_blueprints/renderers/bundle.py` — attachment in both pipelines
- local gap reference D7 (per-agent tool/capability API), ADR-023 (built-in skills; the
  analogous per-agent, deterministic, leaf-module pattern)
