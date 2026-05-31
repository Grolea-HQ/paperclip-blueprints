# ADR-009: In-stack bundle validator, not a JSON-Schema dependency

## Status

Accepted

## Date

2026-05-31

## Context

Constitution Principle II (NON-NEGOTIABLE) requires that every bundle validate
against the `paperclip/v1` and `agentcompanies/v1` schemas **before** any file is
written to disk. v0.1a satisfied this with an inline `structural_check` in
`renderers/bundle.py` scoped to the single-agent slice; v0.1b's spec (US3) pulls a
dedicated, comprehensive validator forward as a deliverable.

Two ways to validate against "the schema" were available:

1. Add a `jsonschema` dependency and validate each file's frontmatter against
   vendored `paperclip/v1` / `agentcompanies/v1` JSON-Schema documents.
2. Validate **in-stack** (plain Python + Pydantic) against the shape the reference
   companies actually exhibit, plus the bundle's referential-integrity rules.

We do not have authoritative JSON-Schema files for the two schemas. ADR-007 makes
the local `examples/reference-companies/` the blessed oracle for bundle shape, and
ADR-001 fixes the dependency set (adding one needs explicit operator approval).
What Paperclip's importer actually accepts is the reference shape — not an abstract
schema document we would have to reverse-engineer and then keep in sync.

## Decision

Implement the validator as an in-stack `validators/` package — **no new
dependency**:

- `validators/schema_shape.py` — rules S1–S9: correct `schema:` strings, required
  frontmatter keys, required body section headings, ≥2 "we are not"/constraints, an
  idle-state belief in every SOUL.md, the OPERATIONS.md section set, the anti-drift
  echo of every constraint and "we are not" negation (P-PAT-10), empty inventory
  tables, and body-only files carrying no schema frontmatter.
- `validators/integrity.py` — rules I1–I10: single acyclic root, span-of-control
  ≤7, and resolution of every skill / project / assignee / handoff reference, plus
  `.paperclip.yaml` maps and the file set matching the assembled bundle.
- `validators/__init__.py::validate_bundle(config, files)` runs both over the
  assembled `CompanyConfig` (structured, robust) **and** the rendered file map
  (shape), aggregates every violation, and raises a single `BundleValidationError`.

`renderers/bundle.py::build_and_write` calls `validate_bundle` after the in-memory
render and before the atomic write, replacing the v0.1a inline `structural_check`
as the pipeline gate. The reference companies (all five) are the shape oracle; the
operator's manual Paperclip import remains the final confirmation (SC-008).

## Consequences

### Positive

- Constitution II is enforced by a dedicated, unit-tested module; no bundle reaches
  disk unvalidated, and a failure leaves no partial bundle (the write step is never
  reached).
- The ADR-001 dependency set is unchanged — no `jsonschema`, no vendored schema
  files to drift out of sync.
- Validating the structured `CompanyConfig` (not just file text) makes the
  referential checks robust to template/whitespace changes.
- Every violation is reported at once (aggregation), so the operator fixes the whole
  bundle in one pass.

### Negative

- "Valid" is defined by the reference shape we encode, not an external schema
  authority. If Paperclip's importer diverges from the reference companies, the
  validator can pass a bundle the importer rejects (caught by the manual import,
  SC-008) — or vice versa. Mitigation: the reference companies are kept current as
  the oracle (ADR-007).
- The anti-drift echo check (S7) expects each constraint / "we are not" to appear in
  the operations anti-drift checks; heavy model paraphrasing could trip it. The
  `operations_generator` prompt is explicit about reproducing them, and a failure is
  a clear, actionable signal rather than a silent drift.

### Neutral

- `structural_check` remains in `renderers/bundle.py` as a tested artifact-level
  utility (used by its existing tests) but is no longer the pipeline gate.

## Alternatives considered

- **Add `jsonschema` + vendored schema files.** Rejected: a new dependency requiring
  operator approval, and we lack authoritative schema documents; the reference shape
  is the real oracle (ADR-007).
- **Keep the inline `structural_check`.** Rejected: US3 calls for a dedicated,
  comprehensive validator; the rule set (S1–S9 + I1–I10) is large enough to warrant
  its own tested module.

## References

- Constitution Principle II — Schema-Valid Bundles (NON-NEGOTIABLE)
- ADR-001 — tech-stack choices (fixed dependency set)
- ADR-007 — source-of-truth hierarchy (reference companies as shape oracle)
- `specs/002-v01b-full-multi-agent-bundle/contracts/bundle-validation.md` — the S/I rule contract
- `src/paperclip_blueprints/validators/` — the implementation

## Update — S7 relaxed from verbatim to key-phrase coverage (Path C)

The S7 anti-drift check introduced with this ADR (commit `fde7076`) required each
COMPANY.md constraint and "we are not" negation to appear **verbatim** — as a
whole-string substring — inside the operations anti-drift checks. The first live
`generate` run failed S7 on every item: that bar is unwinnable, because the
`operations_generator` prompt asks the model to *restate* each item as an operational
check, so a faithful paraphrase fails the verbatim match (and even a literal
reproduction fails on multi-sentence negations). The prior "negative consequence"
above — "S7 could trip on heavy paraphrasing" — landed in practice immediately.

S7 is now a **key-phrase coverage** check: each constraint/negation must contribute at
least one distinctive term (≥5 letters, not a stopword) to the anti-drift text
(`validators/schema_shape.py::_key_terms`). The `operations_generator` prompt was
clarified to remove the self-contradictory "reproduce … restated" wording. The
Constitution-II guarantee is preserved — a dropped item is still caught — without
dictating the model's phrasing. The same change added a failed-bundle dump
(`<output>-failed/`, commit immediately preceding this one) so rejected runs are
inspectable.

This change is the **Path C** commit (subject `v0.1b fix: relax S7 …`; its exact SHA
is the one that introduced this section — see `git log`/`git blame` on this file,
since a commit cannot embed its own hash). Diagnosis context:
`specs/002-v01b-full-multi-agent-bundle/research.md` R-003.
