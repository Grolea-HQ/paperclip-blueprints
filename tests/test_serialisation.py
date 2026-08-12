"""The machine-readable documents (feature 020).

These serialise states that already exist — the four canon coverage states, the two failure
classes — rather than defining new ones. What is new is that they are *stable*: versioned,
byte-identical for identical inputs on any machine, and readable from declared vocabulary
fields with no message-text matching anywhere.

Determinism here is a property of the builder, not of a flag: documents are constructed as
literal dictionaries in a fixed order, so nothing depends on a `sort_keys` argument
surviving a future edit.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from paperclip_blueprints.api import check_canon, validate_brief
from paperclip_blueprints.serialisation import canon_document, dumps, validate_document

_REPO_ROOT = Path(__file__).resolve().parent.parent
_GOOD_BRIEF = _REPO_ROOT / "examples" / "example-brief-research-digest.md"


def _brief_text() -> str:
    return _GOOD_BRIEF.read_text(encoding="utf-8")


def _renumbered() -> str:
    """A brief whose sections have been displaced by one insertion."""
    return (
        _brief_text()
        .replace(
            "## 10. Adapter preferences (optional)",
            "## 10. Notes to self\n\nAnything.\n\n## 11. Adapter preferences (optional)",
        )
        .replace("## 11. Operating canon", "## 12. Operating canon")
        .replace("## 12. Run-policy overrides (optional)", "## 13. Run-policy overrides (optional)")
    )


# --- V2: the validate document ----------------------------------------------


def test_a_valid_brief_documents_its_identity_and_nothing_more() -> None:
    """V2.5, FR-028 — name and slug only.

    Echoing the full parsed brief would duplicate the brief model into a versioned wire
    contract, so every future brief field would pay a synchronisation cost here.
    """
    document = validate_document(validate_brief(_brief_text()))

    assert document["valid"] is True
    assert document["failureClass"] is None
    assert document["fieldsChecked"] is True
    assert set(document["brief"]) == {"name", "slug"}


def test_a_structural_failure_declares_its_class_and_findings() -> None:
    """V2.2, V2.3 — a declared vocabulary, never a message string."""
    document = validate_document(validate_brief(_renumbered()))

    assert document["valid"] is False
    assert document["failureClass"] == "structural"
    assert document["fieldsChecked"] is False
    kinds = {finding["kind"] for finding in document["structuralFindings"]}
    assert kinds == {"heading_mismatch"}
    assert [f["ordinal"] for f in document["structuralFindings"]] == [10, 11, 12]


def test_a_structural_failure_carries_no_field_messages() -> None:
    """V2.4 — the gate, visible in the document rather than only in the exception."""
    document = validate_document(validate_brief(_renumbered()))
    assert document["fieldMessages"] == []


def test_a_field_failure_declares_the_other_class() -> None:
    """V2.2 — the two states a consumer must tell apart."""
    broken = _brief_text().replace("**Slug:** research-digest", "**Slug:** Not A Slug")
    document = validate_document(validate_brief(broken))

    assert document["failureClass"] == "field"
    assert document["fieldsChecked"] is True
    assert document["structuralFindings"] == []
    assert document["fieldMessages"] != []


def test_a_valid_brief_omits_no_declared_key() -> None:
    """V3.2 — key set is fixed by construction, not by which branch ran.

    A consumer that reads `structuralFindings` must find it on every document, including a
    clean one; a key that appears only on failure forces defensive access everywhere.
    """
    valid = validate_document(validate_brief(_brief_text()))
    invalid = validate_document(validate_brief(_renumbered()))
    assert set(valid) - {"brief"} == set(invalid)


def test_the_document_declares_its_format_version() -> None:
    """V2.1 — a stable contract states which contract it is."""
    assert validate_document(validate_brief(_brief_text()))["schema"] == "blueprints.validate/1"


# --- K2: the canon document -------------------------------------------------

_EXISTING_CANON = """\
**The claim-support rule.** Every claim inherits the tier of its weakest support, \
and that tier travels with the claim into the published issue.
(1) *Byline traceability* — whether a named person stands behind the claim.
(2) *Corroboration depth* — how many unrelated outlets carry it independently.
(3) *Correction history* — whether the outlet has amended this story before."""


def _with_canon(replacement: str) -> str:
    """Swap the example brief's section-11 content for `replacement`.

    The fixture ships real marked-up canon, so these cases replace it rather than appending
    — appending would leave the original terms in every result and make each assertion
    about a mixture rather than the case it names.
    """
    assert _EXISTING_CANON in _brief_text(), "fixture canon changed; update this test"
    return _brief_text().replace(_EXISTING_CANON, replacement)


_CANON = """**The provenance citation format.** Every claim carries its source inline.

**The maintenance-priority rubric.** Scored on two dimensions.
(1) *Access difficulty* — how hard the source is to reach.
(2) *Structural comparability* — whether the figures line up."""


def _brief_with_canon() -> str:
    return _with_canon(_CANON)


def test_a_brief_with_no_canon_is_a_distinct_outcome() -> None:
    """K2.1, FR-026 — not an empty scan indistinguishable from full coverage.

    Section 11 is dropped entirely rather than emptied. An emptied section still yields the
    `---` rule that follows it as `free_text`, because the anchored block runs to the end of
    the section — existing behaviour, unrelated to this feature, and not the state being
    tested here.
    """
    text = _brief_text()
    start = text.index("## 11. Operating canon")
    end = text.index("## 12. Run-policy overrides")
    brief = validate_brief(text[:start] + text[end:]).brief_object
    assert brief is not None and brief.free_text is None

    document = canon_document(check_canon(brief, {}))
    assert document["outcome"] == "no_canon_stated"
    assert document["terms"] == []


def test_each_term_carries_one_of_the_four_declared_states() -> None:
    """K2.2 — the states the module already distinguishes, named."""
    brief = validate_brief(_brief_with_canon()).brief_object
    assert brief is not None
    files = {"skills/x/SKILL.md": "We use the provenance citation format for every claim."}
    document = canon_document(check_canon(brief, files))

    states = {term["state"] for term in document["terms"]}
    assert states <= {"carried", "thin", "missing", "not_searchable"}
    by_text = {term["text"]: term for term in document["terms"]}
    assert by_text["The provenance citation format"]["state"] == "thin"
    assert by_text["Access difficulty"]["state"] == "missing"


def test_carriers_are_bundle_relative_and_sorted() -> None:
    """K2.4, FR-027 — the bundle's own path appears nowhere."""
    brief = validate_brief(_brief_with_canon()).brief_object
    assert brief is not None
    files = {
        "z/LAST.md": "the provenance citation format",
        "a/FIRST.md": "the provenance citation format",
    }
    document = canon_document(check_canon(brief, files))
    carriers = next(
        t["carriers"] for t in document["terms"] if t["text"] == "The provenance citation format"
    )
    assert carriers == ["a/FIRST.md", "z/LAST.md"]


def test_counts_agree_with_the_terms_they_summarise() -> None:
    """A summary that can disagree with its detail is a second source of truth."""
    brief = validate_brief(_brief_with_canon()).brief_object
    assert brief is not None
    document = canon_document(check_canon(brief, {"a.md": "nothing relevant"}))

    counted = document["counts"]
    for state, key in (
        ("carried", "carried"),
        ("thin", "thin"),
        ("missing", "missing"),
        ("not_searchable", "notSearchable"),
    ):
        assert counted[key] == sum(1 for t in document["terms"] if t["state"] == state)


def test_extraction_findings_are_distinct_from_coverage() -> None:
    """K2.5 — extraction failing is a different condition from a term not landing."""
    brief = validate_brief(
        _with_canon("Plain prose stating rules with no markup at all.")
    ).brief_object
    assert brief is not None
    document = canon_document(check_canon(brief, {"a.md": "x"}))

    assert document["terms"] == []
    assert [f["kind"] for f in document["extractionFindings"]] == ["canon_present_but_unmarked"]


def test_the_canon_document_declares_its_format_version() -> None:
    """K2.1 — as above, for the other document."""
    brief = validate_brief(_brief_with_canon()).brief_object
    document = canon_document(check_canon(brief, {}))
    assert document["schema"] == "blueprints.check-canon/1"


# --- V3/K4: determinism -----------------------------------------------------


@pytest.mark.parametrize("build", ["validate", "canon"])
def test_serialising_twice_produces_identical_bytes(build: str) -> None:
    """V3.1, K4.1 — the same inputs, the same bytes."""
    if build == "validate":
        first = dumps(validate_document(validate_brief(_brief_text())))
        second = dumps(validate_document(validate_brief(_brief_text())))
    else:
        brief = validate_brief(_brief_with_canon()).brief_object
        assert brief is not None
        files = {"b.md": "the provenance citation format", "a.md": "access difficulty"}
        first = dumps(canon_document(check_canon(brief, files)))
        second = dumps(canon_document(check_canon(brief, dict(reversed(list(files.items()))))))
    assert first == second


def test_key_order_does_not_vary_with_content() -> None:
    """V3.2 — fixed by construction, so it cannot drift with which branch ran."""
    valid = list(validate_document(validate_brief(_brief_text())))
    invalid = list(validate_document(validate_brief(_renumbered())))
    assert valid[: len(invalid)] == invalid


def test_no_document_contains_an_absolute_path() -> None:
    """V2.7, K2.6, FR-027, SC-010 — nothing machine-dependent reaches the wire."""
    brief = validate_brief(_brief_with_canon()).brief_object
    assert brief is not None
    rendered = dumps(validate_document(validate_brief(_brief_text()))) + dumps(
        canon_document(check_canon(brief, {"a.md": "x"}))
    )
    assert str(_REPO_ROOT) not in rendered
    assert "/Users/" not in rendered
    assert not any(line.strip().startswith('"/') for line in rendered.splitlines())


def test_output_ends_with_exactly_one_newline_and_is_utf8_safe() -> None:
    """V3.4, K4.4 — a file a consumer can append to or diff without surprises."""
    rendered = dumps(validate_document(validate_brief(_brief_text())))
    assert rendered.endswith("}\n")
    assert not rendered.endswith("\n\n")
    rendered.encode("utf-8")


def test_documents_round_trip_through_json() -> None:
    """Whatever is built must actually be serialisable — no dataclasses, no tuples that
    only look like lists until something reads them."""
    document = validate_document(validate_brief(_renumbered()))
    assert json.loads(dumps(document)) == document


def test_documents_are_identical_across_processes_with_different_hash_seeds(tmp_path) -> None:
    """INV-001, SC-006 — the cross-machine property, made structural.

    Ordering derived from iterating a set agrees with itself throughout a single-process
    suite and diverges in the field, because string hashing is salted per process. Every
    in-process determinism test above is therefore blind to exactly the defect that matters
    most; only separate interpreters with different `PYTHONHASHSEED` values can see it.
    """
    script = tmp_path / "emit.py"
    script.write_text(
        "from pathlib import Path\n"
        "from paperclip_blueprints.api import check_canon, validate_brief\n"
        "from paperclip_blueprints.serialisation import canon_document, dumps, validate_document\n"
        f"text = Path({str(_GOOD_BRIEF)!r}).read_text(encoding='utf-8')\n"
        "report = validate_brief(text)\n"
        "files = {'b.md': 'byline traceability', 'a.md': 'correction history',\n"
        "         'c.md': 'byline traceability and correction history'}\n"
        "print(dumps(validate_document(report)), end='')\n"
        "print(dumps(canon_document(check_canon(report.brief_object, files))), end='')\n",
        encoding="utf-8",
    )

    outputs = set()
    for seed in ("0", "1", "12345", "99999"):
        env = {**os.environ, "PYTHONHASHSEED": seed}
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            check=True,
            env=env,
            cwd=_REPO_ROOT,
        )
        outputs.add(result.stdout)
    assert len(outputs) == 1, "output varies with PYTHONHASHSEED — an ordering derives from a set"


# --- feature 021: the inspect document ---------------------------------------


def _inspect(source: str) -> dict:
    from paperclip_blueprints.api import inspect_brief
    from paperclip_blueprints.serialisation import inspect_document

    return inspect_document(inspect_brief(source))


def test_the_inspect_document_declares_its_own_version() -> None:
    """I2.3 — independent of the embedded document's, so a new brief field bumps this one."""
    document = _inspect(_brief_text())
    assert document["schema"] == "blueprints.inspect/1"
    assert document["validation"]["schema"] == "blueprints.validate/1"


def test_the_validation_half_is_the_validate_document_verbatim() -> None:
    """I2.1, I2.2 — one definition of a failure, embedded rather than restated.

    Compared against the live builder rather than a fixture of what it used to emit, so a
    change to the validation document appears here automatically instead of silently
    diverging.
    """
    from paperclip_blueprints.api import validate_brief

    assert _inspect(_brief_text())["validation"] == validate_document(validate_brief(_brief_text()))


def test_sections_carry_ordinal_heading_and_span() -> None:
    document = _inspect(_brief_text())
    assert document["sections"], "no sections reported"
    for section in document["sections"]:
        assert set(section) == {"ordinal", "heading", "span"}
        assert set(section["span"]) == {"start", "end"}
        assert section["span"]["start"] <= section["span"]["end"]


def test_a_document_span_reproduces_the_body_from_the_source_bytes() -> None:
    """The guarantee, asserted through the wire shape a consumer actually receives —
    not only against the typed result it is derived from."""
    from paperclip_blueprints.models.brief_sections import scan_sections

    source = _brief_text()
    raw = source.encode("utf-8")
    bodies = {s.ordinal: s.body for s in scan_sections(source)}
    for section in _inspect(source)["sections"]:
        sliced = raw[section["span"]["start"] : section["span"]["end"]].decode("utf-8")
        assert sliced == bodies[section["ordinal"]]


def test_the_key_set_does_not_vary_with_outcome() -> None:
    """I3.5 — `sections` and `brief` are present on every document, `brief` null when there
    are no values, so a consumer never needs defensive access."""
    valid = _inspect(_brief_text())
    invalid = _inspect(_renumbered())
    assert set(valid) == set(invalid) == {"schema", "validation", "sections", "brief"}


def test_a_broken_brief_still_carries_its_sections_and_no_values() -> None:
    """I3.1, I3.2 — the case a consumer meets first."""
    document = _inspect(_renumbered())
    assert document["validation"]["valid"] is False
    assert document["sections"], "sections must survive a structural failure"
    assert document["brief"] is None


def test_sections_include_beyond_range_and_absorbing_sections() -> None:
    """I3.4 — filtering to the declared twelve would turn an observation into an
    interpretation."""
    source = _brief_text() + "\n## 13. My own notes\n\nanything\n"
    ordinals = [s["ordinal"] for s in _inspect(source)["sections"]]
    assert 13 in ordinals


def test_the_inspect_document_holds_no_absolute_path() -> None:
    """I5.2."""
    rendered = dumps(_inspect(_brief_text()))
    assert str(_REPO_ROOT) not in rendered
    assert "/Users/" not in rendered


# --- feature 021 US3: the value projection ------------------------------------

_DISTINCT = _REPO_ROOT / "tests" / "fixtures" / "brief_distinct_fields.md"


def _distinct_source() -> str:
    return _DISTINCT.read_bytes().decode("utf-8")


def test_the_projection_fixture_gives_every_field_a_distinguishable_value() -> None:
    """I4.4, FR-022 — the property that makes the fixture a guard rather than a sample.

    A transposition is invisible to both the exhaustiveness test and the round-trip check,
    because both walk the projection's own table. Only values that cannot be mistaken for
    one another expose a swap, so the fixture's distinguishability is asserted rather than
    assumed — a later edit making two fields resemble each other would silently retire the
    only guard that catches it.
    """
    from paperclip_blueprints.api import validate_brief

    brief = validate_brief(_distinct_source()).brief_object
    assert brief is not None
    values = brief.model_dump()
    assert all(v is not None for v in values.values()), "an unset field cannot be distinguished"
    rendered = [repr(v) for v in values.values()]
    assert len(set(rendered)) == len(rendered), "two fields share a value; a swap would hide"


# The expected document, written out independently of the projection table.
#
# Walking `BRIEF_PROJECTION` to build this would inherit its defects: a transposition swaps
# both sides of the comparison and the assertion still holds. Verified — transposing the
# `name` and `slug` entries left an earlier, table-walking version of this test green. The
# oracle has to be an independent statement of what the document should contain.
_EXPECTED_BRIEF = {
    "name": "Alpha Name Company",
    "slug": "bravo-slug-company",
    "description": "Charlie description of a company in a single short sentence.",
    "northStar": "Delta north star reaching 4200 units within 18 months.",
    "goals": [
        "Echo goal sustained above 11 percent",
        "Foxtrot goal held below 22 percent",
    ],
    "weAre": "Golf paragraph describing what this company is in plain operational terms.",
    "weAreNot": [
        "**We are NOT** hotel, the first thing this company is not.",
        "**We are NOT** india, the second thing this company is not.",
    ],
    "constraints": [
        "Juliett constraint that the company never violates.",
        "Kilo constraint that the company never violates.",
    ],
    "governancePosition": "tight",
    "useCasePattern": "solo-dev-shop",
    "useCaseNotes": "Lima notes about customising the chosen pattern.",
    "hoursPerWeek": 13,
    "capitalMonthlyEur": 24,
    "capitalSetupEur": 35,
    "routineTimezone": "Europe/Helsinki",
    "adapterPreferences": ["Mike adapter preference for one named role"],
    "runPolicyPreferences": ["papa-agent: max turns 7"],
    "freeText": "**Oscar canon rule.** November procedure that agents follow.",
}


def test_every_brief_field_reaches_the_document_under_its_own_key() -> None:
    """I4.1, I4.4, SC-006 — the guard that sees a transposition.

    Compared against a hand-written expectation rather than against the projection table,
    because a test that walks the table cannot distinguish a correct mapping from a swapped
    one: both sides move together.
    """
    document = _inspect(_distinct_source())["brief"]
    assert document is not None
    assert document == _EXPECTED_BRIEF


def test_the_projection_covers_every_field_on_the_model() -> None:
    """I4.3, FR-021, SC-005 — a new brief field fails the suite until it is deliberately
    projected or deliberately excluded.

    This converts "remember to update the wire" into "fails until you do".
    """
    from paperclip_blueprints.models.input import CompanyBrief
    from paperclip_blueprints.serialisation import BRIEF_PROJECTION

    projected = {field for field, _ in BRIEF_PROJECTION}
    assert projected == set(CompanyBrief.model_fields), (
        "the projection and the brief model disagree; project the new field or exclude it "
        f"deliberately: {projected ^ set(CompanyBrief.model_fields)}"
    )


def test_projected_keys_are_unique_and_camel_case() -> None:
    """I4.2 — matching the two shipped documents, and no key claimed twice."""
    import re

    from paperclip_blueprints.serialisation import BRIEF_PROJECTION

    keys = [key for _, key in BRIEF_PROJECTION]
    assert len(set(keys)) == len(keys)
    for key in keys:
        assert re.fullmatch(r"[a-z]+(?:[A-Z][a-z0-9]*)*", key), key


def test_values_are_absent_when_parsing_failed() -> None:
    """I3.2, FR-014 — values read from text that failed to parse are artifacts."""
    assert _inspect(_renumbered())["brief"] is None


# --- feature 021 US4: observations survive a failed interpretation -----------


def test_a_structurally_broken_brief_reports_every_section_and_no_values() -> None:
    """I3.1, I3.2, SC-003 — one response carries both facts."""
    document = _inspect(_renumbered())
    assert document["validation"]["valid"] is False
    assert document["brief"] is None
    assert len(document["sections"]) >= 12


def test_spans_of_a_broken_brief_still_reproduce() -> None:
    """The guarantee does not depend on the brief being interpretable.

    A span says *this region is the section headed X at ordinal N*; that stays true when N
    should not be X, which is why observations are not gated on interpretation succeeding.
    """
    source = _renumbered()
    raw = source.encode("utf-8")
    from paperclip_blueprints.models.brief_sections import scan_sections

    bodies = {(s.ordinal, s.heading): s.body for s in scan_sections(source)}
    for section in _inspect(source)["sections"]:
        sliced = raw[section["span"]["start"] : section["span"]["end"]].decode("utf-8")
        assert sliced == bodies[(section["ordinal"], section["heading"])]


def test_a_duplicated_ordinal_appears_once_per_occurrence() -> None:
    """I3.4 — the list reports what is in the file, not what should be."""
    source = _brief_text().replace(
        "## 9. Operator working pattern",
        "## 9. Operator working pattern\n\nfirst\n\n## 9. Operator working pattern",
        1,
    )
    ordinals = [s["ordinal"] for s in _inspect(source)["sections"]]
    assert ordinals.count(9) == 2


def test_a_section_that_absorbed_a_heading_still_appears(tmp_path) -> None:
    """I3.4 — filtering it out would turn an observation into an interpretation."""
    source = _brief_text().replace(
        "## 6. Constraints", "## 6. Constraints\n\n## Stray heading\n\nstray body\n", 1
    )
    document = _inspect(source)
    assert document["validation"]["valid"] is False
    assert 6 in [s["ordinal"] for s in document["sections"]]
    six = next(s for s in document["sections"] if s["ordinal"] == 6)
    raw = source.encode("utf-8")
    assert "## Stray heading" in raw[six["span"]["start"] : six["span"]["end"]].decode("utf-8")
