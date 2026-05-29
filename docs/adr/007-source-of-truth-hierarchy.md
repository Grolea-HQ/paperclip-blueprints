# ADR-007: Source-of-truth hierarchy for Paperclip + agentcompanies knowledge

## Status

Accepted

## Date

2026-05-29

## Context

The tool encodes knowledge about Paperclip and the `agentcompanies/v1` package
format in its prompts, templates, and validators. That knowledge has several
candidate sources, and during a grill-with-docs review they were found to
*collide* on concrete details:

- The Paperclip product is open source (`github.com/paperclipai/paperclip`, MIT).
  Its `companies-spec.md` lists `slug` as a **required** COMPANY.md frontmatter
  field and shows a minimal AGENTS.md frontmatter (`name/title/reportsTo/skills`).
- The local reference companies in `examples/reference-companies/` (the canonical
  "what good looks like" per ADR-002) **omit** `slug` from COMPANY.md frontmatter,
  carry `tags`, `metadata.paperclip.{tone,mono}`, and `metadata.sources`, and use
  a richer AGENTS.md structure (Mandate / Decision rights / Escalation).
- The `paperclip.community` guides describe concepts (governance spectrum,
  goal-as-outcome) qualitatively, sometimes without the numeric or token-level
  specifics the implementation needs.
- A rendered fetch of the docs site mis-reported approval tokens (`hireagent` vs
  `hire_agent`) — a render artifact, not ground truth.

Without an explicit precedence rule, the generator silently drifts toward
whichever source was read last, and reviews waste time re-litigating which source
"wins" (e.g. the `slug` question, the `metadata.sources` question).

## Decision

Adopt an explicit source-of-truth hierarchy. When sources collide on a concrete
detail, the **higher** tier wins:

1. **`paperclip.ing/docs`** — the official product docs. Authoritative; overrides
   the community guides where they collide.
2. **`paperclip.community`** — community canon: the conceptual guides and the
   blessed example companies they describe. The local
   `examples/reference-companies/` are treated as community-blessed canonical
   examples (per ADR-002), and are the **example oracle** for bundle *shape*.
3. **`github.com/paperclipai/paperclip`** — the source repository. A **secondary
   oracle** for verifying machine-level facts the higher tiers leave ambiguous
   (e.g. the exact `APPROVAL_TYPES` enum), but it does **not** override the
   community-blessed reference shape for bundle authoring.
4. Everything else (rendered SPA fetches, third-party summaries) — non-authoritative;
   use only to locate the tiers above, never to settle a detail.

ADR-002 stands: the local reference companies remain the structural oracle for the
output bundle. This ADR does **not** supersede it. Where the repo's minimal
`companies-spec.md` disagrees with the reference companies on bundle shape (e.g.
`slug` in COMPANY.md frontmatter), the reference companies win.

This ADR authorizes adding the three external sources above to CLAUDE.md's
"Reference materials" section.

## Consequences

### Positive consequences
- Collisions resolve by rule, not by re-argument. The `slug`, `metadata.sources`,
  and approval-token questions have one answer each.
- The repo becomes a sanctioned place to verify machine facts (enums, schema)
  without it quietly overriding the reference-driven bundle shape.

### Negative consequences
- If the official docs / community canon and the running importer ever diverge in
  practice, a generated bundle could pass our checks yet fail import. T052 (real
  import) remains the backstop that catches that.

### Neutral consequences
- Approval-type tokens are now verified (`hire_agent`, `approve_ceo_strategy`,
  `budget_override_required`, `request_board_approval`) and recorded in CONTEXT.md,
  even though the v0.1a bundle expresses decision rights in prose and never emits
  the tokens.

## Alternatives considered

- **Make the repo's `agentcompanies/v1` spec authoritative (supersede ADR-002).**
  Rejected: the reference companies are community-blessed canonical examples, not
  drift; realigning the generator to the minimal repo spec would change the output
  contract for no validated benefit and contradict ADR-002.
- **No explicit hierarchy, decide case by case.** Rejected: that is exactly what
  produced the repeated re-litigation this ADR removes.

## References

- ADR-002 (output bundle format — the reference companies as structural oracle)
- `github.com/paperclipai/paperclip` — `packages/shared/src/constants.ts`
  (`APPROVAL_TYPES`), `.agents/skills/company-creator/references/companies-spec.md`
- `paperclip.ing/docs`, `paperclip.community`, `agentcompanies.io/specification`
- `CONTEXT.md` — verified approval tokens and `agentcompanies/v1` notes
