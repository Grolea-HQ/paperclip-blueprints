# Feature Specification: Platform-revision posture and bundle-facing honesty

**Feature Branch**: `022-platform-revision-posture`

**Created**: 2026-08-19

**Status**: Draft

**Input**: A live import against a current Paperclip established two things: an
example generated bundle imports successfully, and it does so while being read as a legacy schema
revision because it declares none. The first is a claim worth publishing and version-qualifying.
The second turned out not to be a defect worth fixing. Separately, the same import showed the
generated README advertising content that does not survive import.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The bundle stops advertising what import discards (Priority: P1)

An operator opens the generated `README.md` of a bundle they are about to import. Today it shows a
`Goals` count in the Overview table and a `Goals` section listing them. Goals have no counterpart
object, so five minutes after import the company has none — the operator has been told about
content that will not be there. The same README says nothing about which of the other bundle files
become platform objects and which exist for the reader, so `OPERATIONS.md` and
`PROJECT-INVENTORY.md` sit in the tree indistinguishable from files that do land.

After this feature the README states, at file level, what becomes an object and what is for the
reader, and it no longer advertises goals.

**Why this priority**: It is a defect against a decision this project already made. ADR-022
established that goals do not survive import — that is *why* the CEO's `AGENTS.md` carries them.
The README contradicts an implemented decision, so fixing it requires no judgement about the
platform and no new information.

**Independent Test**: Render a bundle from a fixture brief and read the README. Deliverable on its
own: the operator can classify every top-level bundle file without consulting the repo.

**Acceptance Scenarios**:

1. **Given** a fixture brief with goals declared, **When** the bundle is rendered, **Then** the
   README contains neither a Goals row in the Overview table nor a Goals section.
2. **Given** the same bundle, **When** the README is read, **Then** it names, at file level, which
   files become platform objects and which are reader-facing.
3. **Given** a `--single-agent` bundle (no `OPERATIONS.md`, no `PROJECT-INVENTORY.md`), **When** the
   README is read, **Then** the reader-facing list names only files the bundle actually contains.

---

### User Story 2 - The compatibility claim has one findable, expiring home (Priority: P1)

Someone evaluating the project wants to know whether its output actually imports. Today the repo
asserts schema validity; it has never been able to say the claim was checked against a running
platform. That check now exists, it is version-qualified, and it expires.

**Why this priority**: This is the project's strongest credibility artifact — validity *verified*
rather than asserted — and it is worthless if it is stated in two places that drift apart, or
stated without the qualification that makes it honest.

**Independent Test**: Search the repo for the platform revision number and the verification date;
both appear in exactly one tracked file, which the repo README links to.

**Acceptance Scenarios**:

1. **Given** the repo, **When** a reader follows the README link, **Then** they reach a record
   stating that bundles import successfully with a warning, are read as the legacy revision because
   they declare none, and lose nothing because they carry none of the named capabilities.
2. **Given** the record, **When** it is read, **Then** it states which generated versions the claim
   covers and that an operator needing precision should regenerate.
3. **Given** the record, **When** it is read, **Then** it names no bundle and no deployment.

---

### User Story 3 - The posture is recorded where the next reader looks (Priority: P2)

A future maintainer hits the next platform revision and needs to know what this project asserts
about revisions: how one is detected, what compatibility is claimed, what expires, and why no
schema-revision key is emitted despite an importer warning asking for one.

**Why this priority**: Durable, but it changes no output. It is what stops the rejected decision
from being re-litigated from the warning text alone, which reads as though declaring a version is
the remedy.

**Independent Test**: A reader who knows only the importer warning can read ADR-042 and reconstruct
why emitting nothing was chosen.

**Acceptance Scenarios**:

1. **Given** ADR-042, **When** read, **Then** it records emitting a schema-revision key as rejected
   with reasoning, not deferred pending information.
2. **Given** ADR-042, **When** read, **Then** it names the condition the posture depends on: a
   version stamp that moves.
3. **Given** ADR-002, **When** read, **Then** its stability premise no longer stands unqualified and
   its file tree distinguishes platform-facing from reader-facing files.

---

### Edge Cases

- **Version is the uninstalled-source fallback.** `__version__` resolves to `0.0.0+unknown` when the
  package metadata is absent. A pointer line naming that version directs the reader to a record with
  no such entry, while looking authoritative. The line must be suppressed, not rendered with a
  placeholder.
- **Single-agent bundles.** `OPERATIONS.md` and `PROJECT-INVENTORY.md` are only rendered when
  operations content exists. The reader-facing list must not name absent files.
- **Bundles with no projects, tasks, or routines.** The classification describes file classes, not
  counts. It is static text and must not become conditional on a bundle happening to contain none of
  a given kind.
- **A future bundle that does carry one of the named capabilities.** Out of scope, but the posture
  must state that this is the trigger that reopens the emit decision.

## Requirements *(mandatory)*

### Functional Requirements

**Generated README**

- **FR-001**: The generated README MUST NOT contain a Goals row in the Overview table.
- **FR-002**: The generated README MUST NOT contain a Goals section.
- **FR-003**: The generated README MUST state, at file level, which bundle files become platform
  objects on import and which are reader-facing.
- **FR-004**: The classification MUST be file-level only. No per-constraint, per-field or
  per-mechanism statement of what the platform enforces may appear in the template, in generated
  output, or in this feature's documentation.
- **FR-005**: The classification MUST state what lands and what does not without characterising the
  difference — no framing as a gap, limitation, shortfall, or anything the platform ought to do
  differently.
- **FR-006**: The reader-facing list MUST name only files present in the bundle being rendered.
- **FR-007**: The generated README MUST carry a pointer line naming the generating version and
  directing the reader to the compatibility record for what that version was verified against.
- **FR-008**: The pointer line MUST be suppressed entirely when the generating version is the
  `0.0.0+unknown` fallback.

**Bundle invariants**

- **FR-009**: No bundle file may declare a platform schema revision, in any key, in any file.
- **FR-010**: No generation date or other clock reading may enter the render path. Rendering the same
  brief twice MUST produce byte-identical bundles.
- **FR-011**: Every bundle file other than `README.md` MUST be byte-identical to its pre-change
  rendering for the same input.

**Compatibility record**

- **FR-012**: A tracked, publicly visible record MUST hold the dated, version-qualified
  compatibility claim.
- **FR-013**: The claim MUST state that bundles import successfully **with a warning**, that they are
  read as the legacy revision because they declare none, and that nothing is lost because they carry
  none of the capabilities the warning names.
- **FR-014**: The record MUST state that version stamps are coarse — the project is pre-release, the
  version is static and untagged — which generated versions the claim covers, and that an operator
  needing precision should regenerate.
- **FR-015**: The record MUST NOT name any generated bundle, any deployment, or any third-party tool.
- **FR-016**: The repository README MUST link to the record rather than restating any part of it.
- **FR-017**: The platform revision number and the verification date MUST appear in exactly one
  tracked file.

**Decision records**

- **FR-018**: A new ADR MUST record the posture: how a platform revision is detected, what
  compatibility is claimed and how it is qualified, and what expires on what trigger.
- **FR-019**: That ADR MUST record emitting a schema-revision key as rejected with its reasoning, and
  a comment-based provenance marker as rejected with its reasoning.
- **FR-020**: That ADR MUST name the condition the posture depends on — a version stamp that moves —
  and state that until a release cadence exists, the record's granularity is the claim's
  granularity.
- **FR-021**: That ADR MUST NOT restate the compatibility claim's revision number or verification
  date; it points at the record. Discussing the importer's default behaviour as *reasoning* is not a
  restatement of the claim — the prohibition is on carrying a second copy of the expiring fact.
- **FR-022**: ADR-002's schema-stability premise MUST be amended to reflect that a revision has now
  been observed, and its file tree MUST distinguish platform-facing from reader-facing files.

### Key Entities

- **Compatibility record**: The single home for the expiring fact. Holds what was verified, against
  which platform revision, on what date, for which generated versions, and how coarse that
  qualification is.
- **Version stamp**: The generating version already rendered into the bundle README. Load-bearing as
  the key into the compatibility record; only as precise as the project's release discipline.
- **File classification**: A file-level partition of the bundle into what becomes a platform object
  and what exists for the reader.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reader of a generated bundle can determine, for every top-level file in it, whether
  that file becomes a platform object — without consulting the repository.
- **SC-002**: A generated README advertises zero content that does not survive import.
- **SC-003**: The platform revision number and the verification date each occur in exactly one
  tracked file in the repository.
- **SC-004**: Rendering the same brief twice produces byte-identical output, including the README.
- **SC-005**: For a fixed brief, every bundle file except `README.md` is byte-for-byte unchanged from
  before this feature.
- **SC-006**: Removing the classification block from the template causes a test to fail. Absence
  assertions alone do not satisfy this — a test that passes when the template renders empty does not
  count as coverage.
- **SC-007**: A bundle rendered from an uninstalled source tree contains no pointer to the
  compatibility record.

## Assumptions

- The verification is the operator's live import against a current platform; this project has no
  automated import oracle and none is in scope. Live import remains the only mechanism that has ever
  detected a revision.
- Outstanding live-import experiments (whether the declared revision is an honoured input, and
  whether declaring the current revision suppresses a migration the bundle currently benefits from)
  are operator-run and inform the posture. They cannot reverse the emit decision, which rests on the
  present cost of declaring nothing being zero. Their raw results stay in the repository's
  gitignored platform-knowledge notes; only the assertion is published.
- The version bump that makes the record's coverage statement true is the operator's edit to the
  package metadata. This feature states the coverage; it does not perform the bump.
- The generating version is already rendered into the bundle README, so provenance is an existing
  surface being pointed somewhere, not a new one being introduced.
- `docs/` is gitignored per-file rather than by directory pattern, so a new tracked file under it
  requires no ignore-rule change. Every neighbouring platform-knowledge file *is* ignored, so this
  needs stating rather than assuming.
