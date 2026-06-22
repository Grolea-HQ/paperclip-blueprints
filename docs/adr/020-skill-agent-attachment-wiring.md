# ADR-020: Skill→agent attachment wiring (attachment is not automatic on import)

## Status

Accepted

## Date

2026-06-22

> Sequenced **before** ADR-019 (commodity-skill reuse). ADR-019's referenced-skill path
> builds on the attach-instruction emitter defined here. This ADR fixes a live correctness
> defect in every bundle the tool currently ships and has no dependency on the built-in
> catalogue.

## Context

A generated bundle declares each agent's skills in `AGENTS.md` frontmatter
(`skills: [slug]`), and the closure validator I5 guarantees every declared slug resolves to
a `skills/<slug>/SKILL.md`. The tool has, until now, assumed that importing the bundle wires
those declarations into actual agent attachments.

**That assumption is false, confirmed firsthand on a healthy instance.** When a generated
bundle is imported through the UI company-import flow, its skills land in the **company
library** but every one shows **"0 agents / No agents attached."** The `AGENTS.md skills:`
frontmatter does **not** drive agent attachment on import. (This surfaced importing the
Prospector bundle; the operator's production company had its skills hand-attached, which is
what caused the earlier audience/persona drift.) The earlier MUST-2 conclusion (issue #2,
"attachment already wires on import — no rebuild needed") was wrong and has been reopened and
corrected.

Two consequences define the scope:

1. **It is a present defect in all current output.** Every bundle we ship today emits
   `skills:` attachments that silently do not take effect on import. Fixing it is correctness
   work on the existing baseline, not a new feature.
2. **It is broader than ADR-019.** It applies to **every** bundle skill — the
   embedded/synthesized ones too, not only referenced catalogue skills. It therefore must not
   inherit ADR-019's stable-instance catalogue gate (finding 1: `listCatalogSkills` returned
   500s on self-hosted npm, fixed on @canary, not yet stable). Embedded-skill attachment is
   independent of the catalogue and shippable now.

## Decision

The tool owns **skill→agent attachment wiring**, across the board, for every skill in the
bundle.

### Source of truth — `AGENTS.md skills:` stays

`AGENTS.md skills: [slug]` remains the portable, declarative statement of *intended*
attachments (ADR-015: portable — it means the same thing on every instance). We do not remove
it. We add the missing step: turning that intent into actionable wiring, because import does
not.

### v0.1 — a deterministic per-agent attach-instruction emitter

Read each agent's `AGENTS.md skills:` list and emit explicit, per-agent attachment
instructions — "attach skill `X` to agent `Y`" — into `OPERATIONS.md` (and surfaced in
`SETUP`/`README` as appropriate), so after import the operator can run or click them and the
library skills actually attach. The emitter is a pure, deterministic function of the bundle
(mirroring the `renderers/` pattern), and is fully **offline-testable** — no live API.

### v0.2 — deployer attaches via the skills API

The deployer attaches via `POST /api/agents/{id}/skills/sync` (`desiredSkills`), or
`desiredSkills` at hire. This is **folded with ADR-019 Spec B (referenced-skill install) into
one v0.2 deployer-skills spec**, since both hit the `/skills/sync` surface.

### Layering with ADR-019 — extend the emitter, never duplicate it

This ADR owns the attach emitter ("attach skill X to agent Y"). ADR-019's referenced-skill
path **extends** it with an install prefix ("install skill X from source S, then attach to
agent Y"); reuse **calls** this emitter rather than re-implementing it. The dependency is to
be stated explicitly in both specs, so there is exactly one attach-instruction emitter and no
duplication.

### Referenced catalogue skills need both steps

For a referenced catalogue/skills.sh skill, the operator/deployer must **both** install the
skill into the company library **and** attach it per agent — neither is automatic from import.
(This also answers ADR-019 verify item #1: attachment is not automatic by slug for any skill.)

## Consequences

### Positive
- Corrects a silent defect in every bundle currently shipped — declared skills become
  actually-attached skills.
- Operator gets concrete, runnable attach steps instead of a bundle that looks wired but
  isn't.
- Establishes the single attach-instruction emitter that ADR-019's referenced path extends.
- v0.1 has no API or catalogue dependency, so it ships independent of the finding-1 gate.

### Negative / limitations
- v0.1 leaves attachment as an operator step (run the emitted instructions) until the v0.2
  deployer closes it automatically.
- The emitter must stay in lockstep with `AGENTS.md skills:`; a spec-level closure check
  (every declared attachment appears in the emitted instructions) is warranted.

### Neutral
- No change to how skills are synthesized or to the `skills:` frontmatter itself.

## Explicitly deferred

- **v0.2 deployer attach via `/skills/sync`** — folded with ADR-019 Spec B (referenced-skill
  install) into one v0.2 deployer-skills spec.

## Alternatives considered

- **Assume import wires attachments (status quo).** Rejected — factually false; it is the bug
  this ADR fixes.
- **Fold attachment into ADR-019's reference-mechanism spec.** Rejected — attachment is
  broader (all skills, embedded + referenced), is a present defect, carries no catalogue gate,
  and is the foundation reuse depends on; coupling would either delay the defect fix or drag
  the gated reuse feature forward.
- **Drop `skills:` from `AGENTS.md` and only emit instructions.** Rejected — `skills:` is the
  portable attachment intent and the exact source the emitter reads.

## References

- ADR-019 (commodity-skill reuse — builds on this emitter), ADR-015 (portability — attachment
  *intent* in `AGENTS.md` is portable; the *act* of attaching is operator/deployer-side),
  ADR-009 (in-stack validator — I5 closure), ADR-002 (bundle format)
- Issue #2 (MUST-2, reopened and corrected: skills do not auto-attach on import)
- Live findings: (1) `listCatalogSkills` 500 on self-hosted npm, fixed @canary — gates
  ADR-019 referencing, not this; (2) imported skills show "0 agents attached" — this ADR
- Current wiring: `prompts/org_planner.md` (skill slug assignment), `renderers/render.py`
  (`AGENTS.md skills:` emission), `validators/integrity.py` (I5),
  `templates/operations_md.j2` / `tools_md.j2` (where attach instructions surface)
