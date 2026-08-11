"""The declared brief section schema (feature 020).

The brief parser keys every field on a section *number* — ``sec.get(11)`` for the operating
canon, ``sec.get(10)`` for adapter preferences. Nothing checked that the section carrying a
number was the section that number names, so a document renumbered by one insertion parsed
successfully with a field silently absent. Where the renumbered field is an enum the brief
fails loudly; where it is optional free text the anchor is simply not found and the value
is dropped.

This module declares what each ordinal must be, so the ordinal can be verified rather than
trusted.

**Why the ordinal stays the key.** Section 11 was headed "Anything else" before "Operating
canon" while its ``**Other context:**`` anchor never moved. Keying identity on heading text
would therefore have dropped the canon from every brief predating the rename — the same
silent loss, relocated. An invisible machine key would change a file format written and
copy-pasted by hand, and would need a second parsing path plus a rule for partially keyed
documents. So the ordinal keys, the heading verifies, and nothing on disk migrates.

**Anchors are not unique across sections.** ``overrides`` keys both section 10 and section
12; ``choice`` keys both 7 and 8. The ordinal is the only thing distinguishing those pairs,
which is why verifying it matters more than it would if each anchor stood alone.

**One definition of a heading.** :func:`heading_lines_in` is used both by the section
splitter and by the absorption check. A splitter and an absorption scan that disagreed
about what a heading is would be a defect of exactly the kind this module exists to remove.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# A trailing qualifier is presentation, not identity: `Use case pattern (optional)` and
# `Use case pattern` name the same section. Stripped before punctuation flattening, which
# would otherwise turn the parentheses into spaces and leave the qualifier behind.
_TRAILING_PARENTHETICAL = re.compile(r"\s*\([^()]*\)\s*$")

_PUNCTUATION = re.compile(r"[-–—_/,.:;!?\"'’‘“”]+")
_WHITESPACE = re.compile(r"\s+")

# Up to three leading spaces still opens a fence, per ordinary markdown. Four would make it
# an indented code block, which this scanner never needs to consider (see below).
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")

# Section level exactly. `###` and deeper are not boundaries and cannot absorb anything;
# `#` is not a section either. Anchored with no leading whitespace allowed, which is what
# puts indented code blocks outside this scanner's reach by construction rather than by a
# special case that would have to be maintained.
_SECTION_LEVEL = re.compile(r"^##\s")


def normalise_heading(text: str) -> str:
    """Reduce a heading to its comparison form.

    Case, a trailing parenthetical qualifier, punctuation and repeated whitespace are all
    presentation. Absorbing them here is what keeps the alias set carrying genuine renames
    only — an alias set that must also anticipate spelling is a registry someone has to
    remember to update, and forgetting is silent.

    Deliberately *not* shared with ``renderers.canon.normalise``. That function flattens
    hyphenation so a canon term matches its spaced form in a bundle; stripping a trailing
    parenthetical would be wrong there. Sharing them would share a name over two
    behaviours, and give either one a second caller able to pull it.

    Args:
        text: The heading as written, without its ``## N.`` prefix.

    Returns:
        The casefolded comparison form.
    """
    stripped = _TRAILING_PARENTHETICAL.sub("", text.strip())
    flattened = _PUNCTUATION.sub(" ", stripped)
    return _WHITESPACE.sub(" ", flattened).strip().casefold()


@dataclass(frozen=True)
class BriefSection:
    """One declared section: what its ordinal must be headed, and whether it must exist."""

    ordinal: int
    """The identity key. Every field lookup in the parser already uses it."""

    heading: str
    """Canonical heading text, without the ``## N.`` prefix."""

    aliases: tuple[str, ...] = ()
    """Genuine historical renames only.

    Not spelling variants — :func:`normalise_heading` absorbs those. An alias exists when a
    section was deliberately renamed and briefs written before the rename must keep
    parsing.
    """

    required: bool = True
    """Whether an absent section is a fault.

    Sections 10-12 are optional: a brief in this repository stops at section 9, and an
    operator who states no adapter preferences, no operating canon and no run-policy
    overrides has written a complete brief.
    """

    def matches(self, written: str) -> bool:
        """Whether a heading as written names this section.

        Args:
            written: The heading text found in a brief, without its ``## N.`` prefix.

        Returns:
            True when it normalises to this section's canonical heading or any alias.
        """
        key = normalise_heading(written)
        return key == normalise_heading(self.heading) or any(
            key == normalise_heading(alias) for alias in self.aliases
        )

    def render(self) -> str:
        """Emit this section's heading line.

        The second direction of one declaration: the schema that validates a brief's
        headings also produces the template's, so the two cannot drift apart without a test
        failing.

        Returns:
            The full heading line, e.g. ``## 11. Operating canon``.
        """
        return f"## {self.ordinal}. {self.heading}"


BRIEF_SECTIONS: tuple[BriefSection, ...] = (
    BriefSection(1, "Company name and slug"),
    BriefSection(2, "North star"),
    BriefSection(3, "Goals"),
    BriefSection(4, "We are"),
    BriefSection(5, "We are NOT"),
    BriefSection(6, "Constraints"),
    BriefSection(7, "Use case pattern (optional)"),
    BriefSection(8, "Governance spectrum position"),
    BriefSection(9, "Operator working pattern"),
    BriefSection(10, "Adapter preferences (optional)", required=False),
    BriefSection(11, "Operating canon", aliases=("Anything else",), required=False),
    BriefSection(12, "Run-policy overrides (optional)", required=False),
)
"""The declaration, in ordinal order.

A tuple rather than a set or a dict iterated for output: ordering that derives from an
unordered collection agrees with itself throughout a single-process test suite and is
non-reproducible in the field.
"""

_BY_ORDINAL = {section.ordinal: section for section in BRIEF_SECTIONS}


def section_for(ordinal: int) -> BriefSection | None:
    """Return the declared section for an ordinal, or ``None`` if it is beyond the range.

    Args:
        ordinal: The section number found in a brief.

    Returns:
        The declaration, or ``None`` — which is not a fault. A beyond-range ordinal is
        advisory: rejecting it would make a brief written against a newer template a hard
        failure against an older tool.
    """
    return _BY_ORDINAL.get(ordinal)


def heading_lines_in(text: str) -> list[str]:
    """Return every section-level heading line in ``text``, in document order.

    Fenced code blocks are skipped. A ``##`` line inside a fence is not a heading: the
    brief template's own section 11 carries a fenced block, and operating canon may
    legitimately contain markdown examples, so this false positive is live rather than
    theoretical.

    Both backtick and tilde fences are handled, as are fences carrying an info string
    (```` ```markdown ````). A fence closes on a marker of the same character and at least
    the same length with nothing after it; an unterminated fence runs to the end of the
    document, which is how a markdown renderer reads it — guessing where the author meant
    it to close would make this function's answer depend on a heuristic.

    Indented code blocks need no handling and are given none: ``^##`` cannot match at four
    spaces of indent, so they are outside this scanner's reach by construction.

    Args:
        text: Any span of a brief — a whole document, or one section's body.

    Returns:
        The heading lines, right-stripped, in the order they appear.
    """
    found: list[str] = []
    fence: tuple[str, int] | None = None

    for line in text.splitlines():
        marker = _FENCE.match(line)
        if fence is not None:
            if marker is not None:
                char, length = fence
                run = marker.group(1)
                # A closing fence carries no info string.
                closes = run[0] == char and len(run) >= length and not line.strip()[len(run) :]
                if closes:
                    fence = None
            continue
        if marker is not None:
            run = marker.group(1)
            fence = (run[0], len(run))
            continue
        if _SECTION_LEVEL.match(line):
            found.append(line.rstrip())

    return found
