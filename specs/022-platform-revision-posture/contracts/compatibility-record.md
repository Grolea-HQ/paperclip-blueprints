# Contract: the compatibility record and the decision records

Postconditions asserted by the test suite and by review. Cites FR/SC ids from
[spec.md](../spec.md).

## C5 — the record exists, is tracked, and is the only home for the expiring fact

**C5.1** (FR-012) `docs/platform-compatibility.md` exists and is tracked by git. The `docs/`
ignore rules are per-file and per-directory, not a directory-wide pattern, so this holds without an
ignore-rule change — but every neighbouring platform-knowledge file *is* ignored, so the fact is
stated rather than assumed.

**C5.2** (FR-017, SC-003) The platform revision number and the verification date each occur in
exactly one tracked file: this record. No ADR, no README, no template, no test restates them.

**C5.3** (FR-016) The repository README links to the record and restates no part of it.

## C6 — the claim is stated honestly

**C6.1** (FR-013) The claim states all three of: import succeeded, a warning was issued, and the
bundle was read as the legacy revision because it declares none.

**C6.2** (FR-013) The claim states that nothing is lost, and says why — the bundle carries none of
the capabilities the warning names. The zero cost is inside the claim, not a footnote to it.

**C6.3** (FR-014) The record states that version stamps are coarse, that the project is pre-release
with a static untagged version, which generated versions the claim covers, and that an operator
needing precision should regenerate.

**C6.4** (FR-015) The record names no generated bundle, no deployment, and no third-party tool.

## C7 — the posture is recorded

**C7.1** (FR-018) ADR-042 states how a platform revision is detected, what compatibility is claimed
and how it is qualified, and what expires on what trigger.

**C7.2** (FR-019) ADR-042 records emitting a schema-revision key as **rejected with reasoning**, not
deferred pending information — including that declaring the current revision carries an unquantified
migration-on-read risk pointing opposite to the warning's framing.

**C7.3** (FR-019) ADR-042 records a comment-based provenance marker as rejected, because nothing
guarantees comments survive tooling.

**C7.4** (FR-020) ADR-042 names the dependency: the posture rests on a version stamp that moves;
the project has no release process and no tags; until it does, the record's granularity is the
claim's granularity. The trigger for revisiting is stated.

**C7.5** (FR-021) ADR-042 carries no revision number and no date as a compatibility claim. Reasoning
about importer behaviour is permitted; a second copy of the expiring fact is not.

## C8 — ADR-002 is corrected

**C8.1** (FR-022) ADR-002's schema-stability premise no longer stands unqualified. It records that a
revision has been observed and what that changed.

**C8.2** (FR-022) ADR-002's Decision-block file tree distinguishes platform-facing from
reader-facing files, at file level — extending to the whole tree what its ADR-022 revision note
already states for `OPERATIONS.md` alone.
