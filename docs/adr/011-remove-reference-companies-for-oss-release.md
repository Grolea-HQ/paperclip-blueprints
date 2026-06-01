# ADR-011: Remove the reference companies from the public repo for open-source release

## Status

Accepted

## Date

2026-06-01

## Context

ADR-002 made `examples/reference-companies/` the structural oracle for generated
bundles, and ADR-007 ranked it as a tier-2 example oracle for bundle shape. ADR-010
then recorded that these sanitized snapshots are **drifting** from the live product
(empty CEO role; SKILL.md frontmatter) and scheduled a v0.1c re-sourcing pass.

Preparing the repo for open-source release forced a keep-or-remove decision that
the drift alone did not. The five bundles are third-party works under the **Paperclip
Community Companies Licence** (various publishers), not MIT — keeping them would put
non-MIT, share-alike, attribution-bound subtrees inside an otherwise first-party MIT
repo, and would publish a known-stale, known-buggy oracle. No `src/`, script, or
prompt loads the directory at runtime; the only consumer was one drift-guard test.

## Decision

Take **option B: remove `examples/reference-companies/` from the public repo.** The
one test that read a reference HEARTBEAT.md now reads a first-party fixture
(`tests/fixtures/heartbeat_canonical_body.md`) that preserves the verbatim
drift-guard intent. (Commit `fb3d54c`.)

## Consequences

- **ADR-007 tier 2 is inactive** — there is no local example oracle in the repo; the
  tier-1 official docs and tier-3 source repo remain.
- The drift-guard test keeps its meaning via the first-party fixture; generation is
  unaffected (prompts carry their own embedded excerpts).
- Users who want canonical examples can re-source them on demand from
  `paperclip.community/companies`.
- The v0.1c re-sourcing pass is no longer needed for the *public* repo; if examples
  are ever wanted back, option A (re-source + attribute) can be revisited.

## Supersedes

- **ADR-002 (partial):** the reference companies are no longer the in-repo structural
  oracle. The bundle *format* ADR-002 documents still stands.
- **ADR-007 (tier-2 deactivation):** the local-example tier is now empty.

## Resolves

- `docs/TODO-v0.1c.md` item 2 (reference-company drift) — resolved by *removal*
  rather than re-sourcing.

## References

- ADR-002 (output bundle format / reference oracle), ADR-007 (tier hierarchy),
  ADR-010 (reference-company drift)
- Commit `fb3d54c` (the removal); `tests/fixtures/heartbeat_canonical_body.md`
- `paperclip.community/companies` — re-sourcing target if examples are wanted back
