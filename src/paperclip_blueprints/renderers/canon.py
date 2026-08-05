"""Canon-coverage check (feature 016 / ADR-037) — pure, deterministic, advisory.

The brief's section-11 operating canon is the operator's residual channel: rules, rubrics
and thresholds with no other carrier. If it fails to reach the bundle it disappears
silently, because nothing downstream knows it existed. This module makes that failure
visible.

It answers exactly one question, per term: **does this appear anywhere in the rendered
bundle?** It asserts *presence*, never *fidelity* — whether a rubric survived as usable
procedure is human judgement, and nothing here may appear to make it.

Three properties are load-bearing and must survive any future edit:

**Term-oriented, not artifact-oriented.** The question is "does this term appear in any
file?", never "does this artifact contain canon?". A referenced platform-provided
capability contributes no ``SKILL.md`` to the rendered map and is therefore outside the
scan *structurally* — not by an exemption entry that would have to be maintained
(ADR-019's standing constraint). This module must never reason over the built-in
capability set.

**Advisory, never fatal.** Results flow to ``render_files``' ``warn`` sink. This module is
never imported by ``validators/``, which raises.

**Deterministic across processes.** No builtin ``hash()``, and no output is derived by
iterating an unordered set — set iteration order for strings is ``PYTHONHASHSEED``
dependent, so such code agrees with itself throughout a single-process suite and is
non-reproducible in the field (ADR-036, "The sibling class: state a single-process suite
cannot see"). Terms are ordered by first appearance in the canon; carrier paths are
sorted.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

# --- calibration constants --------------------------------------------------
#
# Final calibration happens OUTSIDE this repository: the operator runs extraction against
# their real section-11 text and reports whether it caught the right terms and left the
# prose alone (ADR-037). Moving any of these three is a single-constant change — record
# the reasoning beside it rather than reshaping the rule.

MIN_TERM_CHARS = 8
"""Shortest accepted term. Guards against short capitalised fragments reading as canon."""

MAX_TERMS = 40
"""Cap on reported terms. A report longer than this stops being read, which makes the
check dead while still appearing alive."""

COMMON_WORDS = frozenset(
    """
    a an and are as at be been but by can could do does for from had has have how i if in
    into is it its may might must no not of on or our should so than that the their them
    then there these they this those to too us was we were what when where which while
    who why will with would you your every each all any more most some such only just
    also very much many few own same other another next last first second third
    """.split()
)
"""Ordinary English. A candidate made only of these is prose, not canon."""


# --- shapes -----------------------------------------------------------------


@dataclass(frozen=True)
class CanonTerm:
    """A distinctive fragment of the operating canon, used as the unit of coverage."""

    text: str
    """As written in the canon. This is what a warning names."""

    normalised: str
    """Casefolded, punctuation-flattened matching key. Never surfaced to the operator."""


@dataclass(frozen=True)
class CanonCoverage:
    """Where one canon term was found in the rendered bundle."""

    term: CanonTerm
    carriers: list[str]
    """Bundle-relative paths of every file containing the term, sorted."""

    @property
    def is_missing(self) -> bool:
        """True when no rendered file carries the term."""
        return not self.carriers

    @property
    def is_thin(self) -> bool:
        """True when exactly one file carries the term.

        An honest mechanical proxy for a weak result. It is deliberately *not* a claim
        about which artifacts reach a running agent — the warning names the file and the
        operator applies that knowledge, so the check itself cannot go stale as the
        platform changes.
        """
        return len(self.carriers) == 1


# --- extraction -------------------------------------------------------------

_HYPHENATED = re.compile(r"\b[A-Za-z]+(?:-[A-Za-z]+)+\b")
_QUOTED = re.compile(r"[\"'“‘]([A-Za-z][^\"'”’\n]{2,60})[\"'”’]")
_TITLE_RUN = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b")
_SENTENCE_START = re.compile(r"(?:^|[.!?:]\s+|\n\s*)$")

_PUNCT = re.compile(r"[-_/]+")
_SPACE = re.compile(r"\s+")


def normalise(text: str) -> str:
    """Casefold and flatten punctuation so ``Delivery-Date`` matches ``delivery date``."""
    return _SPACE.sub(" ", _PUNCT.sub(" ", text)).strip().casefold()


def _is_prose(candidate: str) -> bool:
    words = [w for w in normalise(candidate).split() if w]
    return not words or all(w in COMMON_WORDS for w in words)


def extract_canon_terms(
    canon: str | None,
    *,
    exclude_texts: Iterable[str] = (),
    max_terms: int = MAX_TERMS,
) -> list[CanonTerm]:
    """Derive the distinctive terms of a section-11 canon, precision first.

    Precision over recall is deliberate, matching the rule already applied to the
    routine-dependency check: fewer, more distinctive terms, right when they fire. An
    over-eager extractor produces a wall of warnings the operator learns to skip, which is
    operationally the same as no check at all.

    Args:
        canon: The brief's section-11 text. ``None`` or blank yields no terms.
        exclude_texts: The brief's other fields. A phrase carried by one of them reaches
            the generators by an existing path, so its coverage says nothing about the
            defect this check guards and would be pure noise. This is the main precision
            lever.
        max_terms: Override for :data:`MAX_TERMS`.

    Returns:
        Terms ordered by **first appearance in the canon** — never by set iteration,
        which would be hash-seed dependent, and never alphabetically, since first-appearance
        order lets the operator reconcile the report against their own section 11 top to
        bottom.
    """
    if not canon or not canon.strip():
        return []

    excluded = {normalise(t) for t in exclude_texts}

    # (start offset, surface form) so ordering follows the source text.
    candidates: list[tuple[int, str]] = []
    for match in _HYPHENATED.finditer(canon):
        if any(part[:1].isupper() for part in match.group(0).split("-")):
            candidates.append((match.start(), match.group(0)))
    for match in _QUOTED.finditer(canon):
        candidates.append((match.start(1), match.group(1)))
    for match in _TITLE_RUN.finditer(canon):
        # Skip sentence-initial runs: "Never advance an enquiry" is prose that happens to
        # start with a capital, not a named thing.
        if _SENTENCE_START.search(canon[: match.start()]):
            continue
        candidates.append((match.start(), match.group(0)))

    candidates.sort(key=lambda pair: pair[0])

    terms: list[CanonTerm] = []
    seen: set[str] = set()  # membership only — never iterated for output
    for _, surface in candidates:
        key = normalise(surface)
        if key in seen or len(surface) < MIN_TERM_CHARS or _is_prose(surface):
            continue
        if any(_contains(text, key) for text in excluded):
            continue
        seen.add(key)
        terms.append(CanonTerm(text=surface, normalised=key))
        if len(terms) >= max_terms:
            break
    return terms


# --- coverage ---------------------------------------------------------------


def _contains(haystack_normalised: str, needle_normalised: str) -> bool:
    """Word-boundary match, so an accidental substring never reads as coverage."""
    pattern = r"\b" + r"\s+".join(re.escape(w) for w in needle_normalised.split()) + r"\b"
    return re.search(pattern, haystack_normalised) is not None


def canon_coverage(terms: Iterable[CanonTerm], files: Mapping[str, str]) -> list[CanonCoverage]:
    """Locate each canon term across every rendered file.

    Every file in the map is scanned; no artifact kind is excluded, weighted or
    privileged. Narrowing the scan to artifacts that survive import would bake current
    platform behaviour into a mechanical checker — instead the carriers are reported and
    the reader applies that knowledge.

    Args:
        terms: The extracted canon terms, in report order.
        files: The rendered bundle, path → content.

    Returns:
        One result per term, in the order given, each carrying its **sorted** carriers.
    """
    normalised_files = {path: normalise(content) for path, content in files.items()}
    results: list[CanonCoverage] = []
    for term in terms:
        carriers = sorted(
            path
            for path, content in normalised_files.items()
            if _contains(content, term.normalised)
        )
        results.append(CanonCoverage(term=term, carriers=carriers))
    return results


def canon_warnings(coverage: Iterable[CanonCoverage]) -> list[str]:
    """Render the advisory lines for a coverage result.

    Two kinds only — missing and thin. A fully-carried term produces no line: a check
    that prints a line per term on a healthy bundle floods its own sink, and the data is
    available in the :class:`CanonCoverage` results for anyone who wants it.

    Every line names the specific term. An aggregate verdict ("canon coverage
    incomplete") is not actionable without opening the bundle, and it makes a loose
    extractor indistinguishable from a real finding — whereas a named term shows a false
    positive to be a false positive at a glance.

    Lines state reach and nothing else. They must never imply a judgement about whether
    the canon was encoded usefully; that is the operator's call.
    """
    lines: list[str] = []
    for item in coverage:
        if item.is_missing:
            lines.append(
                f"operating canon term {item.term.text!r} appears in no generated file — "
                "it is stated in the brief's section 11 and no artifact carries it"
            )
        elif item.is_thin:
            lines.append(
                f"operating canon term {item.term.text!r} appears in only one file "
                f"({item.carriers[0]})"
            )
    return lines
