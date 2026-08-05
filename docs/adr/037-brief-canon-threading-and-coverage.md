# ADR-037: Thread the brief's operating canon to the procedure carriers, and check its coverage

## Status

**Accepted.**

## Date

2026-08-05

## Context

Section 11 of the brief is the operator's residual channel: the rules, rubrics, thresholds
and classification schemes that no structured field captures. Its defining property is that
**nothing else carries it**. A roster directive in section 7 is materialised into stubs by
the org planner; a constraint in section 6 reaches every generator through
`CompanyDefinition`. Canon stated in section 11 has no second path.

It reached exactly two consumers: `identity_generator` and `org_planner`. The four
generators that write *procedure* — skills, agents, tasks, projects — never saw it.

**Why this was worse than one blind generator.** `org_planner` *does* read section 11, so
it correctly invented capability slugs reflecting canon that lived only there. The skill
generator then wrote each of those skills' contents blind to the canon that motivated the
slug, reconstructing plausible-looking content from the slug name plus the company
constraints. The two halves disagreed and nothing noticed.

On a real 13-agent bundle, a five-dimension scoring rubric and a table of evidence-class
half-lives produced **zero occurrences anywhere in the output**. Not weakened — absent. The
bundle looked complete and was missing its most important procedure. **The slug was the only
surviving carrier of the canon, and a slug carries a name, not a rubric.**

The failure is silent by construction. Nothing in the pipeline knew the canon existed, so
nothing could report that it had gone. This is Constitution Principle IV — brief-faithful
generation over recycled shape — failing in its purest form: the generator fell back to
plausible generic content precisely because the operator's actual material never arrived.

Corroborating evidence that the field had been forgotten rather than deliberately scoped:
`free_text` was the only member of its cluster in `models/input.py` with **no docstring**,
while `use_case_notes` and `run_policy_preferences` both document exactly where they are
threaded.

## Decision

### 1. Thread the canon wholesale to the four procedure carriers

`brief.free_text` is read **once**, in `renderers/bundle.py`, and passed unchanged as a
narrow keyword-only `canon: str | None` to `generate_skill`, `generate_agent`,
`generate_task` and `generate_project`.

**Wholesale, never selective.** No component summarises, ranks, truncates or per-consumer
selects from the canon. A selector would be a second place to lose canon silently — the
exact failure being repaired.

**One read site is what makes that auditable.** The alternative (widening the three
signatures to take the whole `CompanyBrief`) would have been more uniform-looking and
strictly worse: a wide object with no stated contract about which fields are read is the
drift that produced this defect. With one read there is exactly one place a transformation
could be introduced, and a test asserts the whitelist of readers by name — threading
(`bundle.py`), coverage (`render.py`), calibration (`cli.py`) — so a generator that starts
reading the brief directly fails the suite.

Notably `generate_agent` takes `canon=` too, even though it already receives `brief`.
Reading `brief.free_text` there would have been a second threading site and would have
dissolved the guarantee for a trivial saving.

### 2. Each consuming prompt states an encode-don't-paraphrase contract

An identical block in all four prompt files instructs the model that this is operating
canon to be **encoded into procedure** — named dimensions, thresholds and labels appearing
as concrete steps with their actual values — not background to paraphrase into a summary
sentence.

The block is **deliberately duplicated** rather than shared. `render_prompt` builds a bare
`jinja2.Template` with no loader, so `{% include %}` would not resolve; and prompts are
versioned artifacts whose purpose is to be read whole by a human tuning them. A test asserts
the block is present in all four and byte-identical across them, which is what makes the
duplication safe against drift.

### 3. Two generators are excluded, for two different kinds of reason

**These must not be collapsed into a single "we decided not to."** They have different
expiry conditions, and a future reader who flattens them will draw the wrong conclusion.

- **Souls — excluded on FITNESS. Permanent.** `SOUL.md` *does* reach a running agent, so a
  delivery criterion would include it. It is excluded because procedure is the wrong *kind*
  of content for a persona artifact: its value depends on staying short (roughly forty short
  lines), beyond which the model stops treating it as identity and starts treating it as
  instructions it can debate, and a procedural step belongs in the mandate or the heartbeat.
  Threading a long rubric there would degrade the artifact while the same canon is already
  carried by `AGENTS.md` and the skill — so the exclusion costs nothing.
- **Operations and goal hierarchy — excluded on DELIVERY. Platform-dependent; revisit if
  import behaviour changes.** `OPERATIONS.md` is dropped on import and `COMPANY.md` goals do
  not survive (ADR-022), verified against platform v2026.626.0, so these artifacts do not
  reach a running agent. This is a statement about how the platform behaves **today**, not a
  permanent property of these generators.

### 4. A canon-coverage check, term-oriented and advisory

`renderers/canon.py` derives distinctive terms from the canon and reports, through the
existing `warn` sink at the end of `render_files`, any term that reaches zero files.

**Term-oriented, not artifact-oriented.** The question is "does this term appear in any
rendered file?", never "does this artifact contain canon?". This satisfies ADR-019's
standing constraint **structurally**: a referenced commodity skill contributes no `SKILL.md`
to the rendered map and is therefore outside the scan by construction — not by an exemption
entry that would have to be maintained, and that would silently rot when ADR-019 is
eventually implemented. A rule beats a rule plus exceptions.

**Advisory, never fatal.** It never raises and is never part of `validate_bundle`, which
does. A missing rubric is a judgement call for the operator; a schema violation is not.

**Scoped to canon-unique material.** A phrase also present in `we_are`, `constraints`,
`north_star`, `goals`, `we_are_not` or `description` is dropped at extraction. It reaches
the generators by an existing path, so its coverage says nothing about *this* defect and its
presence in the report is pure noise. This is the single sharpest precision lever in the
design.

**Two warning kinds — missing and thin.** Missing (zero carriers) names the term. Thin
(exactly one carrier) names the term **and the file**. A fully-carried term produces no
line. Reporting a line per term would flood the sink on a healthy bundle, which is
operationally identical to no check at all; reporting only a verdict ("canon coverage
incomplete") would be unactionable without opening the bundle and would make a loose
extractor indistinguishable from a real finding. Naming the term degrades the failure mode
gracefully: a false positive is *visibly* a false positive.

**All files are scanned; none is privileged.** Narrowing to artifacts that survive import
would bake v2026.626.0 behaviour into a mechanical checker. Instead the carrier is reported
and the reader applies that knowledge — so a term surviving only in `OPERATIONS.md` appears
as a *thin* result naming that file, and the check itself cannot go stale.

**Presence, never fidelity.** Warning text makes no claim about whether canon was encoded
usefully; a test asserts the absence of quality vocabulary. Whether a rubric survived as
usable procedure is human judgement and the check must not appear to make it.

### 5. Calibration splits: the repo holds shapes, the operator holds reality

The three extraction thresholds are **named module constants**. The committed fixture is a
*structurally equivalent* stand-in — a multi-dimension rubric with named dimensions, a table
with class labels, and ordinary narrative prose alongside, in invented vocabulary — so the
suite exercises the shapes the rule must catch *and* those it must reject. Same-source
negatives are what make it a calibration rather than a keyword list, and they survive
sanitisation because the discrimination lives in the shape, not the vocabulary.

**The real section-11 text never enters this repository.** It is project canon and this repo
is public and open-source-bound; the exclusion holds regardless of how benign any individual
phrase looks. Final calibration happens outside: `blueprints check-canon --input <brief>
--bundle <dir>` runs extraction and coverage against a bundle already on disk — no
generation, no API key — so the thresholds can be tuned against the real brief and the real
failing bundle at zero cost, and re-run after each adjustment. A threshold that needs moving
is a one-constant change.

This places the calibration judgement where the did-it-land judgement already sits: with the
person who wrote the brief.

### 6. The input template ships with the behaviour, and illustrates shape only

Section 11's guidance was rewritten in the same change, because shipping a behaviour change
to an input field while the document describing that field stays stale is the same defect
class this ADR exists to fix.

It states what belongs (procedures, rubrics, standards, decision rules), what belongs
elsewhere (org shape → section 7; identity → sections 4–6), and — plainly — that the
material is now encoded rather than paraphrased, so an offhand aside will come back as
procedure.

It illustrates **shape only**: a named-dimension list and a labelled table with placeholder
content (`Dimension A`, `Class 1`). It deliberately ships **no worked example**. A repository
that shipped an exemplary rubric would begin producing companies carrying that rubric —
recycled shape moved upstream into the brief, one layer earlier than the prompt-level guards
reach, which Principle IV rules out. The sanitised calibration fixture is a *test* artifact
and is deliberately not cross-referenced from the template, since that would be the same
worked example arriving by the back door.

The section heading now reads "Operating canon" while the parser still keys on the
`**Other context:**` anchor. Renaming that anchor would have silently parsed existing
briefs' canon as `None` — this defect, reintroduced through its own documentation task. The
heading/anchor divergence is recorded as follow-up work needing its own spec (a
back-compatible parser accepting both anchors, with a rule for briefs carrying both).

### 7. Cost was settled by arithmetic, before any code

`STRUCTURAL_MODEL` is `claude-sonnet-4-6` at $3/Mtok input. The reference workload adds
27 skills + 13 agents + ~8 tasks + ~3 projects ≈ **51 additional prompt renders**; at a
pessimistic 4k-token canon that is **≈$0.61 per bundle**, against the project's
under-$2-per-bundle target.

This was computed statically during planning, with **no API call**. It confirmed the
wholesale decision rather than making it — had it come out at ten dollars a bundle, the
selective-threading option would have needed reopening. Prompt caching was considered and
rejected: complexity for no gain at this magnitude.

## Consequences

### Positive consequences
- Canon whose only carrier is section 11 now reaches every artifact that writes procedure.
- The class of failure is no longer silent: a term reaching nothing is named on every run.
- `check-canon` makes threshold calibration and re-verification free and repeatable.
- The exclusion rationales are recorded with their different expiry conditions, so the
  platform-dependent one carries its own revisit trigger.
- Principle IV is enforced one layer earlier — in the brief's own documentation.

### Negative consequences
- Every skill/agent/task/project prompt grows by the length of the canon. Bounded, measured,
  ~$0.61/bundle pessimistic.
- Extraction is a heuristic. It will occasionally name a term the operator considers
  uninteresting; by-name reporting is what keeps that cheap to dismiss.
- The contract block is duplicated across four prompts, guarded by a test rather than by
  construction.
- A term carried only by an import-dropped artifact counts as covered. It surfaces as *thin*,
  which is mitigation, not a fix. Accepted deliberately over encoding platform behaviour.

### Neutral consequences
- `free_text` now has three readers with three distinct jobs, whitelisted by name in a test
  that is meant to be edited deliberately rather than widened to silence a failure.
- Section 11's heading and its parser anchor disagree until the follow-up lands.

## Alternatives considered

- **Per-skill canon selection** (send each generator only the relevant slice). Rejected: a
  selector is a second place to lose canon silently, which is the failure being repaired.
- **Widen the generator signatures to take the whole `CompanyBrief`.** Rejected: a wide
  object with no contract about which fields are read is how this defect arose, and it would
  have made the deferred section-7 threading easy to slip in invisibly.
- **Operator-declared canon terms in the brief.** Rejected: it makes the operator do the
  extraction, and a term they forget to declare is silently unguarded — reintroducing the
  silent-loss failure one level up.
- **Make the coverage check a hard validation error.** Rejected: whether canon must appear is
  a judgement, and a false positive that blocks a bundle would get the check disabled.
- **Narrow the scan to artifacts that survive import.** Rejected: bakes platform
  v2026.626.0 behaviour into a mechanical checker; the thin warning carries the signal
  without the assumption.
- **Thread section-7 `use_case_notes` in the same change.** Deferred to its own spec. The
  assessment is settled — section 7 should reach the same carriers under a *constraint*
  contract, distinct from section 11's *encode* contract, since encoding "cap headcount at
  eight" as a procedural step would be a new defect — but shipping both at once would leave
  the validating regeneration with two variables, and adding brief material to the same
  renders raises the paraphrase risk on the very fix being validated.
- **Commit the real section 11 as the calibration fixture.** Rejected: project canon does not
  belong in a public repository, and the structurally-equivalent fixture plus an out-of-repo
  calibration pass gets the same discrimination.

## References

- ADR-022 — object model; `OPERATIONS.md` dropped on import, `COMPANY.md` goals not
  surviving. The basis for the *delivery* exclusion, and its revisit trigger.
- ADR-019 — reuse ecosystem commodity skills (deferred). Its standing constraint is
  satisfied structurally by the term-oriented design, with no exemption list.
- ADR-036 — routine scheduling and collision detection. Two properties carried forward: the
  positive-detection requirement for advisory checks (a check whose tests assert only
  silence cannot be distinguished from a dead one), and the consolidated hazard class *"The
  sibling class: state a single-process suite cannot see"* — of which this feature hit
  variant 2, set-iteration order under `PYTHONHASHSEED`, in code containing no hashing at
  all.
- ADR-035 — spec-artifact commit convention: `spec.md` and `contracts/*.md` are committed.
- Constitution Principles III (test-first) and IV (brief-faithful over recycled shape).
