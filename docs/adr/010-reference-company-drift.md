# ADR-010: Reference companies are drifting from the live product; observed import behavior is the tie-breaker

## Status

Accepted

## Date

2026-05-31

## Context

ADR-002 makes `examples/reference-companies/` the structural oracle for generated
bundles. ADR-007 ranks sources when they collide: tier 1 `paperclip.ing/docs`,
tier 2 `paperclip.community` + the local reference companies (the example oracle
for bundle *shape*), tier 3 `github.com/paperclipai/paperclip` (source repo —
"secondary oracle for machine-level facts" that "does **not** override the
community-blessed reference shape"). ADR-007 also recorded a negative consequence:
"if the official docs / community canon and the running importer ever diverge in
practice, a generated bundle could pass our checks yet fail import. T052 (real
import) remains the backstop."

Reviewing Paperclip release **v2026.529.0** (skills CLI + catalog + provenance
model) surfaced that this divergence is **no longer hypothetical**. The reference
companies — sanitized snapshots of the product's output — disagree with the
*actual shipped product* (tier 3: source spec, shipped bundled skills, importer
behavior) in at least two concrete places:

1. **Empty CEO role.** The references' CEO carried no `role: ceo`, so the importer
   landed the CEO at `role=agent` with stripped permissions (upstream Issue #1990 /
   PR #1989). v0.1a already deviated from the references (commit `15d1c0a`) to emit
   `role: ceo`, driven by observed import failure — the ADR-007 backstop in action.
2. **SKILL.md frontmatter.** The references carry top-level `schema:
   agentcompanies/v1` and `slug:` on SKILL.md, but the live product treats SKILL.md
   as an **Agent Skills** package: a real shipped bundled skill
   (`skills/paperclip/SKILL.md`) carries only `name` + `description`, and the
   companies spec namespaces Paperclip extras under `metadata.paperclip`. See
   `docs/TODO-v0.1c.md` item 1.

The important nuance: both contradicting sources are **tier 3** (the product source
repo and its runtime), which ADR-007 says should **lose** to the tier-2 references
for bundle shape. Yet tier 3 is precisely what decides whether a bundle imports.
Following ADR-007's letter (references win) in case (1) would have produced a
broken bundle; we already overrode it in practice. Two drift points is a pattern.

## Decision

1. **Make the backstop a precedence rule.** When the reference companies (tier 2)
   demonstrably disagree with **observed importer behavior or an actually-shipped
   product artifact** (tier 3) such that following the references would produce a
   non-importable or non-idiomatic bundle, **tier 3 wins for that detail.** This
   does not invert ADR-007 wholesale — the references remain the default shape
   oracle for everything not contradicted by observed product behavior — it
   promotes ADR-007's "real import is the backstop" from a safety net into an
   explicit tie-breaker, and records the two known overrides (CEO role; SKILL.md
   format).

2. **Schedule a re-sourcing pass for v0.1c**, tracked in `docs/TODO-v0.1c.md`
   item 2: refresh `examples/reference-companies/` from a current
   `paperclip.community/companies` export (or a live v2026.529.0+ instance),
   re-sanitize, and re-derive templates/validators against the refreshed shape,
   auditing which fields changed. Once refreshed, the tier-2 references realign with
   the product and the override list (1) shrinks back toward empty.

3. **No v0.1b change.** v0.1b is complete and verified; both drift items are
   forward-compatibility considerations, not v0.1b defects. The bundles import
   today. Action is deferred to v0.1c.

## Precedent

Known overrides applied under this rule, newest last. Extend this table whenever a
new tier-3-over-tier-2 override is taken, so future overrides have something to
anchor to.

| Detail | Reference (tier 2) said | Live product (tier 3) requires | Override taken | Recorded |
|---|---|---|---|---|
| CEO import role | CEO carried no `role` → imported as `agent` (stripped perms) | first `reportsTo: null` agent is CEO; explicit `role: ceo` is read | emit `role: ceo` in `.paperclip.yaml` for the root | v0.1a, commit `15d1c0a` (Issue #1990 / PR #1989) |
| SKILL.md frontmatter | top-level `schema: agentcompanies/v1` + `slug:` | Agent Skills package — `name` + `description`; slug positional | align generator in v0.1c (deferred; not yet applied) | this v2026.529.0 analysis; `docs/TODO-v0.1c.md` item 1 |

## Consequences

### Positive

- The implicit "we deviated from the references for the CEO role" decision now has
  an explicit rule and a recorded rationale, instead of living only in a commit
  message.
- The reference-staleness risk ADR-007 anticipated is tracked with a concrete
  remediation (re-sourcing) rather than rediscovered each time a bundle fails import.

### Negative

- A second precedence rule adds nuance to ADR-007: "references win, except where
  observed product behavior contradicts them." Slightly more to reason about, but it
  matches what we already do in practice.
- "Observed product behavior" requires actually observing it (a real import or a
  `skills audit`), which is heavier than reading a reference file. That cost is the
  point — it is what catches the drift.

### Neutral

- ADR-002 and ADR-007 both stand; this ADR refines, not supersedes, them.

## Alternatives considered

- **Do nothing; rely on the ADR-007 backstop case-by-case.** Rejected: that is how
  the CEO-role deviation ended up undocumented and how the SKILL.md drift would
  recur. Two drift points justify a rule.
- **Invert ADR-007 to make the source repo (tier 3) authoritative for shape.**
  Rejected: too broad. The references are still a better *shape* oracle than the
  minimal source spec for most of the bundle; only the specific points contradicted
  by observed behavior should flip.
- **Re-source the references now.** Rejected for this session: it is a v0.1c task
  with its own verification, and v0.1b is frozen.

## References

- ADR-002 (reference companies as structural oracle)
- ADR-007 (source-of-truth tier hierarchy; the anticipated divergence)
- `docs/TODO-v0.1c.md` (the two drift items + re-sourcing action)
- Issue #1990 / PR #1989 — CEO role default (`github.com/paperclipai/paperclip/issues/1990`)
- Release v2026.529.0 — skills CLI/catalog/provenance
- `skills/paperclip/SKILL.md` — a real bundled skill (name + description only)
