"""The declared brief section schema (feature 020).

Section identity keys on the ORDINAL, and the heading is what verifies it. Keying identity
on heading text was rejected: section 11 was headed "Anything else" before "Operating
canon" while its parser anchor never moved, so a heading-keyed parser would have dropped
the canon from every brief predating the rename.

These tests cover the declaration itself (C1.*), the comparison rule (C2.*), and the shared
fence-aware heading scanner (C3.6, C3.7).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from paperclip_blueprints.models.brief_sections import (
    BRIEF_SECTIONS,
    check_structure,
    heading_lines_in,
    normalise_heading,
    section_for,
)

# --- C1: the declaration ----------------------------------------------------


def test_the_declaration_covers_twelve_contiguous_unique_ordinals() -> None:
    """C1.1 — ordinals 1-12, contiguous and unique."""
    ordinals = [s.ordinal for s in BRIEF_SECTIONS]
    assert ordinals == list(range(1, 13))


def test_sections_one_to_nine_are_required_and_ten_to_twelve_are_optional() -> None:
    """C1.2 — an absent optional section is not a fault.

    `scripts/probe_brief.md` stops at section 9 and must keep parsing, so requiredness
    cannot be widened past 9 without breaking a brief on disk.
    """
    required = {s.ordinal for s in BRIEF_SECTIONS if s.required}
    assert required == {1, 2, 3, 4, 5, 6, 7, 8, 9}


def test_section_eleven_declares_its_earlier_heading_as_an_alias() -> None:
    """C1.3 — the rename that motivated ordinal keying is carried, not forgotten."""
    eleven = section_for(11)
    assert eleven is not None
    assert normalise_heading(eleven.heading) == normalise_heading("Operating canon")
    assert any(normalise_heading(a) == normalise_heading("Anything else") for a in eleven.aliases)


def test_no_two_declared_headings_normalise_to_the_same_value() -> None:
    """C1.4 — normalisation must not merge two distinct sections.

    Stripping a trailing parenthetical is what makes `Use case pattern` match
    `Use case pattern (optional)`; the same rule could collapse a future pair, so the
    declaration asserts it can't rather than trusting inspection.
    """
    seen: dict[str, int] = {}
    for section in BRIEF_SECTIONS:
        for text in (section.heading, *section.aliases):
            key = normalise_heading(text)
            assert key not in seen, (
                f"heading {text!r} (section {section.ordinal}) normalises to the same "
                f"value as section {seen.get(key)}"
            )
            seen[key] = section.ordinal


def test_the_declaration_is_an_ordered_sequence_not_a_set() -> None:
    """INV-001 — output order must never derive from an unordered collection."""
    assert isinstance(BRIEF_SECTIONS, tuple)


def test_section_for_returns_none_beyond_the_declared_range() -> None:
    """A beyond-range ordinal is not a declared section; it is advisory (C4.1)."""
    assert section_for(13) is None
    assert section_for(0) is None


# --- C2: normalised comparison ----------------------------------------------


@pytest.mark.parametrize(
    ("ordinal", "written"),
    [
        (5, "We are not"),  # C2.1 — case
        (5, "WE ARE NOT"),
        (7, "Use case pattern"),  # C2.2 — dropped parenthetical
        (10, "Adapter preferences"),
        (12, "Run-policy overrides"),
        (2, "North star."),  # C2.3 — trailing punctuation
        (3, "Goals  "),
        (1, "Company  name   and  slug"),  # C2.3 — collapsed whitespace
        (11, "Anything else"),  # C1.3 — alias
        (11, "anything else (optional)"),
    ],
)
def test_cosmetic_variance_still_matches_its_declared_section(ordinal: int, written: str) -> None:
    """C2.1-C2.3 — the alias set carries genuine renames, not spelling drift.

    Absorbing cosmetic variance in the comparison is what keeps the alias set small enough
    to stay correct; an alias set that must anticipate spelling is a registry someone has
    to remember to update.
    """
    section = section_for(ordinal)
    assert section is not None
    assert section.matches(written), f"{written!r} should match section {ordinal}"


@pytest.mark.parametrize(
    ("ordinal", "written"),
    [
        (11, "Adapter preferences (optional)"),
        (5, "We are"),
        (4, "We are NOT"),
        (12, "Adapter preferences"),
    ],
)
def test_a_genuinely_different_heading_does_not_match(ordinal: int, written: str) -> None:
    """C2.4 — normalisation loosens comparison without erasing the distinction.

    `We are` and `We are NOT` are the pair most at risk: one is a prefix of the other, and
    a substring-based rule would call them equal.
    """
    section = section_for(ordinal)
    assert section is not None
    assert not section.matches(written)


def test_rendering_a_section_round_trips_through_matching() -> None:
    """C6.1 — one declaration, two directions."""
    for section in BRIEF_SECTIONS:
        rendered = section.render()
        assert rendered.startswith(f"## {section.ordinal}. ")
        assert section.matches(rendered.split(". ", 1)[1])


# --- C3.6/C3.7: the shared fence-aware heading scanner -----------------------


def test_a_plain_heading_line_is_found() -> None:
    assert heading_lines_in("intro\n## Notes\nbody") == ["## Notes"]


@pytest.mark.parametrize(
    ("opening", "closing"),
    [
        ("```", "```"),
        ("~~~", "~~~"),
        ("```markdown", "```"),  # info string on the opening fence only
        ("~~~text", "~~~"),
        ("~~~~", "~~~~"),
        ("````", "````"),
    ],
)
def test_a_heading_inside_a_fenced_block_is_not_a_heading(opening: str, closing: str) -> None:
    """C3.6 — backtick and tilde fences, and fences carrying an info string.

    Section 11's own guidance carries a fenced block and operating canon may legitimately
    contain markdown examples, so this false positive is live rather than theoretical.
    """
    text = f"before\n{opening}\n## Not a heading\n{closing}\nafter"
    assert heading_lines_in(text) == []


def test_scanning_resumes_after_a_fence_closes() -> None:
    """C3.6 — a closed fence must not swallow the rest of the document."""
    text = "```\n## Inside\n```\n## Outside\n"
    assert heading_lines_in(text) == ["## Outside"]


def test_an_unclosed_fence_swallows_the_remainder() -> None:
    """An unterminated fence is treated as open to end of document, which is how markdown
    renderers read it. The alternative — guessing where the author meant it to close —
    would make the scanner's answer depend on a heuristic."""
    assert heading_lines_in("```\n## Inside\nstill inside\n") == []


def test_deeper_headings_are_not_section_level() -> None:
    """C3.6 — `###` cannot absorb anything, because it is not a section boundary."""
    assert heading_lines_in("## Two\n### Three\n#### Four\n") == ["## Two"]


def test_a_single_hash_is_not_section_level() -> None:
    assert heading_lines_in("# One\n## Two\n") == ["## Two"]


def test_an_indented_code_block_needs_no_handling() -> None:
    """C3.7 — asserted so the absence reads as a decision rather than an omission.

    A heading marker cannot match at four spaces of indent, so indented code blocks are
    outside the scanner's reach by construction and no special case is added for them.
    """
    assert heading_lines_in("text\n\n    ## Indented, therefore code\n\ntext") == []


def test_the_scanner_returns_lines_in_document_order() -> None:
    """INV-001 — never an unordered collection."""
    assert heading_lines_in("## A\nx\n## B\ny\n## C") == ["## A", "## B", "## C"]


# --- C3/C4: structural validation ------------------------------------------


def _brief_with(*headings: str) -> str:
    """A document carrying the given heading lines, each with a token body."""
    return "\n\n".join(f"{h}\n\nbody for {h}" for h in headings) + "\n"


def _all_declared() -> list[str]:
    return [s.render() for s in BRIEF_SECTIONS]


def _kinds(findings) -> list[str]:
    return [f.kind for f in findings]


def test_a_correct_document_produces_no_findings() -> None:
    """The baseline the other cases are read against."""
    result = check_structure(_brief_with(*_all_declared()))
    assert result.findings == []
    assert result.advisories == []


def test_a_mismatched_heading_is_reported_with_found_and_expected() -> None:
    """C3.1 — one finding, naming the ordinal, what was found and what was expected."""
    headings = _all_declared()
    headings[10] = "## 11. Adapter preferences (optional)"
    findings = check_structure(_brief_with(*headings)).findings

    assert _kinds(findings) == ["heading_mismatch"]
    assert findings[0].ordinal == 11
    assert findings[0].found == "Adapter preferences (optional)"
    assert findings[0].expected == "Operating canon"


def test_a_renumbering_insertion_reports_every_displaced_section() -> None:
    """C5.3 and the feature's motivating case.

    Inserting one section renumbers everything below it. Before this feature the same
    document parsed clean with the operating canon dropped, because section 11's anchor was
    simply not found and the value fell out of the payload.
    """
    headings = [s.render() for s in BRIEF_SECTIONS if s.ordinal <= 9]
    headings += ["## 10. Something the operator added"]
    headings += [f"## {s.ordinal + 1}. {s.heading}" for s in BRIEF_SECTIONS if s.ordinal >= 10]
    result = check_structure(_brief_with(*headings))

    # 10, 11 and 12 now carry the wrong headings. Section 11 is the one that mattered:
    # its anchor would not be found and the operating canon would fall out of the payload.
    assert _kinds(result.findings) == ["heading_mismatch"] * 3
    assert [f.ordinal for f in result.findings] == [10, 11, 12]
    displaced = next(f for f in result.findings if f.ordinal == 11)
    assert displaced.expected == "Operating canon"
    assert displaced.found == "Adapter preferences (optional)"

    # The shifted section 13 is beyond the declared range: advisory, never a finding.
    assert [a.ordinal for a in result.advisories if a.kind == "undeclared_section"] == [13]


def test_a_duplicate_ordinal_is_reported_rather_than_overwriting() -> None:
    """C3.2 — today the second body silently replaces the first."""
    headings = _all_declared()
    headings.insert(9, "## 9. Operator working pattern")
    findings = check_structure(_brief_with(*headings)).findings

    assert _kinds(findings) == ["duplicate_ordinal"]
    assert findings[0].ordinal == 9


def test_an_absent_required_section_is_reported() -> None:
    """C3.3 — sections 1-9 must exist."""
    headings = [h for h in _all_declared() if not h.startswith("## 6.")]
    findings = check_structure(_brief_with(*headings)).findings

    assert _kinds(findings) == ["missing_required_section"]
    assert findings[0].ordinal == 6
    assert findings[0].expected == "Constraints"


def test_absent_optional_sections_are_not_a_fault() -> None:
    """C3.3, C1.2 — `scripts/probe_brief.md` stops at section 9 and must keep parsing."""
    headings = [s.render() for s in BRIEF_SECTIONS if s.ordinal <= 9]
    assert check_structure(_brief_with(*headings)).findings == []


def test_findings_are_ordered_by_ordinal_not_by_discovery() -> None:
    """C3.9, INV-001 — discovery order depends on scan order, an implementation detail."""
    headings = _all_declared()
    headings[11] = "## 12. Wrong"
    headings[3] = "## 4. Wrong"
    headings[7] = "## 8. Wrong"
    findings = check_structure(_brief_with(*headings)).findings

    assert [f.ordinal for f in findings] == [4, 8, 12]


def test_section_eleven_may_use_its_earlier_heading() -> None:
    """C7.2 — the alias in use, which is why heading text is not the identity key."""
    headings = _all_declared()
    headings[10] = "## 11. Anything else"
    assert check_structure(_brief_with(*headings)).findings == []


# --- C4: beyond-range ordinals ---------------------------------------------


def test_a_beyond_range_ordinal_is_advisory_and_does_not_block() -> None:
    """C4.1 — rejecting would make a newer-template brief fail against an older tool."""
    result = check_structure(_brief_with(*_all_declared(), "## 13. My own notes"))

    assert result.findings == []
    assert [a.kind for a in result.advisories] == ["undeclared_section"]
    assert result.advisories[0].ordinal == 13


def test_a_beyond_range_ordinal_beside_a_missing_section_names_the_likely_typo() -> None:
    """C4.2 — the case that reproduces this feature's own failure class.

    `## 13.` typed where `## 12.` was meant leaves section 12 absent. Section 12 is
    optional, so nothing else fires, and the run-policy overrides are dropped.
    """
    headings = [h for h in _all_declared() if not h.startswith("## 12.")]
    result = check_structure(_brief_with(*headings, "## 13. Run-policy overrides (optional)"))

    kinds = [a.kind for a in result.advisories]
    assert "likely_mistyped_ordinal" in kinds
    typo = next(a for a in result.advisories if a.kind == "likely_mistyped_ordinal")
    assert "13" in typo.message and "12" in typo.message


def test_an_annotation_beside_a_complete_document_is_not_called_a_typo() -> None:
    """C4.3 — annotation and a newer-template section leave every declared section present."""
    result = check_structure(_brief_with(*_all_declared(), "## 13. My own notes"))
    assert [a.kind for a in result.advisories] == ["undeclared_section"]


def test_advisories_do_not_make_a_document_structurally_invalid() -> None:
    """C4.1 — advisory means advisory."""
    result = check_structure(_brief_with(*_all_declared(), "## 14. Notes"))
    assert result.findings == []
    assert result.advisories != []


# --- C3.4/C3.5/C3.8: absorbed headings --------------------------------------


def test_an_unnumbered_heading_is_reported_against_the_section_that_absorbed_it() -> None:
    """C3.4 — the section boundary is the next *numbered* heading, so an unnumbered one
    does not end a section; its body falls inside the section above it, where that
    section's anchors are live for matching."""
    headings = _all_declared()
    document = _brief_with(*headings).replace(
        "body for ## 10. Adapter preferences (optional)",
        "body for ## 10. Adapter preferences (optional)\n\n## Notes\n\nstray content",
    )
    findings = check_structure(document).findings

    assert _kinds(findings) == ["absorbed_heading"]
    assert findings[0].ordinal == 10
    assert findings[0].detail == "## Notes"


def test_a_malformed_section_heading_is_reported_as_an_absorption() -> None:
    """C3.4 — the mechanism that actually occurred.

    `## 11 Operating canon` without its period is not a section heading, so section 11
    does not exist and its body is absorbed by section 10. Reporting only "11 is missing"
    would name a symptom; reporting the absorption names the cause.
    """
    headings = _all_declared()
    headings[10] = "## 11 Operating canon"  # no period
    findings = check_structure(_brief_with(*headings)).findings

    absorbed = [f for f in findings if f.kind == "absorbed_heading"]
    assert len(absorbed) == 1
    assert absorbed[0].ordinal == 10
    assert absorbed[0].detail == "## 11 Operating canon"


def test_absorption_is_reported_even_when_the_heading_matches() -> None:
    """C3.5 — the two assertions are independent.

    This is the residual hole a heading check alone leaves: a section can absorb a foreign
    body while its own heading is perfectly correct, and nothing about the heading would
    reveal it.
    """
    document = _brief_with(*_all_declared()).replace(
        "body for ## 6. Constraints",
        "body for ## 6. Constraints\n\n## An interjection\n\nmore",
    )
    findings = check_structure(document).findings

    assert _kinds(findings) == ["absorbed_heading"]
    assert findings[0].ordinal == 6


def test_one_section_can_report_both_a_mismatch_and_an_absorption() -> None:
    """C3.5 — neither finding suppresses the other."""
    headings = _all_declared()
    headings[5] = "## 6. Something else entirely"
    document = _brief_with(*headings).replace(
        "body for ## 6. Something else entirely",
        "body for ## 6. Something else entirely\n\n## Stray\n\nmore",
    )
    findings = [f for f in check_structure(document).findings if f.ordinal == 6]

    assert _kinds(findings) == ["heading_mismatch", "absorbed_heading"]


def test_a_fenced_heading_in_a_section_body_is_not_an_absorption() -> None:
    """C3.6 — section 11's own guidance carries a fenced block, and operating canon may
    legitimately contain markdown examples."""
    document = _brief_with(*_all_declared()).replace(
        "body for ## 11. Operating canon",
        "body for ## 11. Operating canon\n\n```markdown\n## Example heading\n```\n",
    )
    assert check_structure(document).findings == []


def test_content_before_the_first_section_is_not_absorbed_by_anything() -> None:
    """Text ahead of section 1 belongs to no section, which is what makes relocating the
    template's checklist above section 1 safe."""
    document = "# Company Brief\n\n## Preamble\n\nintro text\n\n" + _brief_with(*_all_declared())
    assert check_structure(document).findings == []


def test_a_fenced_numbered_heading_does_not_split_a_section() -> None:
    """C3.8, FR-033 — the splitter defect.

    A fenced `## 5.` currently ends section 4 and starts a section 5, displacing every
    field below it. The parse must be identical with and without the fenced example.
    """
    from paperclip_blueprints.models.input import _split_sections

    plain = _brief_with(*_all_declared())
    with_fence = plain.replace(
        "body for ## 3. Goals",
        "body for ## 3. Goals\n\n```\n## 5. Not a real section\n```\n",
    )

    assert set(_split_sections(with_fence)) == set(_split_sections(plain))
    assert "Not a real section" in _split_sections(with_fence)[3]
    assert _split_sections(with_fence)[5] == _split_sections(plain)[5]


# --- C6: the template and the schema are one declaration --------------------

_TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "examples" / "input-template.md"


def test_the_shipped_template_carries_exactly_the_declared_headings() -> None:
    """C6.2, C6.3 — one test, both directions.

    This fails if the template's headings are edited without the schema, and fails if the
    schema is edited without the template. It is what gives the convention that a brief
    parser change carries its template update mechanical force in the direction nothing
    else checks.
    """
    template = _TEMPLATE_PATH.read_text(encoding="utf-8")
    numbered = [line for line in heading_lines_in(template) if re.match(r"^##\s+\d+\.", line)]
    assert numbered == [section.render() for section in BRIEF_SECTIONS]


def test_the_shipped_template_is_structurally_sound() -> None:
    """C6.2 — structural validity only.

    A template's fields are deliberately unfilled; that is what makes it a template.
    Requiring them filled would mean carrying example values, which defeats the
    placeholder detection the parser depends on.
    """
    result = check_structure(_TEMPLATE_PATH.read_text(encoding="utf-8"))
    assert result.findings == []
    assert result.advisories == []


def test_nothing_unnumbered_follows_the_last_declared_section_of_the_template() -> None:
    """C6.4 — asserted on the file, with no exemption rule anywhere in the code.

    "Everything after the last declared section is ignored" would be exemption by
    accident: it would exist because the template happened to be shaped that way, and it
    would silently cover a real absorption later.
    """
    template = _TEMPLATE_PATH.read_text(encoding="utf-8")
    headings = heading_lines_in(template)
    last_numbered = max(i for i, line in enumerate(headings) if re.match(r"^##\s+\d+\.", line))
    assert headings[last_numbered + 1 :] == []
