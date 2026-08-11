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
