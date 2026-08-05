# Feature Specification: Brief Canon Threading & Coverage

**Feature Branch**: `016-brief-canon-threading`

**Created**: 2026-08-05

**Status**: Draft

**Input**: Thread the brief's section 11 (`free_text`) operating canon into the skill, agent, task and project generators, which currently render blind to it, and add a mechanical canon-coverage check over the rendered bundle.

---

## Context: the defect

The brief's section 11 is the operator's residual channel for operating canon — the
rules, rubrics and thresholds that have no dedicated field elsewhere in the template.
It reaches exactly two consumers today: the identity generator and the org planner.
The skill, agent, task and project generators never see it.

This is worse than one blind generator, because the org planner *does* read section 11.
It correctly invents capability slugs that reflect canon living only there — names of the
shape `evidence-classification`, `threshold-analysis`, `delivery-date-scoring`. The skill
generator then writes each of those skills' contents blind to the canon that motivated the
slug, reconstructing plausible-looking content from the slug name plus the company
constraints.

On a real 13-agent bundle, a five-dimension evidence-scoring rubric and a table of
evidence-class half-lives produced **zero occurrences anywhere in the output**. Not
weakened — absent. The bundle looked complete and was missing its most important
procedure. The slug was the only surviving carrier of the canon, and **a slug carries a
name, not a rubric**.

The failure is silent by construction: nothing in the pipeline knows the canon existed,
so nothing can report that it went missing.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Operating canon reaches the artifacts that carry procedure (Priority: P1)

The operator writes a rubric, a threshold table, or a classification scheme into section 11
of the brief. They generate a bundle. The generated skills, agent mandates, tasks and
projects encode that material as procedure — the rubric's dimensions appear as steps, the
threshold values appear as stated thresholds — rather than being reconstructed from a slug
name.

**Why this priority**: This is the defect. Without it, the highest-value content in the
brief is silently discarded, and the operator cannot tell by reading the bundle. Every
other part of this feature exists to protect this one.

**Independent Test**: Author a brief whose section 11 contains a distinctive procedural
detail that appears nowhere else in the brief. Generate a bundle. Confirm the detail
appears in at least one generated skill. This is testable with a stubbed model client;
it does not require a real generation run.

**Acceptance Scenarios**:

1. **Given** a brief whose section 11 states a scoring rubric and whose section 11 alone
   mentions a term, **When** the operator generates a full bundle, **Then** that term is
   present in the rendered prompt for every skill, agent, task and project generation.
2. **Given** a brief with no section 11 at all, **When** the operator generates a bundle,
   **Then** the rendered output is unchanged from the current behaviour.
3. **Given** section 11 content, **When** any of the four consuming prompts is rendered,
   **Then** the prompt carries an explicit instruction that this material is operating
   canon to be **encoded into procedure**, not background to paraphrase.
4. **Given** section 11 content, **When** it is threaded to a consumer, **Then** it is
   passed **in full and unmodified** — no per-consumer selection, filtering, ranking or
   summarisation occurs anywhere in the path.

---

### User Story 2 - Canon that goes missing is reported, not silent (Priority: P2)

The operator generates a bundle. If a distinctive term from section 11 reaches **zero**
files in the rendered bundle, the run reports it as an advisory warning naming the term.
The operator decides what, if anything, to do about it.

**Why this priority**: Threading fixes today's instance; the check is what makes the class
of failure non-silent for every future prompt change, model change or brief shape. It is
the durable safeguard, but it delivers nothing on its own if the threading is absent —
hence P2 behind P1.

**Independent Test**: Render a bundle from a brief with section 11 canon, then render one
with the canon deliberately absent from every generated artifact. The first produces no
canon warning; the second names the missing term. Both are testable against a rendered file
map with no model involved.

**Acceptance Scenarios**:

1. **Given** a bundle in which every distinctive section-11 term appears in at least one
   rendered file, **When** the bundle is rendered, **Then** no canon-coverage warning is
   emitted.
2. **Given** a bundle in which a distinctive section-11 term appears in no rendered file,
   **When** the bundle is rendered, **Then** a warning is emitted **naming that specific
   term**, not reporting an aggregate coverage verdict.
3. **Given** a term that is covered, **When** the bundle is rendered, **Then** the report
   states **where** it was found, so a term carried by only one artifact is visible as a
   weak result rather than an unqualified pass.
4. **Given** any bundle, **When** the coverage check runs, **Then** it never fails the run,
   never raises, and never participates in the pre-write validation gate.
5. **Given** the same brief and the same rendered bundle, **When** the check is run
   repeatedly, **Then** it produces identical output every time, with no model call and no
   network access.
6. **Given** an agent that references a platform-provided commodity capability which
   contributes no generated file, **When** the check runs, **Then** that capability is
   never reported as a coverage failure and requires no exemption entry.
7. **Given** the reference section-11 text from the brief that produced the 13-agent
   bundle, **When** terms are extracted, **Then** the scoring-dimension names and
   evidence-class labels are recovered and the ordinary narrative prose in that same
   section is not.

---

### Deferred - Section-7 customization notes (own feature, not this one)

Threading the brief's section-7 customization notes to the same four carriers is
**deferred to its own specification. Deferred, not undecided** — the assessment below is
settled and must not be re-derived; only the shipping is postponed.

**The settled assessment.** Section 7's notes should eventually reach the same four
carriers, but under a **constraint** contract, not section 11's **encode** contract. They
are binding directives about org shape — roster, headcount, what is scheduled. Section 11
is operating canon to be encoded into procedure. Applying the encode contract to an
org-shape directive would have a skill turn "cap headcount at eight" into a procedural
step: a *new* defect, not a fix. The two channels need different framings, and that
distinction is the substance of the deferred work.

**Why it is not shipped here — validation, not design.** What closes this feature is the
operator regenerating the bundle and judging whether the rubric survived as procedure. If
two brief channels changed in the same run and the output comes back mushy, there is no
way to tell whether the canon contract failed or the section-7 material diluted it. One
variable at a time.

**A second-order reason.** The entire risk of wholesale threading is the model paraphrasing
instead of encoding. Adding more brief material to the same renders increases exactly that
risk — on the very fix being validated.

---

### Edge Cases

- **Section 11 absent or empty.** Both threading and the coverage check are complete
  no-ops. Rendered output must be unchanged from current behaviour, so a brief without
  section 11 cannot regress.
- **Section 11 present but entirely ordinary prose.** Term extraction must not treat
  common English as distinctive; a section 11 of plain narrative must not generate a wall
  of warnings. A check that cries wolf gets ignored, which is the same outcome as no check.
- **A term legitimately appears only in an artifact that does not survive import.** The
  check scans every rendered file, so a term surviving only in `OPERATIONS.md` counts as
  covered even though that artifact is dropped on import. Narrowing the scan to
  agent-reaching artifacts would bake today's platform import behaviour into the check —
  exactly the class of version-dependent assumption this project has been bitten by
  repeatedly. Instead, FR-008a reports *where* each term was found, so this case surfaces
  to the operator as a visibly weak result they can judge, while the check itself stays
  free of any claim about which artifacts reach a running agent.
- **A term appears in exactly one file.** Covered. The check asserts reach, not emphasis;
  it has no opinion on how many carriers a term should have.
- **The same canon appears in the brief's structured fields as well as section 11.** No
  special handling — the term is covered, and the check is silent.
- **Extraction produces a term that is a substring of an unrelated word.** Matching must
  not report coverage on an accidental substring hit, nor miss a genuine hit due to
  ordinary case or punctuation differences.

---

## Requirements *(mandatory)*

### Functional Requirements

**Threading**

- **FR-001**: The system MUST make the brief's section-11 operating canon available to the
  skill, agent, task and project generation prompts.
- **FR-002**: The canon MUST be threaded **wholesale** — in full, unmodified, identical for
  every consumer. No component may select, rank, filter, truncate or summarise it per
  consumer. A selector would create a second place for canon to be lost silently, which is
  the failure being fixed.
- **FR-003**: Each consuming prompt MUST state an explicit **encode-don't-paraphrase**
  contract: this material is operating canon to be encoded into the artifact's procedure,
  not background to restate at a summary level.
- **FR-004**: When section 11 is absent or empty, generation MUST behave exactly as it does
  today, producing byte-identical rendered output.
- **FR-005**: The soul, operations and goal-hierarchy generators MUST NOT receive the
  canon. The two exclusions have **distinct rationales that MUST be recorded separately**
  and MUST NOT be collapsed into a single "we decided not to":
  - **Souls — excluded on fitness. Permanent.** `SOUL.md` does reach a running agent, so a
    delivery test would include it. It is excluded because procedure is the wrong *kind* of
    content for a persona file: the artifact's value depends on staying short (roughly forty
    short lines), beyond which the model stops treating it as identity and starts treating
    it as instructions it can debate, and a procedural step belongs in the mandate or the
    heartbeat instead. Threading a long rubric into it would degrade the artifact, and the
    same canon is already carried by the agent mandate and the skill — so the exclusion
    costs nothing.
  - **Operations and goal hierarchy — excluded on delivery. Platform-dependent, revisit
    if import behaviour changes.** Per ADR-022, verified against platform v2026.626.0,
    `OPERATIONS.md` is dropped on import and `COMPANY.md` goals do not survive, so these
    artifacts do not reach a running agent. This MUST be recorded as a statement about
    current platform behaviour, never as a permanent property of these generators.
- **FR-006**: *(Deferred to its own feature — number retained so it cannot be silently
  reused.)* Section-7 customization notes reaching the same four carriers, under a
  **constraint** contract distinct from FR-003's **encode** contract. Deferred, not
  undecided: see "Deferred - Section-7 customization notes" above for the settled
  assessment and the one-variable-at-a-time reason it does not ship here. Nothing in this
  feature may thread section-7 notes to the four carriers.

**Coverage check**

- **FR-007**: The system MUST derive a set of distinctive terms from the section-11 canon.
  Extraction MUST favour **precision over recall** — fewer, more distinctive terms, right
  when it fires — matching the rule already applied to the routine-dependency check.
- **FR-007a**: The extraction rule MUST be calibrated against the **shape of the real
  failing case**, not against a definition argued from first principles. The committed
  fixture MUST be *structurally equivalent* to the section-11 text that produced the
  13-agent bundle — a multi-dimension rubric with named dimensions, a table with class
  labels, and ordinary narrative prose alongside — using invented domain vocabulary.
  Extraction MUST recover the dimension names and class labels and MUST NOT recover the
  narrative prose from that same fixture. Same-source negatives are what make this a
  calibration rather than a keyword list, and they survive sanitisation because the
  discrimination lives in the shape, not the vocabulary.
- **FR-007b**: The real section-11 text MUST NOT enter this repository. It is project canon
  and this is a public, open-source-bound repository — the exclusion holds regardless of how
  benign any individual phrase appears. Final calibration happens outside the repo: the
  operator runs the extractor against the real text during their validation pass. The
  extraction thresholds MUST therefore be **named constants**, so that feedback lands as a
  one-constant change with the reasoning recorded, not a refactor.
- **FR-008**: The system MUST report each uncovered term **by name** — "missing from
  bundle: 'evidence half-life', 'delivery-date scoring'" — never an aggregate verdict such
  as "canon coverage incomplete". A named term is actionable in seconds; a verdict is noise
  the operator learns to skip, which makes the check dead while still appearing alive.
  Naming also makes a slightly-loose extractor tolerable: a false positive is *visibly* a
  false positive rather than an unexplained failure.
- **FR-008a**: The system MUST report **where** each covered term was found, not only that
  it was found. A term surviving in exactly one artifact — or only in an artifact the
  operator knows does not survive import — then presents as a weak result they can judge
  for themselves, without the check encoding any assumption about which artifacts reach a
  running agent.
- **FR-009**: The check MUST be mechanical and deterministic — term presence only, no model
  call, no network access, identical output for identical input.
- **FR-010**: The check MUST be **advisory only**. It reports; it never blocks a run, never
  raises, and never participates in the gate that refuses to write a bundle.
- **FR-011**: The check MUST be **term-oriented, not artifact-oriented** — it asks "does
  this term appear in any rendered file?", never "does this artifact contain canon?". It
  MUST NOT assume every referenced capability is generated by this tool, and MUST NOT carry
  an exemption list to compensate. A referenced platform-provided capability contributes no
  file to the rendered bundle and is therefore outside the scan structurally.
- **FR-012**: The check MUST assert **presence, never fidelity**. Its report MUST NOT
  imply a judgement about whether canon survived as a usable procedure — that is human
  judgement and the check must not appear to make it.
- **FR-013**: The check MUST NOT read, interpret or reason over governance semantics. Its
  entire input is the canon text and the rendered file contents.
- **FR-014**: A term appearing in at least one rendered file MUST be treated as covered,
  regardless of how many files contain it or which files they are.
- **FR-015**: Term matching MUST tolerate ordinary case and surrounding-punctuation
  variation, and MUST NOT report coverage on an accidental substring of an unrelated word.
- **FR-016**: Term extraction MUST NOT treat ordinary English prose as distinctive; a
  section 11 of plain narrative must not produce a wall of warnings. This is the precision
  side of FR-007 and is verified by the same calibration fixture (FR-007a).

**Operator-facing documentation**

- **FR-019**: The input template's section-11 guidance MUST be updated **in the same change**
  as the behaviour, describing what the field now does: what belongs (procedures, rubrics,
  standards, domain decision rules — material agents should follow), what does not (org shape
  is section 7; identity is sections 4–6), and that the material is now **encoded as
  procedure rather than paraphrased as background**, so throwaway notes will surface as
  procedure. Shipping a behaviour change to an input field while the document describing that
  field stays stale is the same defect class this feature exists to fix.
- **FR-020**: That guidance MUST illustrate **shape only** — a named-dimension list, a
  labelled table, with obviously placeholder content. It MUST NOT ship a rich worked example.
  A repository that ships an exemplary rubric will begin producing companies carrying that
  rubric: recycled shape moved upstream into the brief, which Constitution Principle IV rules
  out. The sanitised calibration fixture is a *test* artifact, not documentation, and MUST NOT
  be reused or cross-referenced as such.

**Verification**

- **FR-017**: The suite MUST include a test asserting that content present **only** in
  section 11 reaches at least one generated skill.
- **FR-018**: The suite MUST include a test proving the coverage check **fires** when canon
  is missing — not only that it stays quiet on a clean bundle. A check whose tests assert
  only silence cannot be distinguished from a dead check (ADR-036, the fails-green pattern).

### Key Entities

- **Operating canon**: the brief's section-11 free prose. The operator's residual channel
  for rules, rubrics, thresholds and classification schemes that no structured brief field
  captures. Its defining property is that **nothing else carries it** — if it is not
  threaded, it is gone.
- **Customization notes**: the brief's section-7 prose. Binding directives about org shape
  — roster, headcount, what is scheduled. Partly materialised into structure by org
  planning, unlike operating canon.
- **Canon term**: a distinctive fragment derived from the operating canon, used as the unit
  of the coverage question. Distinctiveness is what separates a signal from noise.
- **Canon carrier**: a generated artifact capable of carrying procedure — a skill, an agent
  mandate, a task, a project.
- **Coverage report**: the advisory list of canon terms that reached no file. A statement
  about reach, carrying no claim about quality.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operating canon stated only in section 11 appears in at least one generated
  skill — the specific failure observed on the 13-agent bundle (a rubric and a threshold
  table producing zero occurrences) cannot recur undetected.
- **SC-002**: Canon that reaches no generated file is reported **by name** on every run,
  reducing the operator's cost of noticing a silent loss from "read ~80 files and remember
  what you wrote" to "read one line and recognise the term". A named term is actionable
  without opening the bundle; an aggregate verdict is not.
- **SC-002a**: Extraction, run against a sanitised fixture structurally equivalent to the
  section-11 text that produced the 13-agent bundle, recovers its dimension names and class
  labels and does not recover its narrative prose — distinctiveness is grounded in the
  *structure* of the case that motivated the work, while the real text stays out of a public
  repository.
- **SC-003**: A bundle whose canon is fully carried produces **zero** canon warnings, so
  the signal stays worth reading.
- **SC-004**: A brief with no section 11 produces output identical to today's, so briefs
  that never used the channel cannot regress.
- **SC-005**: The added generation cost stays at cents scale — under $0.65 per full bundle
  at a pessimistic canon length — comfortably inside the project's under-$2-per-bundle
  target.
- **SC-006**: The coverage check runs to completion with no model call and no network
  access, and returns identical results across repeated runs on the same input.
- **SC-007**: The exclusion rationales remain legible as two different kinds of decision —
  a permanent judgement about artifact fitness, and a revisitable statement about current
  platform import behaviour.

---

## Assumptions

- **Section 11's distinguishing property is that nothing else carries it.** This is what
  justifies threading it wholesale rather than selecting from it: a selector's failure mode
  is silent loss, which is the defect under repair.
- **This feature changes exactly one brief channel.** Section 7 is deferred (FR-006) so
  that the operator's regeneration has one variable: if the output comes back mushy, it is
  the canon contract, not a second channel diluting it.
- **The coverage check scans all rendered files**, not only those that survive import, and
  reports where terms were found rather than filtering by artifact. Narrowing it would
  embed current platform behaviour in the check itself.
- **Calibration is split: the repo holds shapes, the operator holds reality** (FR-007a,
  FR-007b). The committed fixture is structurally equivalent and sanitised; the real
  section 11 never enters the repository, and final threshold confirmation happens during
  the operator's validation pass. This puts the calibration judgement in the same place as
  the did-it-land judgement — with the person who wrote the brief.
- **Verification is by rendered prompt and rendered file map, using a stubbed model
  client.** No real generation run is performed as part of this work.
- **Grading output quality is the operator's**, not this feature's. Whether a rubric
  survived as usable procedure or was smoothed into plausible prose is a judgement only the
  brief's author can make; the regeneration that answers it is theirs to run.
- The advisory reporting channel introduced for earlier collision checks is available at
  the point where the full rendered bundle exists, and is reused rather than replaced.

## Out of Scope

- Running a real generation to validate output quality.
- Any judgement about canon **fidelity** — whether threaded canon was encoded well.
- Governance-model semantics of any kind. This feature's inputs are the brief's free prose
  and the rendered file contents, nothing more.
- Prompt caching of the shared canon block. At cents-scale cost it is complexity for no
  gain.
- Threading canon to the soul, operations or goal-hierarchy generators (FR-005).
- Threading section-7 customization notes to any carrier (FR-006 — deferred to its own
  feature, assessment already settled and recorded above).
