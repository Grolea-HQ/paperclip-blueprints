"""Canon-coverage check (feature 016 / ADR-037) — pure, deterministic, advisory.

The brief's section-11 operating canon is the operator's residual channel: rules, rubrics
and thresholds with no other carrier. If it fails to reach the bundle it disappears
silently, because nothing downstream knows it existed. This module makes that failure
visible.

It answers exactly one question, per term: **does this appear anywhere in the rendered
bundle?** It asserts *presence*, never *fidelity* — whether a rubric survived as usable
procedure is human judgement, and nothing here may appear to make it.

Extraction keys on **markdown structure, not the shape of words.**
------------------------------------------------------------------
The first version of this module inferred canon from typography — hyphenated compounds,
Title-Case runs. Run against a real brief it produced twelve false positives and zero true
positives, because the operator had *already marked* what mattered, using markdown
emphasis, and the rule was busy guessing instead of reading the marks. Two signals carry
canon:

1. **Bold-headed blocks.** A line beginning ``**Some heading.**`` opens a canon item; the
   heading names it.
2. **Enumerated italic inside such a block.** ``(1) *Access difficulty*`` names a
   part of that item.

The enumeration marker is the discriminator, not the italic. Italic alone is used at least
three ways in a real brief — enumerated rubric parts (canon), proper nouns and source names
(noise), and ordinary mid-sentence emphasis (noise) — so extracting every italic span
reproduces a milder version of the original defect. Canon terms are **sentence case**; a
Title-Case rule finds none of them.

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
# their real section-11 text via ``blueprints check-canon`` and reports whether it caught
# the right terms and left the prose alone (ADR-037). Moving any of these is a
# single-constant change — record the reasoning beside it rather than reshaping the rule.

MIN_TERM_CHARS = 6
"""Shortest accepted term. Near-vestigial now that extraction keys on explicit operator
marking rather than word shape; it guards only against stray one-word emphasis."""

MAX_TERMS = 60
"""Cap on reported terms. A report longer than this stops being read, which makes the check
dead while still appearing alive. Hitting the cap is itself warned about — silently
truncating the term list would be the same silent-loss failure this module exists to
report."""

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

SENTENCE_VERBS = frozenset(
    """
    does do did is are was were be been being has have had must should shall will would
    can could may might leaves means applies requires carries happens matters exists
    remains becomes
    """.split()
)
"""Finite verbs that mark a heading as a sentence rather than a name.

A block heading is used as a *probe* — the check asks whether that phrase appears in the
bundle. That works for a name (``The provenance citation format``) and cannot work for a
sentence (``The daily recap does two jobs``): a generated task says "Daily Operations
Recap", never the sentence form, so the probe reports missing however well the canon
landed. A phantom warning that can never clear is worse than no warning.

Sentence-shaped headings are therefore excluded from coverage reporting and **declared**
instead (see :func:`extraction_warnings`) — never silently dropped, which would be the
silent gap this module exists to close. Deliberately tight, and deliberately excluding
noun/verb ambiguities (``set``, ``run``, ``count``): a misclassification is visible in the
declared list, so erring toward "probeable" keeps the failure loud."""


# --- shapes -----------------------------------------------------------------


@dataclass(frozen=True)
class CanonTerm:
    """A distinctive fragment of the operating canon, used as the unit of coverage."""

    text: str
    """As written in the canon, markdown markers stripped. This is what a warning names."""

    normalised: str
    """Casefolded, punctuation-flattened matching key. Never surfaced to the operator."""

    probeable: bool = True
    """Whether this term can meaningfully be searched for in the bundle.

    ``False`` for a sentence-shaped block heading, which no generated artifact would ever
    contain verbatim. Such a term is reported as unprobeable rather than as missing.
    """

    block: str | None = None
    """The bold-headed block this term was enumerated under, if any.

    Carried so a warning can say *which* item a missing part belongs to — "Structural
    comparability" alone is harder to place than "Access difficulty, from 'The
    maintenance-priority rubric'". ``None`` for the block headings themselves.
    """


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

# A bold run at the start of a line opens a canon block. Anchoring to the line start is
# what keeps mid-sentence bold out of the term set.
_BLOCK_HEAD = re.compile(r"^[ \t]*\*\*(?P<head>[^\n]+?)\*\*", re.MULTILINE)

# Italic IMMEDIATELY preceded by an enumeration marker — "(1)", "1." or "1)". The marker is
# the discriminator: unmarked italic is a proper noun or ordinary emphasis, not canon.
_ENUM_ITALIC = re.compile(r"(?:\(\d{1,2}\)|\b\d{1,2}[.)])\s*\*(?P<term>[^*\n]+?)\*")

# A heading names its item in the leading phrase; a dash or comma introduces gloss.
_HEAD_GLOSS = re.compile(r"\s+[—–-]\s+|,\s")

_MARKDOWN_NOISE = re.compile(r"[*_`]+")
_PUNCT = re.compile(r"[-–—_/]+")
_SPACE = re.compile(r"\s+")
_APOSTROPHES = str.maketrans({"’": "'", "‘": "'", "ʼ": "'"})


def _clean(text: str) -> str:
    """Strip markdown markers and normalise apostrophes to their straight form.

    Curly apostrophes are normalised rather than treated as separators: splitting on them
    is what produced orphaned ``s brief leaves open`` fragments under the shape-based rule.
    """
    return _SPACE.sub(" ", _MARKDOWN_NOISE.sub("", text).translate(_APOSTROPHES)).strip()


def normalise(text: str) -> str:
    """Casefold and flatten punctuation, so a hyphenated term still matches its
    spaced form in the bundle."""
    return _SPACE.sub(" ", _PUNCT.sub(" ", _clean(text))).strip().casefold()


def _heading_name(head: str) -> str:
    """Reduce a block heading to the item's name, dropping any trailing gloss.

    ``The Tier C honesty note — this is load-bearing`` names an item called *The Tier C
    honesty note*; the clause after the dash is commentary. Keeping the whole sentence
    would make a poor probe, since a full sentence never appears verbatim in a generated
    artifact — and a term that can never match would report missing on every run.
    """
    name = _HEAD_GLOSS.split(_clean(head), 1)[0]
    return name.rstrip(" .:;,")


def _is_probeable(name: str) -> bool:
    """True when a heading is a name that could plausibly appear in a generated artifact.

    A heading carrying a finite verb is a sentence; a sentence is not a phrase anything
    would restate, so probing for it manufactures a warning that can never clear.
    """
    return not any(word in SENTENCE_VERBS for word in normalise(name).split())


def _is_prose(candidate: str) -> bool:
    words = [w for w in normalise(candidate).split() if w]
    return not words or all(w in COMMON_WORDS for w in words)


def extract_canon_terms(
    canon: str | None,
    *,
    exclude_texts: Iterable[str] = (),
    max_terms: int = MAX_TERMS,
) -> list[CanonTerm]:
    """Derive the canon terms of a section-11 text from its markdown structure.

    Args:
        canon: The brief's section-11 text. ``None`` or blank yields no terms.
        exclude_texts: The brief's other fields. A phrase carried by one of them reaches
            the generators by an existing path, so its coverage says nothing about the
            defect this check guards and would be pure noise. This is the main precision
            lever.
        max_terms: Override for :data:`MAX_TERMS`.

    Returns:
        Terms ordered by **first appearance in the canon** — never by set iteration, which
        would be hash-seed dependent, and never alphabetically, since first-appearance
        order lets the operator reconcile the report against their own section 11 top to
        bottom.
    """
    if not canon or not canon.strip():
        return []

    excluded = {normalise(t) for t in exclude_texts}

    heads = list(_BLOCK_HEAD.finditer(canon))
    # (start offset, surface form, owning block) so ordering follows the source text.
    candidates: list[tuple[int, str, str | None]] = []

    for index, head in enumerate(heads):
        name = _heading_name(head.group("head"))
        if name:
            candidates.append((head.start(), name, None))
        body_end = heads[index + 1].start() if index + 1 < len(heads) else len(canon)
        body = canon[head.end() : body_end]
        for item in _ENUM_ITALIC.finditer(body):
            candidates.append((head.end() + item.start(), _clean(item.group("term")), name))

    candidates.sort(key=lambda c: c[0])

    terms: list[CanonTerm] = []
    seen: set[str] = set()  # membership only — never iterated for output
    for _, surface, block in candidates:
        key = normalise(surface)
        if key in seen or len(surface) < MIN_TERM_CHARS or _is_prose(surface):
            continue
        if any(_contains(text, key) for text in excluded):
            continue
        seen.add(key)
        # Enumerated parts are always probeable; only a heading can be sentence-shaped.
        probeable = True if block is not None else _is_probeable(surface)
        terms.append(CanonTerm(text=surface, normalised=key, block=block, probeable=probeable))
        if len(terms) >= max_terms:
            break
    return terms


def extraction_warnings(
    canon: str | None, terms: Iterable[CanonTerm], *, max_terms: int = MAX_TERMS
) -> list[str]:
    """Report failures of extraction itself, as distinct from failures of coverage.

    Two cases, both of which would otherwise be silent — and a silent zero-result is this
    feature's own defect wearing a new hat:

    **Canon present, nothing extracted.** Now that extraction keys on markdown emphasis,
    that convention is load-bearing: a brief stating canon as unmarked prose yields no
    terms, and a zero-term run that printed nothing would read as "all clear".

    **The cap truncated the list.** Dropping terms silently to stay under a display limit
    loses exactly what the check exists to report.
    """
    lines: list[str] = []
    collected = list(terms)
    if canon and canon.strip() and not collected:
        lines.append(
            "the brief's section 11 has content but no canon items were found — canon is "
            "recognised from markdown emphasis (bold-headed blocks, and enumerated italic "
            "parts within them), so unmarked prose cannot be checked for coverage"
        )
    if len(collected) >= max_terms:
        lines.append(f"canon term list hit its cap of {max_terms}; further terms were not checked")
    unprobeable = [t.text for t in collected if not t.probeable]
    if unprobeable:
        named = ", ".join(repr(name) for name in unprobeable)
        lines.append(
            f"{len(unprobeable)} canon item(s) are stated as sentences rather than names and "
            f"cannot be searched for in the bundle, so their coverage is unknown: {named}"
        )
    return lines


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


def _describe(term: CanonTerm) -> str:
    """Name a term, with its owning block when it has one."""
    if term.block:
        return f"{term.text!r} (from {term.block!r})"
    return repr(term.text)


def canon_warnings(coverage: Iterable[CanonCoverage]) -> list[str]:
    """Render the advisory lines for a coverage result.

    Two kinds only — missing and thin. A fully-carried term produces no line: a check that
    prints a line per term on a healthy bundle floods its own sink, and the data is
    available in the :class:`CanonCoverage` results for anyone who wants it.

    Every line names the specific term. An aggregate verdict ("canon coverage incomplete")
    is not actionable without opening the bundle, and it makes a loose extractor
    indistinguishable from a real finding — whereas a named term shows a false positive to
    be a false positive at a glance.

    Lines state reach and nothing else. They must never imply a judgement about whether the
    canon was encoded usefully; that is the operator's call.
    """
    lines: list[str] = []
    for item in coverage:
        if not item.term.probeable:
            # Declared by extraction_warnings instead; probing a sentence would emit a
            # warning that no amount of correct generation could ever clear.
            continue
        if item.is_missing:
            lines.append(
                f"operating canon term {_describe(item.term)} appears in no generated file "
                "— it is stated in the brief's section 11 and no artifact carries it"
            )
        elif item.is_thin:
            lines.append(
                f"operating canon term {_describe(item.term)} appears in only one file "
                f"({item.carriers[0]})"
            )
    return lines
