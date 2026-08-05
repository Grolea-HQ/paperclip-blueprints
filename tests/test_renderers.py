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


def test_write_bundle_force_does_not_union_prior_contents(tmp_path) -> None:
    # ADR-013 / FR-007: a forced regeneration cleanly replaces — it must not leave a
    # stray file from a prior generation (which downstream caused duplicate entities).
    out = tmp_path / "bundle"
    out.mkdir()
    (out / "STALE-from-prior-run.md").write_text("leftover", encoding="utf-8")
    dest = write_bundle(render_files(_config()), out, force=True)
    written = {str(p.relative_to(dest)) for p in dest.rglob("*") if p.is_file()}
    assert "STALE-from-prior-run.md" not in written
    assert len(written) == 9  # exactly the new single-agent bundle, no union


# --- full-mode structural check (T015) --------------------------------------

from paperclip_blueprints.models.output import CompanyConfig  # noqa: E402
from test_models import _full_config_kwargs  # noqa: E402


def _full_files() -> dict[str, str]:
    return render_files(CompanyConfig(**_full_config_kwargs()))


def test_full_bundle_passes_structural_check() -> None:
    structural_check(_full_files())  # must not raise


def test_full_single_agent_still_nine_files() -> None:
    files = render_files(_config())
    structural_check(files)
    assert len(files) == 9


def test_full_missing_top_level_rejected() -> None:
    files = _full_files()
    del files["README.md"]
    with pytest.raises(BundleError, match="missing top-level"):
        structural_check(files)


def test_full_wrong_schema_string_rejected() -> None:
    files = _full_files()
    files["COMPANY.md"] = files["COMPANY.md"].replace("agentcompanies/v1", "wrong/v9")
    with pytest.raises(BundleError, match="agentcompanies/v1"):
        structural_check(files)


def test_full_dangling_task_project_rejected() -> None:
    files = _full_files()
    key = next(k for k in files if k.startswith("tasks/"))
    files[key] = files[key].replace("project: launch-v1", "project: ghost-project")
    with pytest.raises(BundleError, match="unknown project"):
        structural_check(files)


def test_full_orphan_skill_rejected() -> None:
    files = _full_files()
    files["skills/orphan-skill/SKILL.md"] = (
        "---\nschema: agentcompanies/v1\nslug: orphan-skill\n"
        "name: orphan-skill\ndescription: x\n---\n"
    )
    with pytest.raises(BundleError, match="referenced by no agent"):
        structural_check(files)


def test_full_missing_idle_belief_rejected() -> None:
    files = _full_files()
    key = next(k for k in files if k.endswith("/SOUL.md"))
    files[key] = files[key].replace("Idle", "Busy").replace("idle", "busy")
    with pytest.raises(BundleError, match="idle-state"):
        structural_check(files)


# --- feature 016: no-op parity for a brief without section 11 (C-T5) ---------


def test_bundle_without_canon_renders_byte_identically_to_the_pre_change_baseline() -> None:
    """FR-004: a brief with no ``free_text`` must be completely unaffected.

    ``tests/fixtures/baseline_016.json`` was captured from the rendered file map BEFORE
    any of feature 016's source edits. Capturing it afterwards would have compared the
    new implementation against itself and passed vacuously — the same shape as the
    single-process determinism traps recorded in ADR-036.
    """
    import json
    import pathlib

    baseline_path = pathlib.Path(__file__).resolve().parent / "fixtures" / "baseline_016.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    config = _config()
    assert config.brief.free_text is None, "baseline fixture assumes a brief with no section 11"

    files = render_files(config)
    assert sorted(files) == sorted(baseline), "the set of rendered files changed"
    for path, content in sorted(baseline.items()):
        assert files[path] == content, f"{path} changed for a brief with no operating canon"


def test_canon_coverage_fires_through_the_render_warn_sink() -> None:
    """The dispatch itself must bite, not just the module in isolation.

    A correct check wired to nothing passes every unit test it has. This asserts the
    path from ``render_files`` through the ``warn`` sink actually carries the finding.
    """
    config = _config()
    canon = (
        "**The berth-scoring rubric.** Every observation is scored on two dimensions.\n"
        "(1) *Structural comparability* — how close the observation is to the target.\n"
        "(2) *Outcome verification* — whether the gain was measured or projected.\n"
    )
    config.brief.free_text = canon

    seen: list[str] = []
    render_files(config, warn=seen.append)

    canon_lines = [w for w in seen if "operating canon" in w]
    assert canon_lines, "the canon check emitted nothing for canon absent from the bundle"
    assert any("Structural comparability" in w for w in canon_lines)
    # the rubric block is named so a missing part can be placed in the brief
    assert any("The berth-scoring rubric" in w for w in canon_lines)


def test_canon_coverage_is_silent_when_the_brief_has_no_section_11() -> None:
    config = _config()
    assert config.brief.free_text is None
    seen: list[str] = []
    render_files(config, warn=seen.append)
    assert not [w for w in seen if "operating canon" in w]
