# Contract — the declared brief section schema

Postconditions asserted by `tests/test_brief_sections.py`, `tests/test_models.py` and
`tests/test_brief_parity.py`.

## The declaration

**C1.1** The schema declares twelve sections, ordinals 1–12, contiguous and unique.

**C1.2** Sections 1–9 are required; 10–12 are optional. An absent optional section produces no
finding (FR-006).

**C1.3** Section 11 declares the alias `Anything else` alongside its canonical `Operating canon`
(FR-003).

**C1.4** No two declared headings, including aliases, normalise to the same value (FR-002).

## Normalised comparison

**C2.1** Comparison is case-insensitive: `## 5. We are not` matches the canonical `We are NOT`.

**C2.2** A trailing parenthetical qualifier is disregarded: `## 7. Use case pattern` matches
`Use case pattern (optional)`.

**C2.3** Trailing punctuation and repeated internal whitespace are disregarded.

**C2.4** Normalisation never makes two genuinely different declared headings compare equal (C1.4 is
the standing assertion of this).

## Structural findings

**C3.1** A present section whose heading matches neither canonical nor alias produces exactly one
`heading_mismatch`, naming the ordinal, the heading found and the heading expected (FR-004).

**C3.2** Two sections carrying the same ordinal produce exactly one `duplicate_ordinal` for that
ordinal (FR-005). Before this feature, one body silently replaced the other.

**C3.3** An absent required section produces exactly one `missing_required_section` (FR-006).

**C3.4** A declared section whose body carries a line matching `^##\s` outside a fenced code block
produces exactly one `absorbed_heading`, naming the absorbing ordinal and the absorbed heading text
(FR-012).

**C3.5** `absorbed_heading` is evaluated independently of heading matching: a section whose heading
is correct still reports absorption, and a section can report both findings at once (FR-013).

**C3.6** A `##` line inside a fenced code block produces no finding, and does not split a section
(FR-012, FR-033). Asserted for each fence form:

- backtick fences (```` ``` ````) and tilde fences (`~~~`);
- fences carrying an info string (```` ```markdown ````);
- a fence closing correctly, so text after it is scanned again.

**C3.7** An indented code block receives no special handling, and none is added: `^##` cannot match
at four spaces of indent. Asserted so the absence reads as a decision rather than an omission.

**C3.8** A brief containing a fenced `## 5.` splits into the same sections it would without the
fence, and every field below it parses to the same value (FR-033, SC-013). Before this feature the
fenced line splits a section and displaces those fields silently.

**C3.9** Findings are ordered by ordinal, then by a fixed kind order — never by discovery order
(INV-001).

## Beyond-range ordinals

**C4.1** A section numbered beyond the declared range does not block parsing and produces an
`undeclared_section` advisory (FR-009).

**C4.2** When a beyond-range ordinal is present and an adjacent declared section is absent, a
`likely_mistyped_ordinal` advisory is produced additionally, naming both ordinals (FR-010).

**C4.3** When every declared section is present, C4.2's advisory is not produced — an annotation or a
newer-template section does not read as a typo (FR-010).

## Structure gates fields

**C5.1** When any structural finding exists, no brief object is constructed and no field message is
produced (FR-016).

**C5.2** The result records that field validation was not attempted, as data rather than as prose
only (FR-017).

**C5.3** Structural findings aggregate: a brief with three misaligned sections reports three findings
in one run (FR-018).

**C5.4** `BriefStructureError` and `BriefValidationError` are distinct types sharing the base
`BriefError`; catching the base catches both (FR-019).

## Bidirectionality and the template

**C6.1** The schema renders each section's heading line, and re-parsing rendered output yields the
same declaration (FR-007).

**C6.2** The shipped `examples/input-template.md` satisfies the schema **structurally** — every
declared section present, every heading matching, no absorption (FR-008, FR-015).

Structural validity only, stated explicitly because "satisfies the schema" is otherwise ambiguous
between this and full validity. A template's fields are deliberately unfilled; that is what makes it
a template, and requiring them filled would mean carrying example values, which defeats the
placeholder detection the parser depends on and changes the file's purpose. Structure-gating already
draws this line: structure is meaningful on its own, and absent fields are a separate question asked
later.

**C6.3** C6.2 fails if the template's headings are edited without the schema, and fails if the schema
is edited without the template. One test, both directions.

**C6.4** After restructuring, no unnumbered heading follows the last declared section of the template
(FR-014), and no exemption rule of any kind exists in the code (FR-015).

## Compatibility

**C7.1** Each brief file in the repository parses to a result byte-identical to its frozen
pre-change baseline: `examples/input-template.md`, `examples/example-brief-indie-game-studio.md`,
`examples/example-brief-research-digest.md`, `scripts/probe_brief.md` (INV-003, SC-002).

**C7.2** A brief using section 11's earlier heading parses with its canon intact (C1.3 in use).

**C7.3** A brief that stops at section 9 parses without a structural finding (C1.2 in use).

**C7.4** No parser anchor is renamed and no brief requires migration.
