"""The in-process entry point (feature 020).

A program consuming this tool should not have to shell out and scrape prose, and — the
sharper problem — should not have to reconstruct the analysis the CLI performs. The set of
brief fields excluded from canon extraction existed in two places, character for character,
before this module: once in the command and once in the renderer. Two copies of the canon
check's main precision lever can drift, and a drifted copy answers a different question than
the one asked while looking like an answer to this one.

So the analysis lives here, returns typed results, and both the command and any in-process
caller go through it. Serialisation is a separate module, so the typed result and the
emitted document cannot disagree.

Nothing here performs network access, reads an environment variable, or touches the
filesystem: :func:`check_canon` takes an already-loaded mapping, which keeps path resolution
where a caller can control it and keeps this layer testable without a bundle on disk.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

from .models.brief_sections import Advisory, StructuralFinding
from .models.input import (
    BriefError,
    BriefStructureError,
    BriefValidationError,
    CompanyBrief,
    parse_brief,
    slug_divergence_warning,
)
from .renderers.canon import (
    CanonCoverage,
    canon_coverage,
    canon_exclusions,
    canon_warnings,
    extract_canon_terms,
    extraction_warnings,
)

FailureClass = Literal["structural", "field"]
CanonState = Literal["carried", "thin", "missing", "not_searchable"]
CanonOutcome = Literal["scanned", "no_canon_stated"]
ExtractionFindingKind = Literal[
    "canon_present_but_unmarked",
    "term_cap_reached",
    "sentence_shaped_items",
]


@dataclass(frozen=True)
class BriefReport:
    """The outcome of validating a brief.

    Returned rather than raised, so a caller need not use exceptions for control flow.
    :func:`parse_brief_strict` is the raising counterpart for callers that want the brief or
    nothing.
    """

    valid: bool
    failure_class: FailureClass | None = None
    structural_findings: tuple[StructuralFinding, ...] = ()
    field_messages: tuple[str, ...] = ()
    fields_checked: bool = True
    """False when structure gated them.

    Carried as data rather than left to the message text: an operator who fixes the
    structure and then meets field errors must be able to tell that the second set was
    never produced the first time, not infer it.
    """
    advisories: tuple[Advisory, ...] = ()
    brief_object: CompanyBrief | None = None
    """The parsed brief, for in-process callers. Never serialised — see
    :mod:`paperclip_blueprints.serialisation`."""

    @property
    def name(self) -> str | None:
        return self.brief_object.name if self.brief_object else None

    @property
    def slug(self) -> str | None:
        return self.brief_object.slug if self.brief_object else None


@dataclass(frozen=True)
class ExtractionFinding:
    """A failure of extraction, as distinct from a failure of coverage."""

    kind: ExtractionFindingKind
    message: str


@dataclass(frozen=True)
class CanonTermResult:
    """One extracted canon term and where it landed."""

    text: str
    block: str | None
    state: CanonState
    carriers: tuple[str, ...] = ()


@dataclass(frozen=True)
class CanonCounts:
    """Term totals by state. Derived from the terms, never accumulated separately."""

    carried: int = 0
    thin: int = 0
    missing: int = 0
    not_searchable: int = 0


@dataclass(frozen=True)
class CanonReport:
    """The outcome of a canon check. Never a failure — reach is reported, not judged."""

    outcome: CanonOutcome
    files_scanned: int = 0
    terms: tuple[CanonTermResult, ...] = ()
    extraction_findings: tuple[ExtractionFinding, ...] = ()
    counts: CanonCounts = field(default_factory=CanonCounts)

    coverage_messages: tuple[str, ...] = ()
    """Human-readable coverage lines, for the CLI's default output.

    Carried on the report rather than recomputed by the caller so there is one computation
    behind both renderings. Deliberately **not** serialised: no consumer may need to match
    on message text, and a document that carried these would invite exactly that.
    """


def _state_of(coverage: CanonCoverage) -> CanonState:
    """Name the state the coverage module already distinguishes.

    Order matters: an unprobeable term is *not searchable*, never *missing*. Probing a
    sentence-shaped heading would manufacture a warning no amount of correct generation
    could clear.
    """
    if not coverage.term.probeable:
        return "not_searchable"
    if coverage.is_missing:
        return "missing"
    if coverage.is_thin:
        return "thin"
    return "carried"


_EXTRACTION_KINDS: tuple[tuple[str, ExtractionFindingKind], ...] = (
    ("no canon items were found", "canon_present_but_unmarked"),
    ("hit its cap", "term_cap_reached"),
    ("stated as sentences", "sentence_shaped_items"),
)


def _classify_extraction(message: str) -> ExtractionFindingKind:
    for marker, kind in _EXTRACTION_KINDS:
        if marker in message:
            return kind
    return "canon_present_but_unmarked"


def validate_brief(markdown: str) -> BriefReport:
    """Validate a brief and return the outcome as a value.

    Args:
        markdown: The brief document.

    Returns:
        A report carrying validity, the failure class where invalid, the findings, any
        advisories, and — for in-process callers — the parsed brief.
    """
    advisories: list[Advisory] = []
    try:
        brief = parse_brief(markdown, warn=None)
    except BriefStructureError as exc:
        return BriefReport(
            valid=False,
            failure_class="structural",
            structural_findings=tuple(exc.findings),
            fields_checked=False,
            advisories=tuple(exc.advisories),
        )
    except BriefValidationError as exc:
        return BriefReport(
            valid=False,
            failure_class="field",
            field_messages=tuple(exc.messages),
            fields_checked=True,
        )

    from .models.brief_sections import check_structure

    advisories.extend(check_structure(markdown).advisories)
    if (warning := slug_divergence_warning(brief)) is not None:
        advisories.append(Advisory(kind="slug_divergence", message=warning))
    return BriefReport(valid=True, advisories=tuple(advisories), brief_object=brief)


def parse_brief_strict(markdown: str) -> CompanyBrief:
    """Parse a brief, raising on any failure.

    Args:
        markdown: The brief document.

    Returns:
        The validated brief.

    Raises:
        BriefError: :class:`BriefStructureError` when the sections do not line up,
            :class:`BriefValidationError` when the fields do not validate. Catching the base
            catches both.
    """
    return parse_brief(markdown)


def check_canon(brief: CompanyBrief | None, files: Mapping[str, str]) -> CanonReport:
    """Locate the brief's operating canon across an already-loaded bundle.

    Advisory by construction: this returns a report and raises nothing, whatever it finds.
    It reports *reach* — whether a term appears anywhere — and never whether the canon
    landed as usable procedure, which is a judgement nothing mechanical may appear to make.

    Args:
        brief: The parsed brief, or ``None``.
        files: The rendered bundle as bundle-relative path → content. A mapping rather than
            a directory, so this performs no filesystem access and a caller decides how a
            bundle is read.

    Returns:
        The report, whose outcome distinguishes "no canon stated" from a scan that found
        nothing.
    """
    if brief is None or not brief.free_text:
        return CanonReport(outcome="no_canon_stated")

    terms = extract_canon_terms(brief.free_text, exclude_texts=canon_exclusions(brief))
    coverage = canon_coverage(terms, files)
    results = tuple(
        CanonTermResult(
            text=item.term.text,
            block=item.term.block,
            state=_state_of(item),
            carriers=tuple(item.carriers),
        )
        for item in coverage
    )
    findings = tuple(
        ExtractionFinding(kind=_classify_extraction(message), message=message)
        for message in extraction_warnings(brief.free_text, terms)
    )
    return CanonReport(
        outcome="scanned",
        files_scanned=len(files),
        terms=results,
        extraction_findings=findings,
        counts=CanonCounts(
            carried=sum(1 for r in results if r.state == "carried"),
            thin=sum(1 for r in results if r.state == "thin"),
            missing=sum(1 for r in results if r.state == "missing"),
            not_searchable=sum(1 for r in results if r.state == "not_searchable"),
        ),
        coverage_messages=tuple(canon_warnings(coverage)),
    )


__all__ = [
    "BriefError",
    "BriefReport",
    "CanonCounts",
    "CanonReport",
    "CanonTermResult",
    "ExtractionFinding",
    "check_canon",
    "parse_brief_strict",
    "validate_brief",
]
