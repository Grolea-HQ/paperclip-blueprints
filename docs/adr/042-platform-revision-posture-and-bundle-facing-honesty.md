# ADR-042 — Platform-revision posture, and what a bundle says about itself

**Status:** Accepted
**Date:** 2026-08-19
**Relates to:** ADR-002 (output bundle format, amended by this work), ADR-022 (object model —
what import keeps), ADR-007 (source-of-truth hierarchy)

---

## Context

A live import against a current Paperclip established two things at once.

The first: a generated bundle imports. That had never been verified against a running platform
before — only asserted by validating against the schemas this tool targets. The distinction matters
because a schema check cannot detect that the platform's data model has moved underneath the schema.

The second: the importer warned that the package declares a legacy schema revision and predates nine
task-data capabilities. Our bundles declare no revision at all; absence is normalised to the legacy
value and then reported as though it had been declared.

That warning reads as a defect report with an obvious fix — declare the current revision. It is
worth being precise about why that reading is wrong, because the next person to see the warning will
reach the same conclusion from the same evidence.

ADR-002 accepted the risk of schema evolution on the stated grounds that *"the schemas have been
stable across the examples and docs available so far."* That premise was load-bearing and it is now
falsified by observation. This is the first revision event, and the project had no stated position
on what to do when one arrived.

## Decision

### 1. Compatibility is claimed by importing, dated, and allowed to expire

Live import is the detection mechanism and the only one that has ever detected a revision. What was
verified, against which revision, on what date, and for which generated versions lives in
`docs/platform-compatibility.md` — one file, publicly visible, the single home for the expiring
fact. This ADR deliberately restates neither the revision number nor the date: two copies of an
expiring fact eventually disagree, and the copy that gets updated is never the copy being read.

### 2. No schema-revision key is emitted — rejected, not deferred

The present cost of declaring nothing is **zero**. The capabilities the warning names import only if
the bundle carries the corresponding data, and generated bundles carry none of it. The warning
describes absent data, not lost data.

Against that zero cost sits a risk in the opposite direction from the warning's framing. A revision
counter of this kind normally exists to drive migration on read. If the importer currently *upgrades*
a package it reads as legacy, then declaring the current revision asserts "already current, do not
migrate" and may suppress exactly that normalisation. The warning would then be advertising a
footgun as a remedy: absence is what buys the upgrade, and declaring is what forgoes it.

Whether that migration exists is unresolved. Two operator-run experiments bear on it — whether the
declared value is an honoured input at all (declaring an intermediate revision and checking whether
the reported capability delta narrows) and whether a task object read from the API differs in its
key set between a declaring and a non-declaring import. Their results inform this ADR and cannot
reverse it: the decision rests on the present cost being zero, which no experiment changes.

**The trigger that reopens this:** a generated bundle that begins to carry one of the named
capabilities. At that point the declared revision becomes load-bearing rather than cosmetic, and the
risk above must be resolved rather than avoided.

### 3. A comment-based provenance marker is also rejected

A YAML comment is inert by construction and cannot be mistaken for a declaration, which is its
appeal. It is still the wrong home for a fact the operator needs: nothing guarantees a comment
survives tooling, and it would vanish precisely when the file has passed through something.

### 4. Provenance addresses the reader, in the file the reader opens

The question "what platform shape was this built against?" is asked by someone holding a bundle. It
is answered in the bundle's `README.md`, which is not read by the importer, so nothing can mistake
it for a declaration. The README stamps the generating version and points at the compatibility
record; the record says what that version was verified against. The bundle records what it is; the
repository records what that means.

No generation date is emitted. A date is a fact about the version, not a second fact about the
bundle — the repository already holds it — and recording it in the artifact would put a clock in a
render path that has none. That purity is load-bearing: "byte-identical to today" is this project's
standard of proof that a change is inert, and it stops being available for any file carrying a
timestamp.

Where the version cannot be resolved from package metadata, the pointer is **suppressed entirely**
rather than rendered with the fallback value. A plausible-looking version that resolves to no entry
in the record is worse than silence, because it does not announce itself as broken.

### 5. The bundle states, at file level, what import keeps

ADR-022 established which parts of a bundle become objects. The generated README did not say so, and
worse, advertised company goals — a `Goals` count and a `Goals` section — which have no counterpart
object and do not survive import. That is a contradiction with a decision this codebase already
implements elsewhere (it is *why* the root agent's `AGENTS.md` carries the goals), so removing it
requires no judgement about the platform.

The README now names, at file level, what becomes an object and what is documentation for the
reader. File level is the ceiling: this repository does not classify individual constraints or
fields by enforcement mechanism. The statement is descriptive — what lands and what does not — and
characterises the difference as neither gap nor limitation.

## Condition this posture depends on

**The version stamp must move.** The pointer, and the record's coverage statement, are only worth
anything if the version identifies something. Today it does not identify much: the version is static
in the package metadata, there are no release tags, and it advances only when someone remembers to
advance it. One bump does not fix that — it is hand-maintenance, and hand-maintained version stamps
fail quietly.

So, stated where the next reader will find it rather than rediscovered: **until this project has a
release cadence, the compatibility record's granularity is the granularity of the claim.** The
record says so plainly and tells an operator who needs precision to regenerate. When tags and a
release process exist, the record can be keyed per release and that instruction can go.

## Consequences

**Positive**

- The project's strongest claim — validity verified against a running platform rather than asserted
  — is publishable, dated, and qualified in a way that will not quietly become false.
- The warning is understood rather than obeyed. A future reader who finds it does not re-derive the
  wrong fix from the message text alone.
- The generated bundle stops promising content that import discards.
- No clock enters the render path, so the inertness standard survives.

**Negative**

- The importer will keep warning on every import, and it will keep looking like something is wrong.
  This ADR is the answer to that, but it has to be found.
- The compatibility claim needs manual re-verification and will go stale between imports. Nothing
  detects staleness automatically.
- The version qualification is coarse enough that "regenerate if you need precision" is the honest
  answer, and that is a real cost borne by the operator.

**Accepted risk**

- If migration-on-read exists and the platform later stops applying it to packages that declare
  nothing, our bundles would silently lose the benefit with no warning. The trigger above is the
  planned detection point; between now and then, the only detector is another live import.

## Alternatives considered

1. **Declare the current revision.** Rejected — trades a zero-cost warning for an unquantified
   migration risk pointing the other way.
2. **Declare the legacy revision explicitly**, making the default visible rather than implied.
   Rejected — same risk surface, and it asserts something about our bundles that is only true by the
   importer's own defaulting.
3. **A YAML comment carrying provenance.** Rejected — see §3.
4. **A generation date in the bundle.** Rejected — see §4.
5. **Say nothing and leave the compatibility fact in the local platform notes.** Rejected — those
   notes are gitignored, so the verification would be invisible to exactly the reader for whom it is
   evidence.
