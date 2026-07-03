# ADR-023: Attach built-in Paperclip skills to agents by role

## Status

Accepted

## Date

2026-07-03

## Context

The generator synthesizes a `skills/<slug>/SKILL.md` for every skill it invents and
wires each agent's `skills:` list to those generated files. But a Paperclip instance
already ships a catalog of **built-in** skills that every imported company has, and an
agent needs the role-appropriate ones to actually function — the control plane
(`paperclip`: tasks, coordination, governance) and durable cross-wake memory
(`para-memory-files`) at minimum. Generated bundles never referenced these, so an
imported agent had no handle on the platform capabilities it was expected to use.

Built-ins are resolved by slug against the instance catalog, not carried in the bundle.
So they must appear in an agent's skill list (→ `skills:` frontmatter today, and
`.paperclip.yaml` `desiredSkills` once skill attachment lands — ADR-020, parked) but must
**not** get a generated `SKILL.md`, and the bundle's skill-closure checks must treat their
slugs as resolvable without one.

A separate friction point: the S13 anti-filesystem check (ADR-022) listed
`para-memory-files` as a filesystem-read marker, because the pre-010 prose named that
skill while assuming a company-root memory tree. Declaring `para-memory-files` as a
legitimate skill slug now collides with that marker.

## Decision

Introduce a single-source registry and role rule in `patterns/builtins.py`
(`BUILTIN_SKILLS` plus `builtin_skills_for` / `attach_builtin_skills`), and apply it after
the org is planned (reportsTo — and thus CEO/lead roles — fixed) and custom skills are
assigned:

- **All agents** get `paperclip` and `para-memory-files`.
- **CEO + any lead** (an agent with ≥1 direct report) also get
  `paperclip-converting-plans-to-tasks`.
- **CEO only** (org root / `role: ceo`) also gets `paperclip-create-agent`.
- **Never auto-attached:** `paperclip-board` (the human board member's skill) and
  `paperclip-dev` (operator / instance ops). They remain recognized built-ins so a
  hand-authored reference still resolves without a SKILL.md.

Built-ins are appended after an agent's existing custom skills (so `skills[0]` stays the
primary custom skill, which the single-agent path reads) and de-duplicated, so a built-in
already listed by the org planner is not doubled.

Built-ins get **no** `SKILL.md`. The single exclusion point is `OrgPlan.skill_slugs`
(the set that drives skill-generation fan-out), which now filters out `BUILTIN_SKILLS`;
because a built-in never becomes a `SkillDefinition`, the renderer never creates a
`skills/<builtin>/` directory. Every skill-closure check treats a built-in slug as valid
without a bundle file: the `CompanyConfig` model validator, the `I5` integrity check, and
the legacy `structural_check`.

Finally, `para-memory-files` is removed from the S13 filesystem-read marker set — it is
now a skill slug, not filesystem prose. The memory-path prose S13 guards against is still
caught by the `Own memory` / `memory/<date>` markers.

## Consequences

### Positive consequences
- Imported agents declare the platform capabilities their role needs, with no operator
  hand-editing.
- One registry and one role rule; the "no SKILL.md for built-ins" invariant has a single
  enforcement point (`OrgPlan.skill_slugs`).
- Closure checks stay honest — they still catch a genuinely dangling custom skill, while
  accepting instance-provided built-ins.

### Negative consequences
- The role→built-in mapping is hard-coded to the current Paperclip catalog; a new built-in
  or a renamed slug needs a registry edit.
- The generator now assumes these built-in slugs exist on the target instance; a
  non-standard instance missing one would surface only at import/runtime.

### Neutral consequences
- A single-agent bundle's lone agent is the org root, so it declares the full CEO built-in
  set even though it has no reports — consistent with "CEO = org root".
- Built-ins inflate each agent's `skills:` list but add no bundle files.

## Alternatives considered

- **Generate a SKILL.md for built-ins too.** Rejected: it spends credits to produce a
  weaker, unmaintained copy of a vetted platform skill, and would drift from the instance
  catalog (cf. ADR-019).
- **Attach built-ins during rendering rather than after planning.** Rejected: role
  (CEO/lead) is an org-structure fact; computing it once at plan time, where reportsTo is
  authoritative, keeps the rule pure and testable and lets the skills flow through the
  existing stub → `AgentDefinition` path unchanged.
- **Keep `para-memory-files` as an S13 marker and special-case the skills list.** Rejected:
  the slug is now a first-class skill reference; the memory-path prose S13 targets is
  already covered by the other markers.

## References

- `src/paperclip_blueprints/patterns/builtins.py` — the registry and role rule
- `src/paperclip_blueprints/models/org_plan.py` — `skill_slugs` built-in exclusion
- `src/paperclip_blueprints/renderers/bundle.py` — attachment in both pipelines
- `src/paperclip_blueprints/models/output.py`, `validators/integrity.py` — closure
- ADR-022 (object model; S13), ADR-020 (skill attachment / `desiredSkills`, parked),
  ADR-019 (reuse ecosystem commodity skills)
