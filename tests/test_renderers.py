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

from paperclip_blueprints.models.cadence import Cadence  # noqa: E402
from paperclip_blueprints.models.output import CompanyConfig  # noqa: E402
from paperclip_blueprints.models.task import TaskDefinition  # noqa: E402
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


# One definition of what the pre-022 parity anchors below no longer cover. Feature 022
# (ADR-042) changed README.md deliberately — it dropped the goals advertisement and added the
# file classification and the compatibility pointer. The three baselines below anchor claims
# about canon threading, timezone emission and structured cadence, none of which touch the
# README, so excluding that one file costs those claims nothing. The README is not left
# unanchored: baseline_022 covers it, including an assertion that it did change.
_CHANGED_BY_LATER_FEATURES = {"README.md"}


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
        if path in _CHANGED_BY_LATER_FEATURES:
            continue
        assert files[path] == content, f"{path} changed for a brief with no operating canon"


# --- feature 017: no-op parity for a brief without a stated timezone (C4.1) --


def test_routine_bearing_bundle_without_timezone_matches_the_pre_change_baseline() -> None:
    """FR-004 / SC-003: every brief written before feature 017 renders byte-identically.

    ``tests/fixtures/baseline_017.json`` was captured by rendering a **routine-bearing**
    bundle from a git worktree at the pre-feature commit — not from the current tree.
    Re-capturing it from the edited source would have compared the implementation against
    itself and passed vacuously, which is ADR-036's third class exactly.

    The feature-016 baseline above cannot serve this purpose: its config is the
    single-agent one, which has no tasks and therefore no routines, so it never exercises
    the emitted timezone at all.
    """
    import json
    import pathlib

    baseline_path = pathlib.Path(__file__).resolve().parent / "fixtures" / "baseline_017.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    tasks = [
        TaskDefinition(
            slug="signal-scan",
            name="Signal scan",
            project="launch-v1",
            assignee="cto",
            objective="o",
            completion_criteria=["done"],
            recurrence=Cadence.coerce("mon,wed,fri"),
        ),
        TaskDefinition(
            slug="board-package",
            name="Monthly board package",
            project="launch-v1",
            assignee="cto",
            objective="o",
            completion_criteria=["done"],
            recurrence=Cadence.coerce("monthly"),
        ),
        TaskDefinition(
            slug="ship",
            name="Ship",
            project="launch-v1",
            assignee="cto",
            objective="o",
            completion_criteria=["done"],
        ),
    ]
    config = CompanyConfig(**_full_config_kwargs(tasks=tasks))
    assert config.brief.routine_timezone is None, "baseline assumes a brief with no stated zone"

    files = render_files(config)
    assert sorted(files) == sorted(baseline), "the set of rendered files changed"
    for path, content in sorted(baseline.items()):
        if path in _CHANGED_BY_LATER_FEATURES:
            continue
        assert files[path] == content, f"{path} changed for a brief with no stated timezone"


# --- feature 018: no-op parity for cadences stating no day (C5.2 / C5.3) -----


def test_legacy_string_cadences_render_identically_to_the_pre_018_baseline() -> None:
    """FR-018 / SC-005: a plan whose cadences state no day renders byte-identically.

    ``tests/fixtures/baseline_018.json`` was captured from the tree before any feature-018
    source edit, with tasks carrying legacy string cadences and no dependencies. It is the
    anchor for the claim that structured cadence changes nothing for plans that state no day.
    """
    import json
    import pathlib

    baseline_path = pathlib.Path(__file__).resolve().parent / "fixtures" / "baseline_018.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    def task(slug: str, name: str, rec: str | None = None) -> TaskDefinition:
        return TaskDefinition(
            slug=slug,
            name=name,
            project="launch-v1",
            assignee="cto",
            objective="o",
            completion_criteria=["done"],
            recurrence=Cadence.coerce(rec) if rec else None,
        )

    config = CompanyConfig(
        **_full_config_kwargs(
            tasks=[
                task("signal-scan", "Signal scan", "mon,wed,fri"),
                task("board-package", "Monthly board package", "monthly"),
                task("audit-review", "Quarterly audit review", "quarterly"),
                task("ship", "Ship"),
            ]
        )
    )
    files = render_files(config)
    assert sorted(files) == sorted(baseline), "the set of rendered files changed"
    for path, content in sorted(baseline.items()):
        if path in _CHANGED_BY_LATER_FEATURES:
            continue
        assert files[path] == content, f"{path} changed for a plan stating no cadence day"


def test_canon_coverage_fires_through_the_render_warn_sink() -> None:
    """The dispatch itself must bite, not just the module in isolation.

    A correct check wired to nothing passes every unit test it has. This asserts the
    path from ``render_files`` through the ``warn`` sink actually carries the finding.
    """
    config = _config()
    canon = (
        "**The maintenance-priority rubric.** Every observation is scored on two dimensions.\n"
        "(1) *Access difficulty* — how close the observation is to the target.\n"
        "(2) *Certification window* — whether the gain was measured or projected.\n"
    )
    config.brief.free_text = canon

    seen: list[str] = []
    render_files(config, warn=seen.append)

    canon_lines = [w for w in seen if "operating canon" in w]
    assert canon_lines, "the canon check emitted nothing for canon absent from the bundle"
    assert any("Access difficulty" in w for w in canon_lines)
    # the rubric block is named so a missing part can be placed in the brief
    assert any("The maintenance-priority rubric" in w for w in canon_lines)


def test_canon_coverage_is_silent_when_the_brief_has_no_section_11() -> None:
    config = _config()
    assert config.brief.free_text is None
    seen: list[str] = []
    render_files(config, warn=seen.append)
    assert not [w for w in seen if "operating canon" in w]


# --- provenance stamp on the generated README -------------------------------


def test_generated_readme_carries_a_version_stamped_provenance_footer() -> None:
    """Diagnostic first, attribution second.

    A bundle in the wild with no version is one you cannot reason about: every defect
    chased during this batch would have been faster to place with the generating version
    stamped in the artifact.
    """
    from paperclip_blueprints import __version__

    readme = render_files(_config())["README.md"]
    last = [line for line in readme.strip().splitlines() if line.strip()][-1]
    assert "Paperclip Blueprints" in last, "the stamp must be the footer, not a header"
    assert __version__ in last, "the stamp must carry the resolved package version"
    assert "github.com/Grolea-HQ/paperclip-blueprints" in last


def test_the_provenance_stamp_appears_in_no_other_bundle_file() -> None:
    """One discreet line, in one file. Never inside the operator's identity content."""
    files = render_files(_config())
    stamped = sorted(p for p, content in files.items() if "Paperclip Blueprints" in content)
    assert stamped == ["README.md"]


def test_company_md_is_byte_identical_after_the_provenance_change() -> None:
    """COMPANY.md is the operator's identity content and must not be annotated at all."""
    import json
    import pathlib

    baseline = json.loads(
        (pathlib.Path(__file__).resolve().parent / "fixtures" / "baseline_016.json").read_text(
            encoding="utf-8"
        )
    )
    assert render_files(_config())["COMPANY.md"] == baseline["COMPANY.md"]


# --- LICENSE.txt follows the platform convention ----------------------------


def test_license_names_the_company_and_leaves_publisher_and_licence_to_the_operator() -> None:
    """The tool knows the company; it cannot know a community handle and must not pick a
    licence on the operator's behalf."""
    text = render_files(_config())["LICENSE.txt"]
    assert text.startswith("Company: Indie Game Studio\n")
    for field in ("Publisher:", "Licence:", "Licence URL:"):
        line = next(line for line in text.splitlines() if line.startswith(field))
        assert "TODO" in line, f"{field} must be marked as needing completion"


def test_license_references_the_canonical_terms_rather_than_embedding_them() -> None:
    """Shipping third-party licence text is what ADR-011 removed from this repo."""
    text = render_files(_config())["LICENSE.txt"]
    assert "https://paperclip.community/companies-terms" in text
    assert "No warranty" not in text
    assert "royalty-free" not in text


def test_license_lineage_is_company_derivation_not_tool_provenance() -> None:
    text = render_files(_config())["LICENSE.txt"]
    assert "Lineage:\n(none — original work)" in text
    assert "Blueprints" not in text, "tool attribution belongs in the README, not the licence"


# --- feature 022: the README stops advertising what import discards ----------


def _classification(readme: str) -> str:
    """The classification section only — from its heading to the footer rule."""
    start = readme.index("## What import reads")
    return readme[start : readme.index("\n---", start)]


def test_readme_drops_goals_and_states_what_import_keeps() -> None:
    """C1.1/C1.2/C1.3 (FR-001, FR-002, FR-003).

    The two halves are asserted over one render on purpose. A bare absence check is
    satisfied by a template that renders nothing at all, so "no Goals section" is only
    evidence when something positive is asserted alongside it.

    Goals are the case ADR-022 already settled: they have no counterpart object, which is
    why the root agent's AGENTS.md carries them. Advertising a count of them in the README
    contradicted a decision this codebase already implements.
    """
    readme = render_files(_config())["README.md"]

    assert "| Goals |" not in readme
    assert "## Goals" not in readme
    for goal in _config().company.goals:
        assert goal not in readme, f"goal text still advertised: {goal!r}"

    block = _classification(readme)
    for landing in (
        "`.paperclip.yaml`",
        "`agents/<slug>/`",
        "`projects/<slug>/PROJECT.md`",
        "`tasks/<slug>/TASK.md`",
        "`skills/<slug>/SKILL.md`",
    ):
        assert landing in block, f"{landing} missing from the classification"
    assert "`COMPANY.md`" in block
    assert "read in part" in block


def test_readme_names_only_reader_facing_files_the_bundle_actually_contains() -> None:
    """C2.3 (FR-006).

    OPERATIONS.md and PROJECT-INVENTORY.md are rendered only when operations content
    exists. A single-agent bundle has neither, and a README that lists them sends the
    operator looking for files that are not in the tree.
    """
    from paperclip_blueprints.models.output import CompanyConfig
    from test_models import _full_config_kwargs

    single = render_files(_config())["README.md"]
    assert "OPERATIONS.md" not in single
    assert "PROJECT-INVENTORY.md" not in single

    full = render_files(CompanyConfig(**_full_config_kwargs()))["README.md"]
    assert "`OPERATIONS.md`" in _classification(full)
    assert "`PROJECT-INVENTORY.md`" in _classification(full)


def test_readme_classification_describes_rather_than_editorialises() -> None:
    """C2.4/C2.5 (FR-004, FR-005).

    The bundle states what lands and what does not. Characterising the difference — as a
    gap, a limitation, something the platform ought to do differently — is out of bounds
    for this repository, as is any classification finer than the file.
    """
    import re

    block = _classification(render_files(_config())["README.md"]).lower()
    for word in ("gap", "limitation", "unsupported", "unfortunately", "only", "fails", "should"):
        assert not re.search(rf"\b{word}\b", block), (
            f"editorialising word in classification: {word}"
        )


def test_readme_points_at_the_compatibility_record_reachably() -> None:
    """C3.1/C3.3 (FR-007).

    The reader holds a bundle, not a checkout, so the pointer has to be resolvable — but it
    does not need a second full URL to be so. The repository URL is already on the line, and
    the record is named relative to it, which is one link rather than two.
    """
    from paperclip_blueprints import __version__

    last = [
        line for line in render_files(_config())["README.md"].strip().splitlines() if line.strip()
    ][-1]
    assert __version__ in last
    assert "https://github.com/Grolea-HQ/paperclip-blueprints" in last
    assert "docs/platform-compatibility.md" in last
    assert "verified against" in last
    assert last.count("https://") == 1, "one link, not two"


def test_readme_pointer_is_suppressed_when_the_version_resolves_to_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """C3.2 (FR-008, SC-007).

    A bundle built from an uninstalled source tree stamps the fallback version, which is a
    key into no entry in the record while looking entirely authoritative. Silence beats a
    pointer that does not resolve — the plausible-looking failure is the one that does not
    announce itself. The stamp itself still renders; suppression is scoped to the pointer.
    """
    from paperclip_blueprints import UNKNOWN_VERSION
    from paperclip_blueprints.renderers import render as render_module

    monkeypatch.setattr(render_module, "__version__", UNKNOWN_VERSION)
    readme = render_files(_config())["README.md"]

    assert "platform-compatibility.md" not in readme
    assert "verified against" not in readme
    assert UNKNOWN_VERSION in readme, "the provenance stamp itself must survive"


def test_no_bundle_file_declares_a_platform_schema_revision() -> None:
    """C4.3 (FR-009). ADR-042: emitting nothing is the decision, not an omission."""
    from paperclip_blueprints.models.output import CompanyConfig
    from test_models import _full_config_kwargs

    for files in (render_files(_config()), render_files(CompanyConfig(**_full_config_kwargs()))):
        for path, content in files.items():
            assert "schemaVersion" not in content, f"{path} declares a schema revision"


def test_rendering_the_same_input_twice_is_byte_identical() -> None:
    """C4.2 (FR-010, SC-004). No clock entered the render path with the provenance pointer."""
    assert render_files(_config()) == render_files(_config())


def test_every_file_but_the_readme_matches_the_pre_022_baseline() -> None:
    """C4.1 (FR-011, SC-005).

    ``tests/fixtures/baseline_022.json`` was captured from the unmodified tree before any
    source edit in this feature, holding both the full-bundle and single-agent file maps.
    Re-capturing it from the edited tree would compare the implementation against itself
    and pass vacuously — ADR-036's third class, and the failure this project has hit twice
    this week.
    """
    import json
    import pathlib

    from paperclip_blueprints.models.output import CompanyConfig
    from test_models import _full_config_kwargs

    baseline = json.loads(
        (pathlib.Path(__file__).resolve().parent / "fixtures" / "baseline_022.json").read_text(
            encoding="utf-8"
        )
    )
    rendered = {
        "full": render_files(CompanyConfig(**_full_config_kwargs())),
        "single": render_files(_config()),
    }

    for kind, files in rendered.items():
        assert sorted(files) == sorted(baseline[kind]), f"{kind}: the set of rendered files changed"
        for path, content in sorted(baseline[kind].items()):
            if path == "README.md":
                continue
            assert files[path] == content, f"{kind}: {path} changed"

    # The README is the one file this feature is allowed to change — assert it did, so the
    # loop above cannot pass by the whole feature having silently done nothing.
    assert rendered["single"]["README.md"] != baseline["single"]["README.md"]


def test_readme_names_only_the_paperclip_yaml_keys_this_bundle_carries() -> None:
    """C2.3 (FR-006), applied to the platform-facing bullet.

    ``budgetMonthlyCents`` is emitted only when the brief declares capital, and the routines
    block only when a task recurs. A bullet naming them unconditionally sends the operator
    looking for keys that are not in the file — the goals defect one layer down.

    The assertion is against the rendered ``.paperclip.yaml`` rather than against expected
    text, so it cannot be satisfied by a sentence that merely happens to read correctly for
    the fixture.
    """
    from paperclip_blueprints.models.cadence import Cadence
    from paperclip_blueprints.models.output import CompanyConfig
    from paperclip_blueprints.models.task import TaskDefinition
    from test_models import _full_config_kwargs

    def task(slug: str, rec: str | None = None) -> TaskDefinition:
        return TaskDefinition(
            slug=slug,
            name=slug,
            project="launch-v1",
            assignee="cto",
            objective="o",
            completion_criteria=["done"],
            recurrence=Cadence.coerce(rec) if rec else None,
        )

    bare = _full_config_kwargs()
    rich = _full_config_kwargs(tasks=[task("ship"), task("scan", "mon,wed,fri")])
    rich["brief"] = rich["brief"].model_copy(update={"capital_monthly_eur": 500})

    shapes = [CompanyConfig(**bare), CompanyConfig(**rich), _config()]
    seen_budget, seen_routines = set(), set()

    for config in shapes:
        files = render_files(config)
        yaml_text = files[".paperclip.yaml"]
        bullet = next(
            line
            for line in files["README.md"].splitlines()
            if line.startswith("- `.paperclip.yaml`")
        )
        carries_budget = "budgetMonthlyCents" in yaml_text
        carries_routines = "routines:" in yaml_text

        assert ("monthly budget" in bullet) == carries_budget, bullet
        assert ("routine schedules" in bullet) == carries_routines, bullet
        # Unconditional halves stay unconditional.
        assert "adapter and model" in bullet
        assert "board-approval gate" in bullet

        seen_budget.add(carries_budget)
        seen_routines.add(carries_routines)

    # Both branches of each gate were exercised — otherwise the iff above is satisfied by a
    # bullet that is simply always right for one bundle shape.
    assert seen_budget == {True, False}
    assert seen_routines == {True, False}
