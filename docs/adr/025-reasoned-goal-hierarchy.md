# ADR-025: Emit a reasoned goal hierarchy (structured goals with per-agent owners)

## Status

Accepted

## Date

2026-07-05

## Context

The generator emits company goals as a flat list of strings (COMPANY.md frontmatter
`goals:`). A deployer reading that can only create the goals flat, all at company level and
all CEO-owned. But a well-formed agent company is a **north-star → sub-goals tree with
per-agent owners**: the single north star is the company's root outcome, and each goal is
an outcome some specific agent is accountable for.

Generation is the only stage that knows **both** the north star (from identity) **and**
which agent owns which outcome (from the org it just designed), so building the hierarchy
is a generation responsibility — and it must be **reasoned** from the org graph, not
mechanical. The deployer's native-Goal API (documented as D4 in the local gap reference)
takes exactly `title`, `description`, `level`, `parentId`, `ownerAgentId`; the generator
should emit goals in that shape so the deployer can create a real tree.

An ordering wrinkle makes this non-trivial: identity generation (which produces the goals)
runs **first**, before any agent exists, so goals cannot be owned at that point. Owner
reasoning needs `AgentDefinition.mandate`, which only exists after the per-agent fan-out.

## Decision

### Reasoning model

- The brief's single **north star → the root goal**, owned by the org root (CEO), at
  company level.
- Each **brief goal → a sub-goal** nested under the north star, owned by the agent whose
  mandate makes it accountable for that outcome (reasoned from the org just designed), at
  agent (or team) level.
- A goal stays **company-level / CEO-owned only** where it is genuinely cross-cutting with
  no single accountable agent, or the company is too small for role separation. The rule is
  "nest with reasoned ownership; default company-level only when no single agent owns it,"
  not "always nest."
- **Single-agent company:** the lone agent is root/CEO; goals stay company-level owned by
  it, nested under the root — no orphan, no second root.

### Ordering

The goal-hierarchy step is a new **post-fan-out** step, sequenced alongside
`generate_operations` (which already runs last because it needs the agent list). It runs
after the agents are generated so it can read their mandates. It is sequenced **before**
operations so operations remains the final call (it echoes the whole company). The LLM
decides only *owner* + *level* per goal; the tree shape (single root, each goal nested under
it) is built **deterministically** in the generator, and a deterministic fallback
(north-star → root; anything ambiguous or a single-agent company → company-level/CEO) means
a flaky or absent model can never yield an orphan or a second root. A single-agent company
skips the LLM entirely.

### Carrier

Emit the structured hierarchy as an **additive block in COMPANY.md frontmatter under
`metadata.paperclip.goalHierarchy`**, and **preserve the flat `goals:` list** for
backward-compat. Each entry carries `slug` (the goal id → deployer `parentId`/self),
`title`, `description`, `level`, `parent` (parent goal slug → `parentId`, `null` for root),
`owner` (agent slug → `ownerAgentId`). The structured form is primary/additive; a bundle
with only the flat list still validates.

### Validators (hard failures)

Per "LLM creativity can't overrule structural rules," a malformed hierarchy is rejected, not
silently passed: `GoalHierarchy` enforces exactly one root, unique slugs, resolvable and
acyclic parents; `CompanyConfig` and the bundle validator (`I14`) additionally require every
`owner` to resolve to a real agent in the org. The flat form continues to validate on its
own.

## Consequences

### Positive consequences
- The deployer can create a real goal tree with per-agent owners instead of a flat,
  all-CEO list — this is the generator-side prerequisite for native-Goal creation (D4).
- Ownership is reasoned from the org the generator actually designed, at the one stage that
  knows both the north star and the mandates.
- The tree is structurally valid by construction; the model only influences owner/level, so
  a bad or missing call degrades gracefully rather than corrupting the bundle.

### Negative consequences
- One more Sonnet call per full multi-agent generation (skipped for single-agent).
- Owner assignment is best-effort reasoning; a mis-assignment is possible but always a
  *valid* owner (validated), never a structural break.

### Neutral consequences
- `title`/`description` are currently derived from the goal text (deterministic); richer
  per-goal copy could be generated later without changing the carrier.
- COMPANY.md goals do not survive Paperclip import (ADR-022); the structured block is read by
  the deployer, which reconciles it into native Goals — this ADR is the emit side only.

## Alternatives considered

- **Carrier: a dedicated file (e.g. `GOALS.md`).** Rejected: adds a file to the bundle
  contract and a second place company data lives; goals are company identity and belong with
  COMPANY.md, which the deployer already parses.
- **Carrier: a `.paperclip.yaml` block.** Rejected: `.paperclip.yaml` is the runtime/import
  config (sidebar, agents, projects, routines); company goal *content* is identity, not
  runtime config, and COMPANY.md frontmatter is where such structured company data already
  lives.
- **Reason ownership during identity generation (keep it one step).** Rejected: impossible —
  the org does not exist yet, so there is no agent to own a goal and no mandate to reason
  from. The step must run after the fan-out.
- **Let the LLM emit the whole tree (parents included).** Rejected: it could produce two
  roots or dangling parents. Building the tree deterministically and having the LLM decide
  only owner/level removes that failure mode.

## References

- `src/paperclip_blueprints/models/goal.py` — `GoalDefinition` + `GoalHierarchy`
- `src/paperclip_blueprints/generators/goal_hierarchy.py`,
  `prompts/goal_hierarchy_generator.md` — the reasoning step + fallback
- `src/paperclip_blueprints/renderers/render.py` — the `metadata.paperclip.goalHierarchy` carrier
- `src/paperclip_blueprints/models/output.py`, `validators/integrity.py` (`I14`) — owner closure
- ADR-022 (goals don't survive import; carried for the deployer), local gap reference D4
  (native-Goal API field set)
