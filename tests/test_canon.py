"""Tests for the canon-coverage check (feature 016 / ADR-037).

The check answers ONE question: does each distinctive term from the brief's section-11
operating canon appear anywhere in the rendered bundle? It asserts *presence*, never
fidelity — whether a rubric survived as usable procedure is human judgement, and the
check must not appear to make it.

**On the fixture.** ``tests/fixtures/canon_section11.md`` is derived from a structural
skeleton of a real section 11 supplied by the operator — not authored here. That
provenance is the point. The previous fixture was written from the implementer's guess at
the shape (hyphenated Title-Case compounds); it matched the rule perfectly, nineteen tests
passed, and the real run found nothing at all, because the fixture and the rule were two
expressions of a single wrong assumption. A calibration fixture has to come from an
artifact the implementer did not author, or green means only that you were consistent with
yourself. See ADR-036.

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
    extraction_warnings,
)

_FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "canon_section11.md"


def _canon() -> str:
    return _FIXTURE.read_text(encoding="utf-8")


def _texts() -> set[str]:
    return {t.text for t in extract_canon_terms(_canon())}


# Bold-headed blocks name canon items. Every one is a term; the heading is reduced to the
# item's name, dropping gloss after a dash or comma.
_BLOCK_HEADS = {
    "The engagement",
    "Coverage domains",
    "A definitional question the client's brief leaves open",
    "Source discipline",
    "The Tier C honesty note",
    "The berth-scoring rubric",
    "Evidence tiers and the active-list entry rule",
    "The commissioning-date rule",
    "The provenance citation format",
    "The daily recap does two jobs",
    "Tier discipline as structure",
    "Backtest scope",
}

# Enumerated italic inside a block names a part of that item. Sentence case, not Title Case.
_ENUMERATED = {
    "Freshness against class decay",
    "Structural comparability",
    "Scale transferability",
    "Evidential independence",
    "Outcome verification",
}

_EXPECTED = _BLOCK_HEADS | _ENUMERATED


# --- extraction: must catch (C-C10 positive) --------------------------------


def test_extraction_recovers_every_bold_headed_block() -> None:
    assert _BLOCK_HEADS <= _texts(), f"missed block headings: {sorted(_BLOCK_HEADS - _texts())}"


def test_extraction_recovers_enumerated_italic_rubric_parts() -> None:
    assert _ENUMERATED <= _texts(), f"missed rubric parts: {sorted(_ENUMERATED - _texts())}"


def test_extraction_records_which_block_a_rubric_part_belongs_to() -> None:
    """Block context is what makes a missing part placeable in the operator's brief."""
    by_text = {t.text: t for t in extract_canon_terms(_canon())}
    assert by_text["Structural comparability"].block == "The berth-scoring rubric"
    assert by_text["The berth-scoring rubric"].block is None


def test_canon_terms_are_sentence_case_not_title_case() -> None:
    """A Title-Case heuristic finds none of these — which is why the first rule found none."""
    for text in _ENUMERATED:
        rest = text.split()[1:]
        assert all(w[:1].islower() or not w[:1].isalpha() for w in rest), (
            f"{text!r} is Title Case; the fixture must mirror the real sentence-case shape"
        )


# --- extraction: must NOT catch (C-C10 negative) ----------------------------


def test_extraction_is_exactly_the_expected_set() -> None:
    """The half that makes this a calibration rather than a keyword list.

    Positives and negatives are drawn from the SAME fixture, so the rule has to
    discriminate within one document rather than between two hand-picked ones.
    """
    assert _texts() == _EXPECTED, f"unexpected extras: {sorted(_texts() - _EXPECTED)}"


def test_italic_proper_nouns_are_not_canon() -> None:
    """Italic alone is not the signal — the enumeration marker is."""
    for noise in ("Port Authority Register", "Coastal Statistics Office", "National Freight Board"):
        assert noise not in _texts()


def test_bare_italic_emphasis_on_an_ordinary_word_is_not_canon() -> None:
    assert "scored" not in _texts()


def test_quoted_example_output_is_not_canon() -> None:
    """A quoted illustration of agent output is an example, not a procedure."""
    for term in _texts():
        assert "two channel signals" not in term
        assert "observed handling cost" not in term


def test_a_curly_apostrophe_does_not_split_a_term() -> None:
    """The shape-based rule produced orphaned ``s brief leaves open`` fragments here."""
    assert "’" in _canon(), "fixture must carry a real curly apostrophe"
    assert not any(t.text.startswith("s ") for t in extract_canon_terms(_canon()))
    assert "A definitional question the client's brief leaves open" in _texts()


def test_no_markdown_markers_leak_into_a_term() -> None:
    for term in extract_canon_terms(_canon()):
        assert "*" not in term.text and "_" not in term.text and "`" not in term.text


def test_no_term_is_made_only_of_common_words() -> None:
    for term in extract_canon_terms(_canon()):
        words = [w for w in term.normalised.split() if w]
        assert not all(w in COMMON_WORDS for w in words), f"{term.text!r} is ordinary English"


# --- thresholds and empties -------------------------------------------------


def test_thresholds_are_named_constants_and_overridable() -> None:
    """C-C10a: operator calibration must be a config change, not a code change."""
    assert isinstance(MIN_TERM_CHARS, int)
    assert isinstance(MAX_TERMS, int)
    assert isinstance(COMMON_WORDS, frozenset)
    assert len(extract_canon_terms(_canon(), max_terms=3)) == 3


def test_extraction_is_empty_for_absent_or_blank_canon() -> None:
    assert extract_canon_terms("") == []
    assert extract_canon_terms("   \n  ") == []


# --- extraction-level warnings (the zero-result guard) ----------------------


def test_unmarked_prose_canon_warns_rather_than_reporting_nothing() -> None:
    """Once extraction keys on emphasis, that convention is load-bearing.

    A brief stating canon as unmarked prose yields no terms; a silent zero-term run would
    read as "all clear" — this feature's own defect wearing a new hat.
    """
    prose = "We score every enquiry carefully and we prefer conservative readings.\n"
    terms = extract_canon_terms(prose)
    assert terms == []
    warnings = extraction_warnings(prose, terms)
    assert warnings and "no canon items were found" in warnings[0]
    assert "markdown emphasis" in warnings[0]


def test_a_marked_up_canon_produces_no_zero_term_or_cap_warning() -> None:
    warnings = extraction_warnings(_canon(), extract_canon_terms(_canon()))
    assert not any("no canon items were found" in w for w in warnings)
    assert not any("hit its cap" in w for w in warnings)


# --- probeable vs sentence-shaped headings ----------------------------------


def test_sentence_shaped_headings_are_not_probed() -> None:
    """A heading carrying a finite verb cannot be searched for.

    ``The daily recap does two jobs`` names a real canon item, but a generated task says
    "Daily Operations Recap" — never the sentence. Probing for it manufactures a "missing"
    warning that no amount of correct generation could ever clear.
    """
    by_text = {t.text: t for t in extract_canon_terms(_canon())}
    assert by_text["The daily recap does two jobs"].probeable is False
    assert by_text["A definitional question the client's brief leaves open"].probeable is False


def test_name_shaped_headings_stay_probeable() -> None:
    by_text = {t.text: t for t in extract_canon_terms(_canon())}
    for name in (
        "The provenance citation format",
        "The commissioning-date rule",
        "Source discipline",
        "Evidence tiers and the active-list entry rule",
    ):
        assert by_text[name].probeable is True, f"{name!r} should be probeable"


def test_enumerated_parts_are_always_probeable() -> None:
    """Only a heading can be sentence-shaped; a named part is a name by construction."""
    for term in extract_canon_terms(_canon()):
        if term.block is not None:
            assert term.probeable is True


def test_an_unprobeable_heading_is_declared_not_reported_missing() -> None:
    """Excluding it silently would be the silent gap this module exists to close."""
    terms = [t for t in extract_canon_terms(_canon()) if not t.probeable]
    assert terms
    # No missing/thin line, even though it is carried by nothing.
    assert canon_warnings(canon_coverage(terms, {"a.md": "unrelated"})) == []
    # But it IS named, so its coverage being unknown is visible.
    declared = extraction_warnings(_canon(), extract_canon_terms(_canon()))
    assert any("cannot be searched for" in w for w in declared)
    assert any("The daily recap does two jobs" in w for w in declared)


def test_hitting_the_term_cap_is_reported_rather_than_truncating_silently() -> None:
    """Dropping terms to fit a display limit is the same silent loss the check reports."""
    terms = extract_canon_terms(_canon(), max_terms=3)
    warnings = extraction_warnings(_canon(), terms, max_terms=3)
    assert any("hit its cap" in w for w in warnings)


def test_no_extraction_warning_for_an_empty_section_11() -> None:
    assert extraction_warnings("", []) == []
    assert extraction_warnings(None, []) == []


# --- canon-unique scoping (C-C11) -------------------------------------------


def test_a_phrase_carried_by_another_brief_field_is_not_a_canon_term() -> None:
    """C-C11: the main precision lever.

    A phrase that also appears elsewhere in the brief reaches the generators by an
    existing path, so its coverage says nothing about THIS defect and would be noise.
    """
    found = {
        t.text
        for t in extract_canon_terms(_canon(), exclude_texts=["We track Structural comparability."])
    }
    assert "Structural comparability" not in found
    assert "Outcome verification" in found, "excluding one phrase must not drop the others"


# --- matching (FR-015) ------------------------------------------------------


def _terms_for(*texts: str) -> list:
    return [t for t in extract_canon_terms(_canon()) if t.text in texts]


def test_matching_tolerates_case_and_hyphen_variation() -> None:
    cov = canon_coverage(
        _terms_for("The commissioning-date rule"),
        {"a.md": "we apply the COMMISSIONING DATE rule to every entry"},
    )
    assert cov[0].carriers == ["a.md"]


def test_matching_does_not_count_an_accidental_substring() -> None:
    cov = canon_coverage(
        _terms_for("Outcome verification"), {"a.md": "outcome verifications are unrelated"}
    )
    assert cov[0].carriers == []


# --- coverage + warnings (C-C2 .. C-C7) -------------------------------------


def test_missing_canon_is_reported_by_name() -> None:
    """C-C2 + C-C3: THE POSITIVE-DETECTION TEST.

    Per ADR-036, a check whose tests assert only silence cannot be distinguished from a
    dead one. This asserts the check FIRES, and that the warning names the specific term
    rather than delivering an aggregate verdict the operator would learn to skip.
    """
    warnings = canon_warnings(
        canon_coverage(_terms_for("Outcome verification"), {"a.md": "nothing relevant"})
    )
    assert warnings, "the coverage check did not fire on absent canon"
    assert any("Outcome verification" in w for w in warnings)
    assert not any("coverage incomplete" in w.lower() for w in warnings)


def test_a_missing_rubric_part_names_its_block() -> None:
    warnings = canon_warnings(
        canon_coverage(_terms_for("Structural comparability"), {"a.md": "nothing"})
    )
    assert "The berth-scoring rubric" in warnings[0]


def test_fully_covered_canon_is_silent() -> None:
    """C-C4: quiet on a clean bundle, so the signal stays worth reading."""
    files = {"a.md": "Outcome verification here", "b.md": "Outcome verification again"}
    assert canon_warnings(canon_coverage(_terms_for("Outcome verification"), files)) == []


def test_a_single_carrier_is_reported_as_thin_and_names_the_file() -> None:
    """C-C5: the weak-result signal, with the location the operator needs to judge it."""
    warnings = canon_warnings(
        canon_coverage(_terms_for("Backtest scope"), {"OPERATIONS.md": "Backtest scope"})
    )
    assert len(warnings) == 1
    assert "Backtest scope" in warnings[0] and "OPERATIONS.md" in warnings[0]


def test_every_rendered_file_is_scanned_without_privileging_any_artifact() -> None:
    """C-C6: a term carried only by an import-dropped artifact still counts as covered.

    Narrowing the scan would bake current platform behaviour into the check; the thin
    warning is what surfaces the case instead.
    """
    cov = canon_coverage(_terms_for("Backtest scope"), {"OPERATIONS.md": "Backtest scope"})
    assert cov[0].carriers == ["OPERATIONS.md"]


def test_carriers_are_sorted_and_complete() -> None:
    files = {"z.md": "Backtest scope", "a.md": "Backtest scope", "m.md": "irrelevant"}
    assert canon_coverage(_terms_for("Backtest scope"), files)[0].carriers == ["a.md", "z.md"]


def test_warnings_make_no_claim_about_quality() -> None:
    """C-C7 / FR-012: presence, never fidelity."""
    banned = ("correct", "proper", "faithful", "accurate", "good", "well", "quality")
    warnings = canon_warnings(
        canon_coverage(
            _terms_for("Outcome verification", "Backtest scope"), {"a.md": "Backtest scope"}
        )
    )
    assert warnings
    for w in warnings:
        for word in banned:
            assert word not in w.lower(), f"warning implies a quality judgement: {w!r}"


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
        "f={'b.md':'Backtest scope','a.md':'Backtest scope and Outcome verification'};"
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
        assert "canon" not in path.read_text(encoding="utf-8").lower()


def test_the_check_carries_no_exemption_list() -> None:
    """C-C8: term-oriented, not artifact-oriented.

    A referenced platform-provided capability contributes no file to the rendered map and
    is therefore outside the scan STRUCTURALLY — not by an exception entry that would have
    to be maintained (ADR-019's standing constraint).
    """
    text = (_SRC / "renderers" / "canon.py").read_text(encoding="utf-8")
    assert "BUILTIN" not in text
    assert "builtins" not in text.lower().replace("__builtins__", "")


def test_no_builtin_hash_is_used() -> None:
    """ADR-036 variant 1: builtin ``hash()`` is per-process salted.

    Checked against the parsed AST, not the source text — a docstring that *names* the
    hazard is documentation, not a call site.
    """
    import ast

    tree = ast.parse((_SRC / "renderers" / "canon.py").read_text(encoding="utf-8"))
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "hash" not in called
