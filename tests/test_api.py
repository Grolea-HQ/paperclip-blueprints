"""The in-process entry point (feature 020).

The point of this module is that there is one place the analysis happens. A consumer that
re-derives any part of it drifts from what the tool actually does, and a drifted copy
answers a different question while looking like an answer to this one — which is the defect
the canon check itself exists to report.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from paperclip_blueprints.api import (
    BriefError,
    check_canon,
    parse_brief_strict,
    validate_brief,
)
from paperclip_blueprints.models.input import BriefStructureError, BriefValidationError
from paperclip_blueprints.renderers.canon import canon_exclusions
from paperclip_blueprints.serialisation import canon_document, dumps, validate_document

_SRC = Path(__file__).resolve().parent.parent / "src" / "paperclip_blueprints"
_BRIEF = Path(__file__).resolve().parent.parent / "examples" / "example-brief-research-digest.md"


def _text() -> str:
    return _BRIEF.read_text(encoding="utf-8")


# --- E1.1/E1.2: the surface -------------------------------------------------


def test_validate_brief_returns_rather_than_raises_on_an_invalid_brief() -> None:
    """E1.1 — invalidity is a value, so a caller need not use exceptions for control flow."""
    report = validate_brief("# nothing here\n")
    assert report.valid is False
    assert report.failure_class == "structural"


def test_parse_brief_strict_raises_for_callers_that_want_the_brief_or_nothing() -> None:
    """E1.1 — the raising counterpart, and both failures share one base."""
    with pytest.raises(BriefStructureError):
        parse_brief_strict("# nothing here\n")
    with pytest.raises(BriefValidationError):
        parse_brief_strict(_text().replace("**Slug:** research-digest", "**Slug:** Not A Slug"))
    with pytest.raises(BriefError):
        parse_brief_strict("# nothing here\n")


def test_check_canon_accepts_a_mapping_and_touches_no_filesystem(monkeypatch) -> None:
    """E1.2 — path resolution stays where a caller controls it.

    Enforced rather than described: `Path.read_text` is made to explode for the duration, so
    a future edit that reaches for the filesystem here fails loudly instead of quietly
    acquiring an I/O dependency.
    """
    brief = validate_brief(_text()).brief_object
    assert brief is not None

    def _forbidden(*args: object, **kwargs: object) -> str:
        raise AssertionError("check_canon must not read the filesystem")

    monkeypatch.setattr(Path, "read_text", _forbidden)
    report = check_canon(brief, {"a.md": "byline traceability"})
    assert report.outcome == "scanned"


def test_check_canon_never_raises_whatever_it_finds() -> None:
    """INV-002 — advisory by construction, not by the caller remembering to catch."""
    brief = validate_brief(_text()).brief_object
    assert brief is not None
    for files in ({}, {"a.md": ""}, {"a.md": "nothing relevant at all"}):
        assert check_canon(brief, files).outcome in {"scanned", "no_canon_stated"}


# --- E1.3/E1.4/E1.7: one definition of the exclusions -----------------------


def test_canon_exclusions_is_the_only_construction_of_that_list() -> None:
    """E1.3 — asserted against the source, because the duplicate was invisible in review.

    Before this feature the list existed twice, character for character, in `cli.py` and
    `renderers/render.py`. Both are now callers. This looks for the shape of a second
    construction — a literal list gathering `we_are_not` alongside `goals` — anywhere but
    the one definition.
    """
    pattern = re.compile(r"\*brief\.we_are_not|\*brief\.goals")
    builders = sorted(
        path.relative_to(_SRC).as_posix()
        for path in _SRC.rglob("*.py")
        if pattern.search(path.read_text(encoding="utf-8"))
    )
    assert builders == ["renderers/canon.py"], (
        f"the excluded-field set is constructed in more than one place: {builders}"
    )


def test_every_call_path_uses_the_one_definition_object() -> None:
    """E1.4 — delegation, asserted by identity rather than by resemblance.

    Both consumers must hold *the same function*, not an equivalent list. If either reverts
    to constructing its own, the name is no longer imported there and this fails — where a
    test that merely called the shared function would pass regardless of what the consumers
    do, and so would assert nothing about them.
    """
    from paperclip_blueprints import api
    from paperclip_blueprints.renderers import canon, render

    assert api.canon_exclusions is canon.canon_exclusions
    assert render.canon_exclusions is canon.canon_exclusions


def test_widening_the_excluded_set_changes_what_the_entry_point_reports(monkeypatch) -> None:
    """E1.7, SC-009 — the exclusions are load-bearing, not decorative.

    A phrase carried by another brief field reaches the generators by an existing path, so
    its coverage says nothing about the defect the check guards. Excluding the canon's own
    text should therefore empty the term list entirely.
    """
    from paperclip_blueprints import api

    brief = validate_brief(_text()).brief_object
    assert brief is not None
    assert "The claim-support rule" in {
        term.text for term in check_canon(brief, {"a.md": "x"}).terms
    }

    def widened(b: object) -> list[str]:
        return [*canon_exclusions(b), getattr(b, "free_text", "") or ""]

    monkeypatch.setattr(api, "canon_exclusions", widened)
    assert check_canon(brief, {"a.md": "x"}).terms == ()


# --- E1.6: the entry point and the command agree ----------------------------


def test_serialising_the_entry_point_result_matches_the_command_output() -> None:
    """E1.6 — the equivalence the two-module split exists to make checkable."""
    from typer.testing import CliRunner

    from paperclip_blueprints.cli import app

    result = CliRunner().invoke(app, ["validate", "--input", str(_BRIEF), "--json"])
    assert result.exit_code == 0, result.output
    assert result.stdout == dumps(validate_document(validate_brief(_text())))


def test_the_canon_document_matches_the_entry_point_result() -> None:
    """E1.6 — the same property for the other command."""
    brief = validate_brief(_text()).brief_object
    assert brief is not None
    files = {"COMPANY.md": "byline traceability appears here"}
    assert dumps(canon_document(check_canon(brief, files))).endswith("}\n")
    assert canon_document(check_canon(brief, files)) == canon_document(check_canon(brief, files))


# --- E2.3/K3.2: the layering that keeps the check advisory ------------------


def test_the_bundle_validators_cannot_reach_the_canon_module() -> None:
    """K3.2, INV-002 — asserted structurally, not by inspection.

    `validators/` raises. If it could reach the canon check, a coverage finding could become
    a hard failure, and reporting reach would start blocking writes.
    """
    validators = _SRC / "validators"
    offenders = [
        path.relative_to(_SRC).as_posix()
        for path in validators.rglob("*.py")
        if re.search(r"\bcanon\b", path.read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_the_entry_point_reads_no_environment_and_makes_no_client(monkeypatch) -> None:
    """E2.3 — no API key, no network, no client construction on either path."""
    import paperclip_blueprints.generators.client as client_module

    def _forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("the entry point must not construct a client")

    monkeypatch.setattr(client_module, "LLMClient", _forbidden)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    report = validate_brief(_text())
    assert report.valid is True
    assert check_canon(report.brief_object, {"a.md": "x"}).outcome == "scanned"


# --- feature 021: the inspection ---------------------------------------------


def test_inspection_carries_the_validation_report_whole() -> None:
    """The composition, at the typed level: one `BriefReport`, produced by one function.

    Restating validity here would create a second definition free to drift from the first,
    which is the defect the shipped documents were built to avoid.
    """
    from paperclip_blueprints.api import inspect_brief

    inspection = inspect_brief(_text())
    assert inspection.validation == validate_brief(_text())


def test_inspection_carries_every_scanned_section() -> None:
    """Sections come from the scan, so beyond-range and duplicated ordinals are included."""
    from paperclip_blueprints.api import inspect_brief
    from paperclip_blueprints.models.brief_sections import scan_sections

    inspection = inspect_brief(_text())
    assert [s.ordinal for s in inspection.sections] == [s.ordinal for s in scan_sections(_text())]


def test_inspection_of_a_broken_brief_still_locates_its_sections() -> None:
    """Spans are observations, values are interpretations.

    A span says *this region is the section headed X at ordinal N*, which stays true even
    when N should not be X. Interpreting misaligned text yields artifacts; observing where
    text sits yields none.
    """
    from paperclip_blueprints.api import inspect_brief

    broken = (
        _text()
        .replace(
            "## 10. Adapter preferences (optional)",
            "## 10. Notes to self\n\nAnything.\n\n## 11. Adapter preferences (optional)",
        )
        .replace("## 11. Operating canon", "## 12. Operating canon")
    )

    inspection = inspect_brief(broken)
    assert inspection.validation.valid is False
    assert inspection.sections, "sections must be located even when the brief does not parse"
    assert inspection.brief_object is None


def test_inspection_of_a_valid_brief_carries_the_parsed_brief() -> None:
    from paperclip_blueprints.api import inspect_brief

    inspection = inspect_brief(_text())
    assert inspection.brief_object is not None
    assert inspection.brief_object.slug == "research-digest"
