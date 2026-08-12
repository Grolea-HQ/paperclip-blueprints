# Feature Specification: Section spans, and an inspect document

**Feature Branch**: `021-section-spans-and-inspect`

**Created**: 2026-08-12

**Status**: Draft

**Input**: A programmatic consumer holds briefs as text and renders a structured view over them. It needs two things it cannot re-derive safely: where each section sits in the source, and the parsed values.

## Context

Nothing that ships locates a section in the source. The scan computes heading offsets and
discards them on the next line — they exist to let a section body be sliced from the original
rather than rejoined from split lines, and they are not carried anywhere a caller can reach.
A consumer that needs boundaries must re-derive them with a second regex, which is a second
definition of where a section starts, free to drift from the parser's. Feature 020 exists to
remove exactly that class of disagreement.

Parsed values have the same shape of problem across a process boundary. In-process a caller
gets a `CompanyBrief`; out-of-process it must scrape human output or re-implement the parser.

**Spans cannot promise to reproduce values.** On a brief with LF endings every parsed value
happens to be a verbatim substring of the source. On the same brief with CRLF endings the
multi-line ones are not: the anchored-block reader splits and rejoins with `\n`, normalising
line endings inside the value. List items lose their bullet marker and integers discard
non-digits. So "the value is a slice of the source" is a property of the current fixtures,
not of the parser — and a span offering that guarantee would be false first on inputs nobody
tests. Section *bodies* are genuine slices; values are not.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A section can be located and reproduced exactly (Priority: P1)

A consumer holding the brief as bytes can slice out any section's body using the reported
span and get exactly the body the tool reports, character for character.

**Why this priority**: It is the capability. Everything else here is delivery.

**Independent test**: For every section of a brief, slice the source bytes over the reported
span, decode, and compare to the reported body. Run it on a brief carrying CRLF endings and
an astral character, since a brief with neither proves only that it works on the fixtures.

**Acceptance Scenarios**:

1. **Given** a brief, **When** its sections are scanned, **Then** each carries a span whose
   slice of the source decodes to exactly that section's body.
2. **Given** a brief with CRLF line endings, **When** a section's span is sliced, **Then** it
   reproduces the body — the guarantee does not depend on line-ending style.
3. **Given** a brief containing a character outside the Basic Multilingual Plane, **When** a
   span is sliced, **Then** it reproduces the body — offsets do not shift with encoding width.
4. **Given** any section, **When** its span is read, **Then** it covers the body only and
   never the heading line.

---

### User Story 2 - Locations and verdict arrive together, out of process (Priority: P2)

A consumer runs one command and receives one document carrying both what the tool made of
the brief and where each section sits.

**Why this priority**: A span a consumer cannot obtain is not a capability. This is the
channel, and it is useless without US1 being true.

**Independent test**: Run the command against a brief; confirm the response carries the
validation result and the section list, and that the validation half is identical to what the
existing validate command emits for the same input.

**Acceptance Scenarios**:

1. **Given** a brief, **When** the command runs, **Then** one document is emitted carrying the
   validation result and the section list.
2. **Given** the same brief, **When** both this command and the existing validation command
   run, **Then** the validation content is identical — one definition, not two.
3. **Given** a change to the validation document's shape, **When** this document is produced,
   **Then** it carries the change automatically, because it embeds rather than restates.
4. **Given** either document, **When** its version is read, **Then** the two version numbers
   are independent of each other.

---

### User Story 3 - Parsed values without re-parsing (Priority: P3)

A consumer obtains the brief's field values from the same response, without reimplementing
the parser or scraping prose.

**Why this priority**: The values are obtainable today in-process, so this closes a gap for
out-of-process callers rather than enabling something impossible.

**Independent test**: Run the command on a valid brief; confirm every field of the parsed
brief is present under a stable name. Add a field to the brief model and confirm the suite
fails until the new field is deliberately projected or deliberately excluded.

**Acceptance Scenarios**:

1. **Given** a valid brief, **When** the document is produced, **Then** it carries the brief's
   field values.
2. **Given** an invalid brief, **When** the document is produced, **Then** it carries no
   values — values read from text that failed to parse are artifacts.
3. **Given** a new field on the brief model, **When** the suite runs, **Then** it fails until
   that field is projected or explicitly excluded.
4. **Given** two projected fields whose positions were transposed, **When** the suite runs,
   **Then** it fails — the fixture's values are distinguishable enough to expose a swap.

---

### User Story 4 - Locations survive a brief that does not parse (Priority: P4)

A consumer receives section locations even when the brief is structurally broken, so it can
show where the problem is.

**Why this priority**: It is the case a consumer meets first and the moment locations are most
useful. Separate from US2 because the natural reading of "structure gates fields" would
suppress it, and a suppressed capability is indistinguishable from an absent one.

**Independent test**: Run the command on a renumbered brief; confirm the section list is fully
populated and the values are absent, in the same response.

**Acceptance Scenarios**:

1. **Given** a structurally broken brief, **When** the document is produced, **Then** the
   section list is present and complete.
2. **Given** the same brief, **When** the document is produced, **Then** no values are present.
3. **Given** a brief carrying a section numbered beyond the declared range, **When** the
   section list is read, **Then** that section appears in it.
4. **Given** a brief where one section has absorbed an unnumbered heading, **When** the section
   list is read, **Then** that section appears with its span covering its whole body, absorbed
   content included — the span reports what is there, not what should be.

---

### Edge Cases

- **An empty section body** — a span that is empty (`start == end`) rather than absent, so a
  consumer never has to distinguish "no body" from "no span".
- **A brief with no sections at all** — an empty section list, not an error; the validation
  half already reports the structural failure.
- **A section whose body is entirely whitespace** — the span delimits the reported body, so an
  empty reported body gets an empty span.
- **A duplicated ordinal** — both occurrences appear in the section list with their own spans,
  since the list reports what is in the file.
- **A brief that is valid but has no operating canon** — the value is absent rather than empty,
  matching what the parser produced.

## Requirements *(mandatory)*

### Functional Requirements

**Section spans**

- **FR-001**: Every scanned section MUST carry a span locating its body in the source.
- **FR-002**: Span offsets MUST be **UTF-8 byte offsets** into the source document. Not code
  points: a consumer slicing a byte offset natively in a UTF-16 language breaks on the first
  em dash — which these briefs contain in quantity — so a missing conversion fails during
  development. Code-point offsets slice correctly in such a language until a character outside
  the Basic Multilingual Plane appears, which is the version that ships.
- **FR-003**: Spans MUST be half-open, `[start, end)`, and the contract MUST say so — the
  off-by-one is the other failure that is silent.
- **FR-004**: A span MUST cover the section **body only**, never the heading line. Heading text
  is structural identity, so a consumer able to rewrite a heading could undo the schema check;
  a body-span replacement cannot change which section it is.
- **FR-005**: A span MUST delimit exactly the body as reported, so slicing the source over the
  span and decoding it yields that body with no further trimming.
- **FR-006**: FR-005 MUST be verified by slicing and comparing, on a fixture carrying **both**
  CRLF line endings and a character outside the Basic Multilingual Plane. Every brief in the
  repository is LF and non-astral, so a test over existing briefs would establish only what the
  feature-020 baselines established.
- **FR-007**: The contract MUST state the negative beside the positive: a span is a byte range
  into the source as UTF-8, half-open, covering the body — with **no claim about headings and
  no claim about values**. A consumer reading only the positive half will assume the rest.
- **FR-008**: Value-level spans MUST NOT be emitted in any form, including as locations without
  a reproduction guarantee. A weak variant beside a strong one is eventually used as the strong
  one, and it fails on the inputs least likely to be tested.
- **FR-009**: The specification MUST record that value spans are blocked on the pre-anchor
  discard work, which owns the anchored-block reader's line-ending rejoin. Stating the
  dependency is what stops it being rediscovered.

**The inspect document**

- **FR-010**: A new command MUST provide this document. It MUST NOT be a flag on the existing
  validation command, because one command emitting two document shapes forces a consumer to
  branch on which it got.
- **FR-011**: The command MUST be named for what it does under both outcomes. A name meaning
  "parse" is incoherent for a command that emits a document precisely because parsing failed,
  and that is the first case a consumer meets.
- **FR-012**: The document MUST **embed the validation document verbatim**, produced by the
  same serialiser, rather than restating validity. One definition of what a failure is.
- **FR-013**: The document MUST declare its own format version, independent of the embedded
  document's.
- **FR-014**: Brief values MUST appear only when parsing succeeded.
- **FR-015**: The section list MUST appear whenever the document is produced, including when
  the brief fails structurally. **Spans are observations; values are interpretations.** A span
  says *this region is the section headed X at ordinal N*, which remains true even when N
  should not be X. Structure gating exists because interpreting misaligned text yields
  artifacts; observing where text sits yields none.
- **FR-016**: The section list MUST include every scanned section — beyond-range ordinals,
  duplicated ordinals, and sections carrying absorbed headings included. Filtering it to the
  declared twelve would turn an observation into an interpretation.
- **FR-017**: The command MUST exit non-zero when the brief is invalid and zero when it is
  valid, with the failure class read from the embedded document rather than from the status.
- **FR-018**: The document MUST contain no absolute filesystem path.

**Projecting the values**

- **FR-019**: Values MUST reach the document through an **explicit projection**, one entry per
  field, never by dumping the model. The wire contract has to be stable independently of the
  model, or the version number describes something that changed without it.
- **FR-020**: Projected field names MUST follow the casing of the two shipped documents.
- **FR-021**: A test MUST assert the projection covers every field on the brief model, so a new
  field fails the suite until it is deliberately projected or deliberately excluded.
- **FR-022**: The projection fixture MUST give every projected field a value obviously
  distinguishable from every other field's. An exhaustiveness test and a round-trip check both
  walk the projection's own table and therefore share its defects; a transposition is invisible
  to both, and only the fixture can expose it.

**Entry point**

- **FR-023**: The in-process entry point MUST expose this as a typed result, following the
  established split: analysis returns types, a separate serialiser produces the document, so
  the two cannot disagree.
- **FR-024**: The command MUST be a caller of that entry point, holding no analysis of its own.

**Reading the source**

- **FR-025**: Brief files MUST be read without newline translation, on every path that reads a
  brief. Text-mode reading translates CRLF to LF by default, so on a CRLF brief the string
  parsed is not the file: byte offsets computed against it would be shifted by one byte per
  preceding line, and a consumer slicing the file it holds would silently get the wrong region.
  "The source" in FR-002 and FR-005 is only true once this holds.
- **FR-026**: Every command MUST read a brief the same way. Reading faithfully for the new
  command alone would let two commands parse different strings for one file and disagree about
  it — the defect class this line of work exists to remove.
- **FR-027**: The change MUST be shown to be additive for parsed values. Every value path
  already passes through line-splitting, which discards line terminators, and rejoins with a
  newline — so no value gains a carriage return and no generated bundle changes. Only section
  bodies, which are raw slices, differ on a CRLF brief, and their fidelity is the point. This
  is asserted rather than assumed, because it is the whole basis for the change being additive.

**Invariants**

- **INV-001** (determinism): identical inputs MUST produce byte-identical output on any
  machine, verified across separate processes rather than within one.
- **INV-002** (compatibility): the existing validation and canon commands MUST behave exactly
  as they do today, in both their human and machine modes.
- **INV-003** (gating): field values are gated on successful parsing; observations are not.

### Key Entities

- **Span**: a half-open UTF-8 byte range into the source, locating one section's body.
- **Scanned section**: an ordinal, the heading as written, the body, and the body's span.
- **Brief inspection**: the validation result, the section list, and — when valid — the brief's
  field values.
- **Projection**: the mapping from brief model fields to their names in the document.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every section of every brief in the repository, slicing the source bytes over
  the reported span and decoding reproduces the reported body exactly.
- **SC-002**: SC-001 also holds for a brief with CRLF endings and for a brief containing a
  character outside the Basic Multilingual Plane, each proven by a fixture that carries it.
- **SC-003**: A consumer can locate every section of a structurally broken brief, and receives
  no field values for it, from a single response.
- **SC-004**: The validation content of the inspect document is identical to the validation
  command's output for the same brief, compared directly rather than asserted separately.
- **SC-005**: Adding a field to the brief model fails the suite until the field is projected or
  explicitly excluded.
- **SC-006**: Transposing two entries in the projection fails the suite.
- **SC-007**: Two runs on the same brief, in separate processes with differing environments,
  produce byte-identical output.
- **SC-008**: No emitted document contains an absolute path.
- **SC-009**: The existing validation and canon commands produce byte-identical output to what
  they produce today, in both modes.
- **SC-010**: No span is emitted for any value, in any form.
- **SC-011**: A brief with CRLF endings parses to the same field values as the same brief with
  LF endings — only its section bodies differ, and only by their line terminators.
- **SC-012**: A bundle generated from a CRLF brief is byte-identical to one generated from the
  same brief with LF endings.

## Assumptions

- **The new command has a human mode as well as a machine mode**, consistent with the other
  commands, with the machine mode opt-in. The human mode lists sections with their ordinals and
  byte ranges.
- **The source of truth for offsets is the file's bytes**, decoded as UTF-8 with no newline
  translation (FR-025). A brief that is not valid UTF-8 is out of scope; the existing reader
  already assumes UTF-8.
- **Section spans are computed during the existing scan**, which already derives the offsets it
  currently discards, rather than by a second pass.
- **An empty body yields an empty span** rather than an absent one, so a consumer has one shape
  to handle.

## Dependencies

- **Value spans are blocked on the pre-anchor discard work.** That specification owns the
  anchored-block reader, whose split-and-rejoin normalises line endings inside multi-line
  values. Until that is fixed, no value can carry a span with a reproduction guarantee, and a
  span without one is excluded by FR-008.

## Out of Scope

- **Value-level spans**, per FR-008 and the dependency above.
- **Heading spans.** A consumer able to locate and replace a heading can undo the structural
  identity check that feature 020 established.
- **Editing or writing back.** This feature reports locations; applying an edit is the
  consumer's concern.
- **Line and column positions.** We do not agree with a consumer on what a line is: the
  standard library's line splitting treats several additional characters as line breaks, where
  a consumer splitting on carriage-return/newline does not.
- **Any change to the validation or canon documents**, beyond the inspect document embedding
  the first of them.
