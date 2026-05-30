"""Tests for renderers — frontmatter round-trip (T007) and bundle orchestration (T021)."""

import pytest

from paperclip_blueprints.renderers.bundle import (
    BundleError,
    structural_check,
    write_bundle,
)
from paperclip_blueprints.renderers.frontmatter import dump_frontmatter
from paperclip_blueprints.renderers.render import render_files
from test_templates import _config


def test_frontmatter_is_fenced() -> None:
    out = dump_frontmatter({"schema": "agentcompanies/v1", "slug": "ceo"})
    assert out.startswith("---\n")
    assert out.rstrip().endswith("---")


def test_special_char_scalar_is_single_quoted() -> None:
    out = dump_frontmatter({"schema": "agentcompanies/v1", "slug": "ceo", "name": "CEO / Editor"})
    assert "name: 'CEO / Editor'" in out
    # plain slug stays bare
    assert "slug: ceo\n" in out


def test_inline_sequence_for_flow_keys() -> None:
    out = dump_frontmatter(
        {"slug": "ceo", "skills": ["voice-capture", "editorial-calendar"]},
        flow_seq_keys={"skills"},
    )
    assert "skills: [voice-capture, editorial-calendar]" in out


def test_none_renders_as_null() -> None:
    out = dump_frontmatter({"slug": "ceo", "reportsTo": None})
    assert "reportsTo: null" in out


def test_empty_list_inline() -> None:
    out = dump_frontmatter({"tags": []}, flow_seq_keys={"tags"})
    assert "tags: []" in out


def test_block_list_items_quoted_when_needed() -> None:
    out = dump_frontmatter(
        {"goals": ["10,000 subscribers within 90 days", "conversion above 2.5%"]}
    )
    assert "goals:" in out
    assert "- '10,000 subscribers within 90 days'" in out


def test_key_order_preserved() -> None:
    out = dump_frontmatter({"schema": "agentcompanies/v1", "name": "X Co", "version": "1.0.0"})
    assert out.index("schema:") < out.index("name:") < out.index("version:")


def test_nested_mapping() -> None:
    out = dump_frontmatter({"metadata": {"paperclip": {"tone": "green", "mono": "N"}}})
    assert "metadata:" in out
    assert "paperclip:" in out
    assert "tone: green" in out


# --- bundle structural check + atomic write (T021) --------------------------


def test_structural_check_passes_valid_bundle() -> None:
    structural_check(render_files(_config()))  # should not raise


def test_structural_check_rejects_missing_file() -> None:
    files = render_files(_config())
    del files["COMPANY.md"]
    with pytest.raises(BundleError):
        structural_check(files)


def test_structural_check_rejects_wrong_schema() -> None:
    files = render_files(_config())
    files[".paperclip.yaml"] = files[".paperclip.yaml"].replace("paperclip/v1", "bogus/v9")
    with pytest.raises(BundleError):
        structural_check(files)


def test_structural_check_rejects_too_few_negations() -> None:
    files = render_files(_config())
    # collapse the "We are not." block to a single bullet
    files["COMPANY.md"] = (
        "---\nschema: agentcompanies/v1\n---\n\n# X\n\n## Identity\n\n"
        "**We are not.**\n\n- only one negation\n\n**North star.** x\n"
    )
    with pytest.raises(BundleError):
        structural_check(files)


def test_structural_check_rejects_missing_idle_belief() -> None:
    files = render_files(_config())
    soul_path = "agents/ceo/SOUL.md"
    files[soul_path] = files[soul_path].replace("Idle", "Busy").replace("idle", "busy")
    with pytest.raises(BundleError):
        structural_check(files)


def test_structural_check_rejects_skill_cross_ref_mismatch() -> None:
    files = render_files(_config())
    agents_path = "agents/ceo/AGENTS.md"
    files[agents_path] = files[agents_path].replace("release-checklist", "some-other-skill")
    with pytest.raises(BundleError):
        structural_check(files)


def test_write_bundle_writes_nine_files(tmp_path) -> None:
    out = tmp_path / "bundle"
    dest = write_bundle(render_files(_config()), out)
    assert dest == out  # bundle root is the output dir itself, no slug subdir
    written = {str(p.relative_to(dest)) for p in dest.rglob("*") if p.is_file()}
    assert len(written) == 9
    assert (dest / "COMPANY.md").exists()


def test_write_bundle_refuses_nonempty_without_force(tmp_path) -> None:
    files = render_files(_config())
    out = tmp_path / "bundle"
    write_bundle(files, out)
    with pytest.raises(BundleError):
        write_bundle(files, out)
    # with force it succeeds
    dest = write_bundle(files, out, force=True)
    assert dest.exists()
