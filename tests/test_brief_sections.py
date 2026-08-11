"""The declared brief section schema (feature 020).

Section identity keys on the ORDINAL, and the heading is what verifies it. Keying identity
on heading text was rejected: section 11 was headed "Anything else" before "Operating
canon" while its parser anchor never moved, so a heading-keyed parser would have dropped
the canon from every brief predating the rename.

These tests cover the declaration itself (C1.*), the comparison rule (C2.*), and the shared
fence-aware heading scanner (C3.6, C3.7).
"""

from __future__ import annotations

import pytest

from paperclip_blueprints.models.brief_sections import (
    BRIEF_SECTIONS,
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
