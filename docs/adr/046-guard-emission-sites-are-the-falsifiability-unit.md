# ADR-046 — A guard is enforcement evidence only at the emission sites verified falsifiable

**Status:** Accepted
**Date:** 2026-08-31
**Relates to:** ADR-014 (resilient JSON generation; the `validators/` package this audits),
BLUA-8 (weekly falsifiability audit), BLUA-9 (this routing decision)

---

## Context

BLUA-8's mutation sweep against `49b472c` tested all 51 guard emission sites across 32 guard
IDs in `validators/integrity.py` and `validators/schema_shape.py` by deleting each site in turn
and checking whether the full suite (822 tests) still passed. 24/51 sites are falsifiable
(deletion is caught). 27/51 are not — deletion of the site leaves the suite green. Ten guard IDs
(`I3`, `I5`, `I7`, `I8`, `I9`, `I10`, `S3`, `S4`, `S5`, `S8`) have **no** falsifiable site at all,
including `I9` (`.paperclip.yaml` coherence) and `I10` (file-set completeness), both
import-blocking conditions.

The audit separates two defects. Class A — no test names the guard at all (`I3`, `I7`, `I8`,
`I9`, `I10`, `S3`, `S4`, `S5`, `S8`): nine IDs, unprotected outright. Class B — a test exists but
asserts `pytest.raises(..., match="<ID>")`, a prefix match that a multi-site guard can satisfy
from any one of its sites while the others are deleted (`I5`, `I14`, `S7`, `S15`): four IDs,
falsely reading as covered under a per-ID measure.

The audit also surfaced its own instrument defect: a concurrent second sweep on the same
working tree cross-attributed failures between unrelated guards and reported every corrupted
restore as clean (F-2). The contamination was caught only because this run added an
attribution check (the failing test must *name* the mutated guard, not merely make the suite
red) — a check the original protocol lacked.

## Decision

### 1. The falsifiability unit is the emission site, not the guard ID

A guard ID is "covered" only to the extent that each of its emission sites independently fails
the suite when deleted. `I5`'s three sites are three separate claims; verifying one site says
nothing about the other two. Per-ID coverage claims are retired as a measure — they are the
mechanism that let Class B pass unnoticed.

### 2. Non-falsifiable sites may not be cited as enforcement evidence

Until a site is reclassified FALSIFIABLE-VERIFIED by a mutation re-run, no operator-facing or
board-facing claim may cite it as something the platform enforces. This includes the 9 Class A
guard IDs (no protection at any site) and the 4 Class B guard IDs (protection at some but not
all sites) — the citation must be scoped to the verified site, never the ID. QA Lead's reading
of the report stands: not falsifiable, not evidence.

### 3. Remediation is owned per QA Lead's classification, no amendment

Class A (`I3`, `I7`, `I8`, `I9`, `I10`, `S3`, `S4`, `S5`, `S8`): write a test from scratch per
site, each constructing the specific violating state and asserting the guard reports it.
Class B (`I5`, `I14`, `S7`, `S15`): rewrite the existing assertion from an ID-prefix match to a
match on the specific message per site, and add a test per site not yet covered by any message
match. `I9` and `I10` are prioritized first — both are import-blocking and both currently have
zero protected sites.

### 4. The audit protocol requires exclusive access to the tree under mutation

F-2 is not a QA-execution mistake correctable by care on the next run; it is a missing lock in
the harness, and it produced a *confidently wrong* result — every corrupted site reported
`restore_green=True` — rather than a visible error. This was escalated to the Board as a change
to standing audit protocol, not decided here, because it sets a precedent for how every future
falsifiability sweep is trusted.

**Board ruling, 2026-09-05 (BLUA-11): adopted as amended, effective at the next sweep.** The
exclusive-lock requirement stands, with three amendments the Board adopted from the CEO
challenge record:

1. **Scope is the tree under mutation, not the harness globally.** A sweep locks the working
   tree it mutates. Audits of other trees stay concurrent; only concurrent sweeps *on one tree*
   — the F-2 failure — are prevented.
2. **The lock records its holder's liveness** (run id and pid), so a lock left by a dead sweep
   is identifiable as such. Two mid-sweep crashes are already on the record (F-0, F-3); a lock
   that could not distinguish a dead holder would wedge every later audit behind a manual file
   deletion, which is the same undocumented step that produced F-3.
3. **A stale lock is a tree-integrity incident, not a file to delete.** A cooperative lock stops
   a second sweep from *starting*; it does not stop an orphaned mutator already past its check —
   F-2's second harness outlived the run that started it. So a stale lock means the tree is of
   unknown integrity: verify it against version control before the next sweep starts.

The attribution check (a failing test must name the mutated guard) remains standing regardless,
per Consequences below; the Board was not asked to choose between the two, and the lock closes
the class the attribution check cannot reach — an identical-sides restore verification, which no
assertion inside either sweep can observe.

## Consequences

- 27 emission sites, spanning 10 guard IDs with zero protected sites, are not usable as
  enforcement evidence in any operator-facing or board-facing claim until reclassified.
- QA Lead proceeds directly to remediation per the Class A / Class B split above; no
  re-classification round is needed.
- The attribution check added this run (failing test must name the mutated guard) becomes a
  standing requirement of the mutation protocol, independent of the Board's ruling on locking —
  it is what caught F-2 and nothing else in the existing protocol would have.
- No mutation sweep starts without the tree lock from the next sweep onward (Board, BLUA-11).
  Until the harness carries it, a sweep's `restore_green` column is not citable as evidence on
  its own — the identical-sides comparison class stays open in an unlocked harness.
- Guard coverage claims elsewhere in this repo's docs (ADRs citing a guard ID as enforcing a
  rule) should be read as scoped to whichever sites this audit verified, not the full ID, until
  each ADR is checked against this report.

## Alternatives considered

- **Accept per-ID coverage as sufficient evidence:** rejected — this is exactly the measure
  that let `I5`/`I14`/`S7`/`S15` read as protected while 2 of `I5`'s 3 sites and both of
  `S15`'s and `S7`'s non-asserted sites were deletable. Retiring the ID as the unit is the
  point of this ADR, not a detail of it.
- **Treat non-falsifiable-but-unreached-by-any-mutation-failure sites as lower priority than
  reached-but-unasserted sites:** rejected as a distinction for prioritization, not for the
  enforcement claim — both leave a real violation undetected in the suite; the audit's
  "vacuous" vs "universal assertion never exercised" split is diagnostic, not a severity
  ranking, and remediation order here is driven by import-blocking impact instead (`I9`,
  `I10` first).

## References

- `docs/working/blua-8-falsifiability-report-49b472c.md` — full site-by-site findings
- `docs/working/blua-8-mutation-log-49b472c.md` — raw mutation results, 51 rows
- BLUA-9 — this routing decision; BLUA-8 — the audit that produced the evidence
- BLUA-11 — Board decision on the exclusive tree lock (§4): adopted as amended, 2026-09-05
