"""Typed reports → JSON-ready structures (feature 020).

Separate from :mod:`paperclip_blueprints.api` on purpose: analysis produces typed results,
this turns them into documents, and neither does the other's job. A single module doing both
would make "the document is derived from the typed result" a convention rather than a
structure, and the equivalence test would have nothing to hold onto.

**Determinism is a property of the builder.** Every document is constructed as a literal
dictionary in a fixed order, so key order cannot drift with which branch ran and does not
depend on a ``sort_keys`` argument surviving a future edit. Nothing is derived from
iterating an unordered collection, and no absolute path reaches the output — the bundle
directory a caller supplies is machine-dependent, so only a count and bundle-relative paths
appear.

Every state is readable from a declared vocabulary field. No consumer should ever have to
match on message text; messages are for people.
"""

from __future__ import annotations

import json
from typing import Any

from .api import BriefInspection, BriefReport, CanonReport
from .models.input import CompanyBrief

VALIDATE_SCHEMA = "blueprints.validate/1"
CANON_SCHEMA = "blueprints.check-canon/1"
INSPECT_SCHEMA = "blueprints.inspect/1"


BRIEF_PROJECTION: tuple[tuple[str, str], ...] = (
    ("name", "name"),
    ("slug", "slug"),
    ("description", "description"),
    ("north_star", "northStar"),
    ("goals", "goals"),
    ("we_are", "weAre"),
    ("we_are_not", "weAreNot"),
    ("constraints", "constraints"),
    ("governance_position", "governancePosition"),
    ("use_case_pattern", "useCasePattern"),
    ("use_case_notes", "useCaseNotes"),
    ("hours_per_week", "hoursPerWeek"),
    ("capital_monthly_eur", "capitalMonthlyEur"),
    ("capital_setup_eur", "capitalSetupEur"),
    ("routine_timezone", "routineTimezone"),
    ("adapter_preferences", "adapterPreferences"),
    ("run_policy_preferences", "runPolicyPreferences"),
    ("free_text", "freeText"),
)
"""Brief model field → document key, one entry per field.

Explicit rather than a model dump. The wire contract has to be stable independently of the
model: dumping would make every model edit a wire change by default, with nowhere to mark a
field internal and no way to keep a rename from breaking every consumer — while the version
number kept reading the same.

A test asserts this covers every field on the model, so a new field fails the suite until it
is deliberately projected or deliberately excluded. That test cannot see a *transposition*,
since it walks this same table; only a fixture whose per-field values are obviously
distinguishable can.
"""


def validate_document(report: BriefReport) -> dict[str, Any]:
    """Build the ``validate`` document.

    Carries the verdict, the failure class, the findings, any advisories, and — only when
    valid — an identity summary of name and slug. Not the full parsed brief: that would
    duplicate the brief model into a versioned wire contract, so every future brief field
    would pay a synchronisation cost here.

    Args:
        report: The result of :func:`paperclip_blueprints.api.validate_brief`.

    Returns:
        A JSON-ready mapping. Keys present on every document regardless of outcome, so a
        consumer never needs defensive access; ``brief`` is the sole exception and appears
        only when there is a brief to describe.
    """
    document: dict[str, Any] = {
        "schema": VALIDATE_SCHEMA,
        "valid": report.valid,
        "failureClass": report.failure_class,
        "fieldsChecked": report.fields_checked,
        "structuralFindings": [
            {
                "kind": finding.kind,
                "ordinal": finding.ordinal,
                "found": finding.found,
                "expected": finding.expected,
                "detail": finding.detail,
            }
            for finding in report.structural_findings
        ],
        "fieldMessages": list(report.field_messages),
        "advisories": [
            {"kind": advisory.kind, "ordinal": advisory.ordinal, "message": advisory.message}
            for advisory in report.advisories
        ],
    }
    if report.brief_object is not None:
        document["brief"] = {"name": report.name, "slug": report.slug}
    return document


def canon_document(report: CanonReport) -> dict[str, Any]:
    """Build the ``check-canon`` document.

    Serialises states the canon module already distinguishes. ``outcome`` separates "the
    brief states no operating canon" from a scan that found nothing, which are different
    facts that would otherwise render identically.

    Args:
        report: The result of :func:`paperclip_blueprints.api.check_canon`.

    Returns:
        A JSON-ready mapping carrying a file count rather than any path of its own.
    """
    return {
        "schema": CANON_SCHEMA,
        "outcome": report.outcome,
        "filesScanned": report.files_scanned,
        "counts": {
            "carried": report.counts.carried,
            "thin": report.counts.thin,
            "missing": report.counts.missing,
            "notSearchable": report.counts.not_searchable,
        },
        "terms": [
            {
                "text": term.text,
                "block": term.block,
                "state": term.state,
                "carriers": list(term.carriers),
            }
            for term in report.terms
        ],
        "extractionFindings": [
            {"kind": finding.kind, "message": finding.message}
            for finding in report.extraction_findings
        ],
    }


def inspect_document(inspection: BriefInspection) -> dict[str, Any]:
    """Build the ``inspect`` document.

    The validation half is :func:`validate_document`'s output **verbatim**, not a restatement
    — one definition of what a failure is, and a change to that document appears here
    automatically. The two ``schema`` versions are independent: a new brief field bumps this
    document, never the one it embeds.

    ``sections`` is present whatever the outcome; ``brief`` is ``null`` unless parsing
    succeeded. Spans are observations and values are interpretations, so only the second is
    gated.

    Args:
        inspection: The result of :func:`paperclip_blueprints.api.inspect_brief`.

    Returns:
        A JSON-ready mapping. Its key set does not vary with outcome, so a consumer never
        needs defensive access.
    """
    return {
        "schema": INSPECT_SCHEMA,
        "validation": validate_document(inspection.validation),
        "sections": [
            {
                "ordinal": section.ordinal,
                "heading": section.heading,
                "span": {"start": section.span.start, "end": section.span.end},
            }
            for section in inspection.sections
        ],
        "brief": _brief_values(inspection.brief_object),
    }


def _brief_values(brief: CompanyBrief | None) -> dict[str, Any] | None:
    """Project a parsed brief onto its document keys, or ``None`` when there is none."""
    if brief is None:
        return None
    return {key: getattr(brief, field) for field, key in BRIEF_PROJECTION}


def dumps(document: dict[str, Any]) -> str:
    """Render a document as text, deterministically.

    ``sort_keys`` is deliberately not used: keys are already in a deliberate order, and
    sorting would scatter related fields while hiding careless construction rather than
    exposing it. The byte-identity tests catch what sorting would have papered over.

    Args:
        document: A JSON-ready mapping from one of the builders above.

    Returns:
        The document with a single trailing newline, safe to write as UTF-8.
    """
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"
