# Contract: the generated bundle README

Postconditions asserted by the test suite. Cites FR/SC ids from [spec.md](../spec.md).

## C1 — nothing that does not survive import is advertised

**C1.1** (FR-001) The rendered `README.md` contains no `| Goals |` row in the Overview table.

**C1.2** (FR-002) The rendered `README.md` contains no `## Goals` section, and none of the goal
strings from the brief appear anywhere in it.

**C1.3** (SC-006) C1.1 and C1.2 are asserted *together with* C2.1. An absence assertion alone is
satisfied by a template that renders nothing, so absence is only evidence when paired with a
positive assertion over the same render.

## C2 — the file classification is present, file-level, and honest about presence

**C2.1** (FR-003) The rendered `README.md` names, as becoming platform objects: `.paperclip.yaml`,
`agents/`, `projects/`, `tasks/`, `skills/`.

**C2.2** (FR-003) It names `OPERATIONS.md` and `PROJECT-INVENTORY.md` as reader-facing, and states
that `COMPANY.md` is read in part — its name and description read, its identity body not.

**C2.3** (FR-006) For a bundle rendered without operations content, `OPERATIONS.md` and
`PROJECT-INVENTORY.md` appear nowhere in the README. The list names only files the bundle contains.

**C2.4** (FR-005) The classification contains none of: `gap`, `limitation`, `unsupported`,
`unfortunately`, `only`, `fails`, `should`. It states what lands and what does not.

**C2.5** (FR-004) The classification makes no statement about individual constraints, fields, or
enforcement mechanisms, and asserts nothing about which per-agent file lands.

## C3 — the provenance pointer

**C3.1** (FR-007) When the generating version is resolved from package metadata, the README's last
non-empty line carries the version *and* a pointer to the compatibility record.

**C3.2** (FR-008, SC-007) When the generating version is the uninstalled-source fallback, the
pointer clause is absent from the whole file. The version stamp itself still renders — suppression
is scoped to the pointer.

**C3.3** The pointer is a resolvable URL, not a repository-relative path.

## C4 — inertness

**C4.1** (FR-011, SC-005) For a fixed input, every rendered file except `README.md` is byte-identical
to `tests/fixtures/baseline_022.json`, for both the full-bundle and single-agent configurations. The
set of rendered file paths is unchanged.

**C4.2** (FR-010, SC-004) Rendering the same input twice produces identical output. No file in the
bundle contains a date or time that varies between renders.

**C4.3** (FR-009) No rendered file declares a platform schema revision. `schemaVersion` occurs
nowhere in the bundle.
