"""Feature 010 — object-model constitution & governance delivery (ADR-022).

This file covers US2 (no filesystem-read assumptions), US5 (idle-state correction), and
US1 (governance reaches agents via the instruction bundle). All offline — no live API.
US3/US4 land in later increments.
"""

from __future__ import annotations

from paperclip_blueprints.generators.client import load_prompt
from paperclip_blueprints.models.output import CompanyConfig
from paperclip_blueprints.renderers.render import render_files
from paperclip_blueprints.validators.schema_shape import _check_idle_state, check_schema_shape
from test_models import _full_config_kwargs
from test_templates import _config

# `para-memory-files` dropped from the marker set in ADR-023 — it is now a legitimate
# built-in skill slug, not filesystem-read prose (still caught by the memory-path markers).
_FS_MARKERS = ("## File system", "Company root", "Own memory", "memory/<date>")


# --- US2: no filesystem-read assumptions; HEARTBEAT empty --------------------


def test_tools_md_has_no_filesystem_section() -> None:
    tools = render_files(_config())["agents/ceo/TOOLS.md"]
    for marker in _FS_MARKERS:
        assert marker not in tools, marker
    # the company-tree secrets phrasing is gone too
    assert "company tree" not in tools


def test_heartbeat_has_no_file_or_rules_refs() -> None:
    hb = render_files(_config())["agents/ceo/HEARTBEAT.md"]
    # ADR-022: the empty runtime journal references NO other bundle file — not
    # OPERATIONS.md (dropped on import), not the filesystem-memory paths, and not
    # even AGENTS.md. Rules live in AGENTS.md; HEARTBEAT.md just stays empty.
    for bad in ("OPERATIONS.md", "memory/<date>", "para-memory-files", "AGENTS.md"):
        assert bad not in hb


def test_s13_is_clean_on_a_generated_bundle() -> None:
    config = _config()
    files = render_files(config)
    assert not any(x.startswith("S13") for x in check_schema_shape(config, files))


def test_s13_flags_an_injected_filesystem_ref() -> None:
    config = _config()
    files = render_files(config)
    files["agents/ceo/TOOLS.md"] += "\n## File system\n- Company root: `x/`\n"
    assert any(x.startswith("S13") for x in check_schema_shape(config, files))


# --- US5: idle-state protocol correction -------------------------------------


def test_operations_prompt_corrects_idle_state() -> None:
    p = load_prompt("operations_generator").lower()
    assert "never" in p and "in_progress" in p
    assert "schedule" in p  # the routine schedule is the liveness
    assert "zero output" in p or "one short-lived issue" in p


def test_v_idle_rejects_in_progress_as_liveness() -> None:
    bad = "Leave the issue in_progress when a routine is the live continuation path."
    assert _check_idle_state(bad)


def test_v_idle_passes_the_corrected_protocol() -> None:
    ok = (
        "Idle is a success state: one short-lived issue per routine run, closed that run; "
        "never leave an issue in_progress as a liveness marker (the schedule is the liveness); "
        "zero output on empty wakes."
    )
    assert _check_idle_state(ok) == []


def test_full_fixture_operations_passes_v_idle() -> None:
    config = CompanyConfig(**_full_config_kwargs())
    files = render_files(config)
    assert not any(x.startswith("V-idle") for x in check_schema_shape(config, files))


# --- US1: governance reaches agents via the instruction bundle ---------------


def test_ceo_agents_md_carries_governance() -> None:
    ceo = render_files(CompanyConfig(**_full_config_kwargs()))["agents/ceo/AGENTS.md"]
    for sec in (
        "## Idle-state protocol",
        "## Company goals",
        "## Board-gate and approval",
        "## Critical rules",
    ):
        assert sec in ceo, sec
    assert "Never ship without sign-off." in ceo  # the critical rule reached the carrier


def test_non_ceo_agents_md_has_idle_but_not_ceo_sections() -> None:
    cto = render_files(CompanyConfig(**_full_config_kwargs()))["agents/cto/AGENTS.md"]
    assert "## Idle-state protocol" in cto
    for sec in ("## Company goals", "## Board-gate and approval", "## Critical rules"):
        assert sec not in cto


def test_idle_state_protocol_reaches_each_agents_md() -> None:
    files = render_files(CompanyConfig(**_full_config_kwargs()))
    assert "Idle is a success state." in files["agents/ceo/AGENTS.md"]
    assert "Idle is a success state." in files["agents/cto/AGENTS.md"]


def test_v_gov_is_clean_on_full_bundle() -> None:
    config = CompanyConfig(**_full_config_kwargs())
    files = render_files(config)
    assert not any(x.startswith("V-gov") for x in check_schema_shape(config, files))


def test_v_gov_flags_missing_ceo_governance() -> None:
    config = CompanyConfig(**_full_config_kwargs())
    files = render_files(config)
    files["agents/ceo/AGENTS.md"] = files["agents/ceo/AGENTS.md"].replace(
        "## Critical rules", "## Removed"
    )
    assert any(
        x.startswith("V-gov") and "Critical rules" in x for x in check_schema_shape(config, files)
    )


# --- US3: the hiring board-gate ships as a structured company setting ---------


def test_paperclip_yaml_sets_the_hiring_board_gate() -> None:
    y = render_files(CompanyConfig(**_full_config_kwargs()))[".paperclip.yaml"]
    assert "requireBoardApprovalForNewAgents: true" in y


def test_s14_flags_a_missing_hiring_gate() -> None:
    config = CompanyConfig(**_full_config_kwargs())
    files = render_files(config)
    files[".paperclip.yaml"] = files[".paperclip.yaml"].replace(
        "requireBoardApprovalForNewAgents: true", "requireBoardApprovalForNewAgents: false"
    )
    assert any(x.startswith("S14") for x in check_schema_shape(config, files))
