"""Tests for the canon-coverage check (feature 016 / ADR-037).

The check answers ONE question: does each distinctive term from the brief's section-11
operating canon appear anywhere in the rendered bundle? It asserts *presence*, never
fidelity — whether a rubric survived as usable procedure is human judgement, and the
check must not appear to make it.

See ``specs/016-brief-canon-threading/contracts/canon-coverage.md``.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

from paperclip_blueprints.renderers.canon import (
    COMMON_WORDS,
    MAX_TERMS,
    MIN_TERM_CHARS,
    canon_coverage,
    canon_warnings,
    extract_canon_terms,
)

_FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "canon_section11.md"


def _canon() -> str:
    return _FIXTURE.read_text(encoding="utf-8")


# The structural items the rule exists to catch: five named scoring dimensions and three
# evidence-class labels. Sanitised vocabulary — the shapes are what carry the calibration.
_EXPECTED = {
    "Persuadability-Index",
    "Reach-Confidence",
    "Timing-Fit",
    "Margin-Headroom",
    "Switch-Cost",
    "Observed-Signal",
    "Inferred-Signal",
    "Reported-Signal",
}


# --- extraction: calibrated against the failing case's shape (C-C10) ---------


def test_extraction_recovers_the_dimension_names_and_class_labels() -> None:
    """C-C10 positive side: the structural items must survive extraction."""
    found = {t.text for t in extract_canon_terms(_canon())}
    assert _EXPECTED <= found, f"missed: {sorted(_EXPECTED - found)}"


def test_extraction_rejects_ordinary_prose_from_the_same_source() -> None:
    """C-C10 negative side — the half that makes this a calibration, not a keyword list.

    The negatives are drawn from the SAME fixture as the positives, so the rule is
    discriminating within one document rather than between two hand-picked ones.
    """
    found = {t.text for t in extract_canon_terms(_canon())}
    assert found == _EXPECTED, f"unexpected extras: {sorted(found - _EXPECTED)}"


def test_no_term_is_made_only_of_common_words() -> None:
    for term in extract_canon_terms(_canon()):
        words = [w for w in term.normalised.split() if w]
        assert not all(w in COMMON_WORDS for w in words), f"{term.text!r} is ordinary English"


def test_extraction_is_capped_and_respects_the_minimum_length() -> None:
    terms = extract_canon_terms(_canon())
    assert len(terms) <= MAX_TERMS
    for term in terms:
        assert len(term.text) >= MIN_TERM_CHARS


def test_thresholds_are_named_constants_and_overridable() -> None:
    """C-C10a: operator calibration must be a config change, not a code change."""
    assert isinstance(MIN_TERM_CHARS, int)
    assert isinstance(MAX_TERMS, int)
    assert isinstance(COMMON_WORDS, frozenset)
    few = extract_canon_terms(_canon(), max_terms=3)
    assert len(few) == 3


def test_extraction_is_empty_for_absent_or_blank_canon() -> None:
    assert extract_canon_terms("") == []
    assert extract_canon_terms("   \n  ") == []


# --- canon-unique scoping (C-C11) -------------------------------------------


def test_a_phrase_carried_by_another_brief_field_is_not_a_canon_term() -> None:
    """C-C11: the main precision lever.

    A phrase that also appears elsewhere in the brief reaches the generators by an
    existing path, so its coverage says nothing about THIS defect. Reporting it would be
    pure noise.
    """
    found = {t.text for t in extract_canon_terms(_canon(), exclude_texts=["We track Timing-Fit."])}
    assert "Timing-Fit" not in found
    assert "Switch-Cost" in found, "excluding one phrase must not drop the others"


# --- matching (FR-015) ------------------------------------------------------


def test_matching_tolerates_case_and_hyphen_variation() -> None:
    terms = [t for t in extract_canon_terms(_canon()) if t.text == "Timing-Fit"]
    cov = canon_coverage(terms, {"a.md": "we score timing fit for every enquiry"})
    assert cov[0].carriers == ["a.md"]


def test_matching_does_not_count_an_accidental_substring() -> None:
    terms = [t for t in extract_canon_terms(_canon()) if t.text == "Switch-Cost"]
    cov = canon_coverage(terms, {"a.md": "the switch-costing model is unrelated"})
    assert cov[0].carriers == []


# --- coverage + warnings (C-C2 .. C-C7) -------------------------------------


def _terms_for(*texts: str) -> list:
    return [t for t in extract_canon_terms(_canon()) if t.text in texts]


def test_missing_canon_is_reported_by_name() -> None:
    """C-C2 + C-C3: THE POSITIVE-DETECTION TEST.

    Per ADR-036, a check whose tests assert only silence cannot be distinguished from a
    dead one. This asserts the check FIRES, and that the warning names the specific term
    rather than delivering an aggregate verdict the operator would learn to skip.
    """
    terms = _terms_for("Margin-Headroom")
    warnings = canon_warnings(canon_coverage(terms, {"a.md": "nothing relevant here"}))
    assert warnings, "the coverage check did not fire on absent canon"
    assert any("Margin-Headroom" in w for w in warnings)
    assert not any("coverage incomplete" in w.lower() for w in warnings)


def test_fully_covered_canon_is_silent() -> None:
    """C-C4: quiet on a clean bundle, so the signal stays worth reading."""
    terms = _terms_for("Margin-Headroom")
    files = {"a.md": "we compute Margin-Headroom", "b.md": "Margin-Headroom again"}
    assert canon_warnings(canon_coverage(terms, files)) == []


def test_a_single_carrier_is_reported_as_thin_and_names_the_file() -> None:
    """C-C5: the weak-result signal, with the location the operator needs to judge it."""
    terms = _terms_for("Margin-Headroom")
    warnings = canon_warnings(canon_coverage(terms, {"OPERATIONS.md": "Margin-Headroom"}))
    assert len(warnings) == 1
    assert "Margin-Headroom" in warnings[0]
    assert "OPERATIONS.md" in warnings[0]


def test_every_rendered_file_is_scanned_without_privileging_any_artifact() -> None:
    """C-C6: no artifact kind is excluded or weighted.

    A term carried only by an artifact that does not survive import still counts as
    covered — narrowing the scan would bake current platform behaviour into the check.
    The thin warning is what surfaces it instead.
    """
    terms = _terms_for("Switch-Cost")
    cov = canon_coverage(terms, {"OPERATIONS.md": "Switch-Cost matters"})
    assert cov[0].carriers == ["OPERATIONS.md"]


def test_carriers_are_sorted_and_complete() -> None:
    terms = _terms_for("Switch-Cost")
    files = {"z.md": "Switch-Cost", "a.md": "Switch-Cost", "m.md": "irrelevant"}
    assert canon_coverage(terms, files)[0].carriers == ["a.md", "z.md"]


def test_warnings_make_no_claim_about_quality() -> None:
    """C-C7 / FR-012: presence, never fidelity."""
    banned = ("correct", "proper", "faithful", "accurate", "good", "well", "quality")
    terms = _terms_for("Margin-Headroom", "Switch-Cost")
    warnings = canon_warnings(canon_coverage(terms, {"a.md": "Switch-Cost"}))
    assert warnings
    for w in warnings:
        lowered = w.lower()
        for word in banned:
            assert word not in lowered, f"warning implies a quality judgement: {w!r}"


# --- determinism (C-C9) -----------------------------------------------------


def test_output_is_identical_across_differing_hash_seeds() -> None:
    """C-C9: the variant-2 hazard from ADR-036's consolidated hazard-class section.

    Set iteration order for strings is PYTHONHASHSEED-dependent, so a check that derived
    output by iterating a set would agree with itself all suite long and still be
    non-reproducible in the field. A single-process assertion cannot see that — the
    subprocess IS the test, following tests/test_routines.py's precedent.
    """
    script = (
        "import json,pathlib;"
        "from paperclip_blueprints.renderers.canon import extract_canon_terms,"
        "canon_coverage,canon_warnings;"
        f"c=pathlib.Path({str(_FIXTURE)!r}).read_text(encoding='utf-8');"
        "t=extract_canon_terms(c);"
        "f={'b.md':'Switch-Cost','a.md':'Switch-Cost and Timing-Fit'};"
        "print(json.dumps([x.text for x in t]+canon_warnings(canon_coverage(t,f))))"
    )
    outs = []
    for seed in ("0", "1", "42", "12345"):
        proc = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            check=True,
            env={"PYTHONHASHSEED": seed, "PATH": "/usr/bin:/bin"},
        )
        outs.append(proc.stdout.strip())
    assert len(set(outs)) == 1, f"output varied with PYTHONHASHSEED: {outs}"


# --- structural guarantees (C-C1, C-C8) -------------------------------------

_SRC = pathlib.Path(__file__).resolve().parent.parent / "src" / "paperclip_blueprints"


def test_the_check_never_enters_the_raising_validation_gate() -> None:
    """C-C1: advisory only. validate_bundle raises; this must never be part of it."""
    for path in (_SRC / "validators").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "canon" not in text.lower(), f"{path.name} references the canon check"


def test_the_check_carries_no_exemption_list() -> None:
    """C-C8: term-oriented, not artifact-oriented.

    A referenced platform-provided capability contributes no file to the rendered map and
    is therefore outside the scan STRUCTURALLY — not by an exception entry that would
    have to be maintained. That is the difference between a rule and a rule plus
    exceptions (ADR-019's standing constraint).
    """
    text = (_SRC / "renderers" / "canon.py").read_text(encoding="utf-8")
    assert "BUILTIN" not in text, "the check must not reason over the built-in capability set"
    assert "builtins" not in text.lower().replace("__builtins__", "")


def test_no_builtin_hash_is_used() -> None:
    """ADR-036 variant 1: builtin ``hash()`` is per-process salted.

    Checked against the parsed AST, not the source text — a docstring that *names* the
    hazard is documentation, not a call site, and must not trip the assertion.
    """
    import ast

    tree = ast.parse((_SRC / "renderers" / "canon.py").read_text(encoding="utf-8"))
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "hash" not in called
