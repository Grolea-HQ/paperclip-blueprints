"""Reading a brief faithfully (feature 021).

Text-mode reading translates CRLF to LF by default, so on a CRLF brief the string parsed is
not the file. Byte offsets computed against it are shifted by one byte per preceding line,
and a consumer slicing the file it holds lands in the wrong region — silently, and only on
CRLF input. Reading without newline translation is what makes "offsets into the source"
true rather than conditional.

The change is additive, and these tests are what establish that rather than assume it: no
parsed value gains a carriage return, and a bundle generated from a CRLF brief is
byte-identical to one generated from the same brief with LF endings. Only section bodies
differ, which is precisely the text that must stay faithful.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from paperclip_blueprints.models.input import CompanyBrief, parse_brief

_REPO_ROOT = Path(__file__).resolve().parent.parent
_FIXTURE = Path(__file__).parent / "fixtures" / "brief_crlf_astral.md"


def _crlf_source() -> str:
    """The fixture as its bytes decode — never via text mode, which would translate them."""
    return _FIXTURE.read_bytes().decode("utf-8")


def _lf_source() -> str:
    return _crlf_source().replace("\r\n", "\n")


# --- T001: the fixture is the instrument, so its properties are asserted ----


def test_the_fixture_still_carries_crlf_endings() -> None:
    """Every brief in the repository is LF. Without this fixture the reproduction and
    fidelity tests establish only that the code works on LF, which is what the feature-020
    baselines already established.

    Asserted on disk rather than trusted: an editor, a formatter or a well-meaning
    normalisation pass could strip the property and disarm every test that depends on it
    while all of them keep passing.
    """
    raw = _FIXTURE.read_bytes()
    assert b"\r\n" in raw
    assert b"\n" not in raw.replace(b"\r\n", b""), "the fixture has bare LF endings mixed in"


def test_the_fixture_still_carries_an_astral_character() -> None:
    """The second axis. A character outside the Basic Multilingual Plane is where a
    code-point offset and a UTF-16 offset diverge, and where a byte offset differs from
    both. The repository's briefs contain none."""
    text = _crlf_source()
    astral = [c for c in text if ord(c) > 0xFFFF]
    assert astral, "the fixture no longer contains a character above U+FFFF"


def test_the_fixture_is_a_valid_brief() -> None:
    """A fixture that stopped parsing would make every test below vacuous."""
    assert parse_brief(_crlf_source()).slug == "research-digest"


# --- T002: reading preserves what is in the file ----------------------------


def test_text_mode_reading_would_translate_the_fixture() -> None:
    """The defect this feature's reader change exists to remove, pinned.

    This documents *why* the reader cannot use the default: it is not a hypothetical about
    some other file, it is what happens to this fixture today.
    """
    assert _FIXTURE.read_text(encoding="utf-8") != _crlf_source()
    assert "\r\n" not in _FIXTURE.read_text(encoding="utf-8")


def test_the_brief_reader_preserves_line_endings() -> None:
    """S5.1 — the string parsed is the file's bytes decoded, so offsets into it index the
    file."""
    from paperclip_blueprints.cli import read_brief_source

    assert read_brief_source(_FIXTURE) == _crlf_source()


def test_every_command_reads_a_brief_the_same_way() -> None:
    """FR-026 — reading faithfully for one command alone would let two commands parse
    different strings for one file and disagree about it.

    Asserted against the source: no brief-reading path may call the translating form.
    """
    import re

    cli_source = (_REPO_ROOT / "src" / "paperclip_blueprints" / "cli.py").read_text(
        encoding="utf-8"
    )
    # The bundle scan reads rendered bundle files, not briefs, and is out of scope.
    brief_reads = [
        line
        for line in cli_source.splitlines()
        if re.search(r"\b(input|input_path)\b.*read_text", line)
    ]
    assert brief_reads == [], f"a brief is still read in text mode: {brief_reads}"


# --- T004: the change is additive for values --------------------------------


def _values(brief: CompanyBrief) -> dict[str, object]:
    return brief.model_dump()


@pytest.mark.parametrize("field", sorted(CompanyBrief.model_fields))
def test_a_crlf_brief_parses_to_the_same_value_as_its_lf_twin(field: str) -> None:
    """S5.2 — per field, not on the whole model.

    Asserting the models are equal would report one failure naming nothing; asserting per
    field means a value path that starts carrying a carriage return names itself.
    """
    crlf = _values(parse_brief(_crlf_source()))
    lf = _values(parse_brief(_lf_source()))
    assert crlf[field] == lf[field]


def test_no_parsed_value_carries_a_carriage_return() -> None:
    """The positive form of the same property, stated directly.

    It holds structurally rather than by care: every value path splits lines — which
    discards terminators — and rejoins with a newline. That same split-and-rejoin is why a
    multi-line value is not a slice of a CRLF source, which is why values carry no spans.
    One mechanism, two consequences, opposite signs.
    """
    for name, value in _values(parse_brief(_crlf_source())).items():
        rendered = value if isinstance(value, str) else repr(value)
        assert "\r" not in rendered, f"{name} carries a carriage return"


def test_section_bodies_do_differ_between_the_two() -> None:
    """The counterpart, and the reason the change is not a no-op.

    Without this the additive-ness tests above would also pass if the reader change had
    silently done nothing at all.
    """
    from paperclip_blueprints.models.brief_sections import scan_sections

    crlf_bodies = [s.body for s in scan_sections(_crlf_source())]
    lf_bodies = [s.body for s in scan_sections(_lf_source())]
    assert crlf_bodies != lf_bodies
    assert any("\r" in body for body in crlf_bodies)


# --- T005: the change reaches no generated bundle ---------------------------


def test_a_bundle_generated_from_a_crlf_brief_is_byte_identical_to_its_lf_twin() -> None:
    """S5.3, FR-027 — the basis for calling the reader change additive.

    Values are unchanged (above), so nothing a generator interpolates should differ. This
    asserts the conclusion at the far end rather than inferring it: a bundle is where a
    stray carriage return would actually surface, as mixed line endings in a shipped file.

    **What this covers, and what it does not.** The generators are mocked, so the rendered
    files reflect canned output rather than the brief's values — a value that reaches only a
    generator *prompt*, such as the operating canon, would not show up here. Verified by
    mutation: making a value carry a carriage return leaves this assertion green. The
    prompt-input comparison below closes that gap and is itself mutation-verified; the
    per-field equality tests above are what actually detect a changed value.
    """
    import sys

    sys.path.insert(0, str(Path(__file__).parent))
    from paperclip_blueprints.generators.client import LLMClient
    from paperclip_blueprints.renderers.bundle import generate_bundle_full
    from paperclip_blueprints.renderers.render import render_files
    from test_cli import _dispatch_full

    def _render(source: str) -> dict[str, str]:
        config = generate_bundle_full(parse_brief(source), LLMClient(_invoke=_dispatch_full))
        return render_files(config)

    crlf_files = _render(_crlf_source())
    lf_files = _render(_lf_source())

    assert sorted(crlf_files) == sorted(lf_files), "the set of generated files differs"
    for path in sorted(lf_files):
        assert crlf_files[path] == lf_files[path], f"{path} differs between CRLF and LF input"


def test_no_generated_file_carries_a_carriage_return() -> None:
    """The same property stated so a failure names the file rather than a diff."""
    import sys

    sys.path.insert(0, str(Path(__file__).parent))
    from paperclip_blueprints.generators.client import LLMClient
    from paperclip_blueprints.renderers.bundle import generate_bundle_full
    from paperclip_blueprints.renderers.render import render_files
    from test_cli import _dispatch_full

    config = generate_bundle_full(parse_brief(_crlf_source()), LLMClient(_invoke=_dispatch_full))
    for path, content in render_files(config).items():
        assert "\r" not in content, f"{path} carries a carriage return"


def test_generator_inputs_are_identical_between_a_crlf_brief_and_its_lf_twin() -> None:
    """The half the rendered-file comparison cannot see.

    Values threaded into a generator's prompt never reach a rendered file under a mocked
    transport, so a carriage return arriving in the operating canon would pass every
    file-level check. Capturing what is handed to the transport covers that path directly.
    """
    import sys

    sys.path.insert(0, str(Path(__file__).parent))
    from paperclip_blueprints.generators.client import LLMClient
    from paperclip_blueprints.renderers.bundle import generate_bundle_full
    from test_cli import _dispatch_full

    def _calls(source: str) -> list[str]:
        seen: list[str] = []

        def _record(**kwargs: object) -> str:
            # Every keyword, not a chosen subset: naming one that the transport does not
            # take yields a comparison of identical `None`s that passes unconditionally.
            seen.append(repr(sorted((k, repr(v)) for k, v in kwargs.items())))
            return _dispatch_full(**kwargs)

        generate_bundle_full(parse_brief(source), LLMClient(_invoke=_record))
        assert seen, "no generator was invoked; the comparison below would be vacuous"
        return sorted(seen)

    assert _calls(_crlf_source()) == _calls(_lf_source())
