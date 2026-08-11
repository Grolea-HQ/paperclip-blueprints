# Feature Specification: A declared brief schema, and machine-readable results

**Feature Branch**: `020-brief-schema-and-machine-output`

**Created**: 2026-08-11

**Status**: Draft

**Input**: The brief is becoming a programmatic surface as well as a hand-edited file. Three
properties of the current parser make that unsafe: section identity rests on an unvalidated ordinal,
section 11's heading and its parser anchor disagree, and `validate` / `check-canon` emit human prose
only.

## Context

The brief parser keys every field on a section *number* — `sec.get(11)` for the operating canon,
`sec.get(10)` for adapter preferences, and so on — and nothing checks that the section carrying a
number is the section that number is supposed to name. ADR-038 recorded this as "a correctness
constraint wearing a placement costume" and preserved it by convention: append new sections after the
last one. Convention is what this feature replaces with an assertion.

**The failure is silent, and it is unevenly distributed.** Insert one section mid-document and
everything below renumbers. Where the renumbered field is an enum (governance position, use-case
pattern) the brief fails loudly, because a `Literal` or a known-set check rejects the wrong value.
Where the field is optional free text — the operating canon above all — the anchor simply is not
found, the value is dropped, and the brief validates clean **with the canon gone**. That is the exact
silent-loss failure ADR-037 exists to close, reintroduced one layer lower, in the parser rather than
in the threading.

Two further defects share the same root:

- **A duplicate ordinal overwrites silently.** Sections are collected into a mapping keyed by number,
  so two sections numbered 9 leave one survivor and no report.
- **A heading that misses the recognised form is invisible, and its body folds upward.** A section
  boundary is the *next recognised heading*, so a heading written without its period ceases to exist
  and its whole body is absorbed into the preceding section — where its anchors are live for
  matching. The shipped template already depends on this: two unnumbered sections at the end of the
  file currently live inside section 12's parsed body.

**Why identity keys on the ordinal rather than the heading.** Section 11 has been headed at least two
ways in this repository's own history ("Anything else", then "Operating canon") while its parser
anchor stayed fixed. Making heading *text* the identity key would therefore have dropped the canon
from every brief written before the rename — the same failure, relocated. Making an invisible machine
key the identity would change a file format humans hand-write and copy-paste, and would require a
second parsing path plus a rule for partially-keyed briefs. So the ordinal remains the key, and the
heading becomes the thing that *verifies* it: a declared schema stating which heading each ordinal
must carry, so a renumbered brief is an error message instead of a quiet subtraction. Section
reordering stays impossible, as ADR-038 already established; nothing has asked for it, and an
explicit machine key remains a clean additive upgrade if that ever changes.

**Machine-readable results are the other half.** A consumer today has to scrape stdout, and — worse —
must re-derive the composition the CLI performs inline, notably the set of brief fields excluded from
canon extraction. A re-derived copy drifts from the one the tool uses, which reproduces the precision
defect that got the first canon extractor thrown out. The canon states (carried, thin, missing, not
searchable) are already defined; this is serialisation and an owned entry point, not new semantics.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A misaligned brief fails loudly instead of losing a field (Priority: P1)

An operator (or a program) inserts, removes, renames or duplicates a section. The brief is rejected
with a message naming the section that does not line up, rather than parsing successfully with a
field silently absent.

**Why this priority**: It is the safety property the whole feature exists for, and the one the
operator ranked above elegance. Everything else here is convenience by comparison.

**Independent Test**: Take a valid brief; insert a section mid-document so everything below
renumbers; confirm the result is a structural error naming section 11's mismatch — and confirm that
before this feature the same input parsed clean with the operating canon dropped.

**Acceptance Scenarios**:

1. **Given** a brief whose sections have been renumbered by an insertion, **When** it is validated,
   **Then** validation fails naming each ordinal whose heading does not match its declared identity.
2. **Given** a brief with two sections carrying the same number, **When** it is validated, **Then**
   validation fails naming the duplicated ordinal — today one body silently replaces the other.
3. **Given** a brief whose section 11 is headed with a historical spelling ("Anything else"), **When**
   it is validated, **Then** it passes, because the declared schema carries that alias.
4. **Given** a brief whose heading differs only cosmetically from the declared one — different case, a
   dropped "(optional)" suffix, altered trailing punctuation — **When** it is validated, **Then** it
   passes, because comparison is normalised.
5. **Given** any of the briefs already in this repository, including one that stops at section 9,
   **When** they are parsed, **Then** each produces exactly the brief it produces today.
6. **Given** a brief carrying a section numbered beyond the declared range, **When** it is validated,
   **Then** parsing proceeds and an advisory reports the undeclared ordinal.
7. **Given** a brief carrying an undeclared ordinal while an adjacent declared section is absent,
   **When** it is validated, **Then** the advisory additionally names the likely mistyped ordinal and
   the section it appears to have displaced.

---

### User Story 2 - An absorbed heading is caught, not silently merged (Priority: P2)

An unnumbered or malformed heading inserted between sections is reported, rather than dissolving into
the section above it and taking its content along.

**Why this priority**: It is a distinct failure from a mismatched ordinal, and the heading check does
not cover it — a section can absorb a foreign body while its own heading remains perfectly correct.
Left out, it is the residual hole through which the original defect returns.

**Independent Test**: Insert an unnumbered heading after a declared section, with a body line
carrying a recognised anchor; confirm it is reported. Confirm the assertion fires independently — a
section can report an absorption while its heading matches, and can report both faults at once.

**Acceptance Scenarios**:

1. **Given** a brief with an unnumbered heading between two declared sections, **When** it is
   validated, **Then** validation fails naming the absorbing section and the absorbed heading.
2. **Given** a brief whose section heading is malformed such that the section is not recognised,
   **When** it is validated, **Then** the fault is reported as an absorption by the preceding section
   — the mechanism that actually occurred — rather than only as a missing section.
3. **Given** a brief where one section both carries a wrong heading and has absorbed a heading,
   **When** it is validated, **Then** both are reported, because the two assertions are independent.
4. **Given** the shipped template, **When** it is validated, **Then** no absorption is reported,
   because nothing unnumbered follows the last declared section.

---

### User Story 3 - Results are consumable by a program (Priority: P3)

A program runs brief validation or a canon check and receives a structured document it can act on,
without parsing prose and without re-deriving any part of the analysis.

**Why this priority**: It is the stated motivation for the feature, but it is worthless on a surface
that can mis-parse — a machine-readable report of the wrong answer is worse than prose, because it
invites automated trust. Structure first, serialisation second.

**Independent Test**: Run both commands in machine mode against fixtures on two machines with
different environments; compare the two outputs byte for byte; confirm a consumer can distinguish
"the sections do not line up" from "these fields are empty" without pattern-matching any message
text.

**Acceptance Scenarios**:

1. **Given** a brief that fails structurally, **When** validated in machine mode, **Then** the result
   declares the failure class as structural, distinctly from a field-level failure, in a declared
   field rather than in a message string.
2. **Given** the same brief and bundle on two different machines, **When** either command is run in
   machine mode, **Then** the two outputs are byte-identical.
3. **Given** a canon check that finds missing terms, **When** run in machine mode, **Then** each term
   carries its state — carried, thin, missing, or not searchable — and its carriers as
   bundle-relative paths.
4. **Given** a canon check that finds missing terms, **When** it completes, **Then** it reports
   success: findings are advisory and never make the command fail.
5. **Given** a machine-mode run, **When** the output is inspected, **Then** it contains no absolute
   filesystem path and no value that varies by machine.

---

### User Story 4 - A consumer calls in-process rather than shelling out (Priority: P4)

A program obtains the same results by calling the tool directly, getting typed results rather than a
serialised document it must re-parse.

**Why this priority**: It removes a whole class of drift — today the only way to get canon coverage
is to re-implement the composition the CLI performs inline — but a consumer can survive with the
serialised form until it exists.

**Independent Test**: Call the entry point on a brief and a rendered bundle; confirm the results
match the command's machine-mode output exactly; confirm the command itself now goes through that
same entry point, holding no analysis logic of its own.

**Acceptance Scenarios**:

1. **Given** a brief and a rendered bundle, **When** a consumer calls the entry point, **Then** it
   receives typed results equivalent to the command's machine-mode output.
2. **Given** the entry point, **When** the set of brief fields excluded from canon extraction is
   changed, **Then** the change takes effect for both the command and in-process consumers, because
   only one definition exists.
3. **Given** the canon entry point, **When** the code is inspected, **Then** nothing on the
   bundle-validation path that raises can reach it, and it raises nothing of its own for coverage
   findings.

---

### Edge Cases

- A brief with **no numbered sections at all** (an empty or unrelated file) — reported as a
  structural failure naming what was expected, not as a list of missing fields.
- **Content before the first numbered section** — ignored, as today; this is what makes relocating
  the template's checklist above section 1 safe.
- An **optional section absent** (10, 11 or 12) — not a structural error; an in-repo brief stops at
  section 9 and must keep parsing.
- A section present but **empty** — structurally fine; its fields are absent, which is a field-level
  matter reported on a later run.
- A brief that is **both** structurally broken and field-invalid — only the structural failures are
  reported, plus an explicit statement that field validation was not attempted.
- A canon check on a brief with **no section 11 content** — a valid, representable result state, not
  an error and not an empty report indistinguishable from a clean one.
- **Non-ASCII or curly punctuation in a heading** — normalisation must not make two genuinely
  different headings compare equal, nor a heading unequal to itself across encodings.

## Requirements *(mandatory)*

### Functional Requirements

**The declared schema**

- **FR-001**: The system MUST carry a declared schema mapping each brief section ordinal to its
  canonical heading, any historical aliases, and whether the section is required.
- **FR-002**: Heading comparison MUST be normalised — case-insensitive, with a trailing parenthetical
  qualifier disregarded, and whitespace and punctuation runs collapsed — so cosmetic variance passes
  and only genuine renames need an alias.
- **FR-003**: The alias set MUST carry genuine historical renames only. It MUST include section 11's
  earlier spelling, so briefs written before that rename continue to parse.
- **FR-004**: A present section whose heading matches neither its canonical form nor an alias MUST
  produce a structural failure naming the ordinal, the heading found, and the heading expected.
- **FR-005**: Two or more sections carrying the same ordinal MUST produce a structural failure naming
  that ordinal.
- **FR-006**: A required declared section that is absent MUST produce a structural failure. An absent
  optional section MUST NOT.
- **FR-007**: The declared schema MUST be able to render the section headings it validates, so one
  declaration serves both directions.
- **FR-008**: The shipped brief template MUST be verified against the declared schema, such that
  editing either alone fails. This is the mechanism that gives the existing "a change to the brief
  parser carries its template update" convention teeth in the direction it currently misses.
- **FR-009**: A section numbered beyond the declared range MUST be reported as advisory and MUST NOT
  block parsing. Rejecting it would make a brief written against a newer template a hard failure
  against an older tool, which is the opposite of what append-only placement was meant to enable;
  ignoring it would let a mistyped ordinal drop a real section in silence.
- **FR-010**: When an undeclared ordinal appears **and** an adjacent declared section is absent, the
  advisory MUST say so and name the likely mistyped ordinal. This is the case that reproduces this
  feature's own failure class — `## 13.` present while section 12 is missing means the run-policy
  overrides were dropped — and it is distinguishable from the benign cases, since an annotation or a
  newer-template section normally leaves every declared section present.
- **FR-011**: In machine-readable output, an advisory MUST appear as a declared kind rather than a
  message string, so a consumer sets its own severity. This is what makes an advisory safe rather
  than merely lenient: nothing in the tool decides for the consumer that the finding is minor.

**Absorption**

- **FR-012**: A declared section whose body contains a line in heading form MUST produce a structural
  failure naming the absorbing section and the absorbed heading. A line inside a fenced code block
  MUST NOT count: section 11's own guidance carries a fenced block and operating canon may
  legitimately contain markdown examples, so this is a live false positive rather than a theoretical
  one. Both fence characters MUST be handled — backtick and tilde — as MUST fences carrying an info
  string (for example ```` ```markdown ````). Indented code blocks need no handling and MUST NOT
  acquire any: a heading marker cannot match at four spaces of indent. This is stated so it is not
  rediscovered as an apparent omission.
- **FR-013**: FR-012 MUST be asserted independently of FR-004 — evaluated for every section
  regardless of whether its own heading matched, and capable of being reported alongside a heading
  failure for the same section.
- **FR-014**: The brief template MUST be restructured so that no unnumbered heading follows the last
  declared section; its validation checklist and closing guidance MUST move ahead of section 1.
- **FR-015**: The template MUST satisfy FR-012 after restructuring, with no exemption rule of any
  kind — no marker, no "anything after the last declared section is ignored".

**Failure reporting**

- **FR-016**: When any structural failure is found, field validation MUST NOT be attempted and no
  brief object MUST be constructed.
- **FR-017**: The result MUST state explicitly that field validation was not attempted and why, so an
  operator who fixes the structure and then meets field errors does not conclude the fix caused them.
- **FR-018**: Structural failures MUST aggregate among themselves — every misaligned section reported
  in one run, not the first only.
- **FR-019**: Structural and field failures MUST be distinct types sharing a common base, so a caller
  that does not care can handle one thing and a caller that does can separate the two states.

**Machine-readable results**

- **FR-020**: `validate` and the canon check MUST each offer a machine-readable mode emitting a single
  structured document, with no human-oriented text interleaved.
- **FR-021**: Human-oriented output MUST remain the default and MUST be unchanged when the
  machine-readable mode is not requested.
- **FR-022**: Each document MUST declare its own format version.
- **FR-023**: A failure's class MUST appear as a declared field with a fixed vocabulary — never as a
  message string, an exception name, or a flag a consumer must interpret. The same applies to an
  advisory's kind (FR-011).
- **FR-024**: The canon document MUST carry, per extracted term, its text, its owning item where it
  has one, and its state from the fixed set: carried, thin, missing, not searchable — plus the
  carrying files for a term that has them.
- **FR-025**: The canon document MUST represent extraction-level findings (canon present but
  unmarked, the term cap reached, items stated as sentences) distinctly from coverage findings.
- **FR-026**: The canon document MUST be able to represent "the brief states no operating canon" as a
  distinct outcome, not as an empty report indistinguishable from full coverage.
- **FR-027**: No document MUST contain an absolute filesystem path; file references MUST be
  bundle-relative.
- **FR-028**: The `validate` document MUST carry the verdict, the failure class where invalid, the
  findings, any advisories, and an identity summary of the brief's name and slug — and nothing more.
  The identity summary is what makes "human and machine mode agree" checkable, since the human line
  states exactly those two values. Echoing the full parsed brief is excluded: it would duplicate the
  brief model into a versioned wire contract, so every future brief field would pay a synchronisation
  cost here. Providing it behind an opt-in does not avoid that cost, only defers it.

**In-process entry point**

- **FR-029**: The system MUST expose a stable in-process entry point returning typed results for both
  brief validation and canon coverage.
- **FR-030**: Serialisation MUST be a separate step from analysis, so typed results and the
  machine-readable document cannot disagree.
- **FR-031**: The entry point MUST own the composition currently performed inline by the command —
  in particular the set of brief fields excluded from canon extraction — such that exactly one
  definition of it exists.
- **FR-032**: The commands MUST become callers of the entry point, retaining no analysis of their own.

**Splitter correctness (defect fix)**

- **FR-033**: Section splitting MUST use the same definition of a heading as FR-012, and MUST
  therefore ignore heading-form lines inside fenced code blocks. Today a fenced `## 5.` inside a
  brief splits a section, silently corrupting every field below it. This is a defect, not a scope
  addition — nothing would defend the current behaviour — and it is fixed here rather than deferred
  because a splitter and an absorption scan that disagree about what a heading is would be a defect
  of exactly the kind this feature exists to remove.
- **FR-034**: The fix MUST be shown to change no current parse, by the compatibility baselines
  required under INV-003. That evidence is what makes fixing it here safe rather than opportunistic.

**Invariants**

- **INV-001** (determinism): The same inputs MUST produce byte-identical output on any machine. No
  ordering may derive from the process-salted builtin hash or from iterating an unordered collection;
  no result may depend on filesystem case-sensitivity or traversal order. Document key order MUST be
  fixed.
- **INV-002** (advisory): The canon check MUST remain advisory. It reports reach, never quality; it
  MUST NOT be reachable from bundle validation, which raises; and a completed scan MUST report
  success regardless of what it found. Only an operational failure — an unreadable brief or bundle —
  may fail the command.
- **INV-003** (compatibility): Every brief currently on disk MUST parse to exactly what it parses to
  today. No anchor is renamed, no file format changes, and no brief requires migration.

### Key Entities

- **Section schema entry**: one brief section's declared identity — ordinal, canonical heading,
  historical aliases, required or optional.
- **Structural finding**: one way in which a brief's sections fail to line up — its kind (heading
  mismatch, duplicate ordinal, missing required section, absorbed heading), the ordinal it concerns,
  and what was found versus expected.
- **Brief validation result**: validity, the failure class where invalid, the findings, and whether
  field validation was attempted.
- **Canon term result**: one extracted term with its owning item, its coverage state, and its
  carrying files.
- **Canon report**: the term results, extraction-level findings, and the counts by state.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A brief renumbered by a single inserted section is rejected with a message naming the
  misaligned section — where today it is accepted with the operating canon dropped and nothing said.
- **SC-002**: Every brief file currently in the repository, including the one using section 11's
  earlier heading and the one that stops at section 9, produces exactly the parsed result it produces
  today.
- **SC-003**: Each of the four structural fault kinds — mismatched heading, duplicate ordinal,
  missing required section, absorbed heading — is caught, and each is demonstrated by a test that
  fails if that single assertion is removed.
- **SC-004**: A structurally broken brief reports only structural findings, plus one statement that
  field validation was not attempted; zero field-level messages appear.
- **SC-005**: Editing the template's headings without updating the declared schema fails a test, and
  the converse fails the same test.
- **SC-006**: Both commands' machine-readable output is byte-identical across two machines with
  differing environments and locales, for identical inputs.
- **SC-007**: A consumer can distinguish a structural failure from a field failure, and a missing
  canon term from a thin one, using declared fields alone — with no message-text matching anywhere.
- **SC-008**: The canon check reports success on every completed scan, whatever it finds, and remains
  unreachable from bundle validation.
- **SC-009**: The set of brief fields excluded from canon extraction is defined in exactly one place,
  and both the command and an in-process consumer are shown to use it.
- **SC-010**: No machine-readable output contains an absolute path.
- **SC-011**: A brief whose section 12 was mistyped as an undeclared ordinal produces an advisory
  naming both — where today the run-policy overrides are dropped with nothing said — while a brief
  with a genuine extra trailing section produces an advisory that makes no such claim.
- **SC-012**: The `validate` document's identity summary states the same name and slug as the human
  line, verified by a test that compares the two modes rather than asserting each separately.
- **SC-013**: A brief whose operating canon contains a fenced markdown example reports no absorption
  and splits into the same sections it would without the fence — where today the fenced heading
  splits a section and silently displaces every field below it.

## Assumptions

- **Machine mode is opt-in per command, and off by default.** Existing human output stays as it is,
  which keeps every current invocation working unchanged.
- **Sections 1–9 are required; 10, 11 and 12 are optional.** This matches how briefs are used today —
  a brief in this repository stops at section 9 — and the period-less-heading case the operator
  raised is still caught, because that section's body is absorbed by its predecessor and FR-012 fires
  on it. Requiredness is therefore not what closes that hole, and does not need to be widened.
- **Field naming in the machine-readable documents follows this project's own conventions rather than
  the platform's**, since the documents describe briefs and canon, not platform objects.
- **The canon check's exit status is success for any completed scan**, following directly from
  INV-002; only an unreadable brief or bundle fails it. `validate` keeps failing on an invalid brief.
- **The entry point returns typed results and the serialiser is separate**, so in-process consumers
  are not forced through a serialisation round trip.
- **The declared schema covers today's twelve sections.** A future section is added to the schema by
  the change that adds it to the template.

## Out of Scope

- **The pre-anchor discard.** Content written above a section's anchor is silently dropped, because
  the anchor's tail plus everything following it is what gets read. This is a real defect and it needs
  fixing whatever identity keys on — it gets its own specification, so that it cannot be traded away
  inside this one.
- **Section reordering.** Order is defined by the template and append-only placement is a correctness
  property, not a style preference. An explicit machine key remains a clean additive upgrade if
  reordering ever becomes a requirement; choosing ordinal validation now does not foreclose it.
- **Renaming any parser anchor**, including section 11's, since that would break briefs on disk for a
  cosmetic gain.
- **Any change to what the canon check means.** Its states are already defined; this feature
  serialises them.
- **Echoing parsed brief values back to a caller.** A read-back surface is a separate feature with a
  separate contract; see FR-028 for why an opt-in is not a cheaper way to have it.
- **Machine-readable output for `generate` and `preview`.**
