"""Feature 009 — skill→agent attachment wiring (ADR-020).

Import does not auto-attach skills to agents, so the bundle emits explicit per-agent
attach instructions (OPERATIONS.md for full bundles, README.md for single-agent) and a
pre-write closure check guarantees the instructions equal the declared `skills:` pairs.
All offline — no live API, no model call.
"""

from __future__ import annotations

import pytest

from paperclip_blueprints.models.agent import AgentDefinition, AgentSoul
from paperclip_blueprints.models.output import CompanyConfig
from paperclip_blueprints.renderers.attachments import (
    AttachmentPair,
    attach_step,
    attachment_pairs,
    attachments_by_agent,
    parse_attach_steps,
)
from paperclip_blueprints.renderers.bundle import BundleError, structural_check
from paperclip_blueprints.renderers.render import render_files
from test_models import _full_config_kwargs
from test_templates import _config


def _soul() -> AgentSoul:
    return AgentSoul(
        identity="I am here.",
        what_we_are="We are a studio.",
        product_reality="One product.",
        beliefs=["Idle is a success state; I wait between cycles."],
        how_i_act=["I decide."],
        what_i_dont_do=["I do not drift."],
        my_north_star="$1 forever.",
    )


def _agent(slug: str, skills: list[str], reports_to: str | None = None) -> AgentDefinition:
    return AgentDefinition(
        slug=slug,
        name=slug.upper(),
        title=slug.upper(),
        reports_to=reports_to,
        skills=skills,
        mandate="m",
        triggers=["t"],
        receives_from=[],
        hands_to=[],
        deliverables=["d"],
        can_approve=["a"],
        must_escalate=["e"],
        escalation_text="x",
        tools_role_specific="y",
        soul=_soul(),
    )


# --- T002: emitter ----------------------------------------------------------


def test_attachment_pairs_are_ordered_by_agent_then_skill() -> None:
    agents = [_agent("editor", ["fact-check", "house-style"]), _agent("researcher", ["vetting"])]
    assert attachment_pairs(agents) == [
        AttachmentPair("editor", "fact-check"),
        AttachmentPair("editor", "house-style"),
        AttachmentPair("researcher", "vetting"),
    ]


def test_shared_skill_yields_one_pair_per_declaring_agent() -> None:
    agents = [_agent("a", ["shared"]), _agent("b", ["shared"], reports_to="a")]
    pairs = attachment_pairs(agents)
    assert pairs.count(AttachmentPair("a", "shared")) == 1
    assert pairs.count(AttachmentPair("b", "shared")) == 1
    assert len(pairs) == 2


def test_empty_agents_yield_no_pairs() -> None:
    assert attachment_pairs([]) == []
    assert attachments_by_agent([]) == []


def test_attach_step_round_trips_through_parser() -> None:
    pair = AttachmentPair("editor", "fact-check")
    step = attach_step(pair)
    assert step == "Attach skill `fact-check` to agent `editor`"
    assert parse_attach_steps(step) == {("editor", "fact-check")}


def test_attachments_by_agent_groups_steps() -> None:
    agents = [_agent("editor", ["fact-check", "house-style"])]
    grouped = attachments_by_agent(agents)
    assert grouped == [
        (
            "editor",
            [
                "Attach skill `fact-check` to agent `editor`",
                "Attach skill `house-style` to agent `editor`",
            ],
        )
    ]


# --- T012: reuse boundary (FR-008) ------------------------------------------


def test_attach_step_is_the_single_reusable_unit() -> None:
    # ADR-019's referenced path composes an install prefix onto attach_step; it must be
    # callable on one pair in isolation (no duplication of the emitter).
    prefixed = "Install skill `x` from `gh:o/r@abc`, then " + attach_step(AttachmentPair("y", "x"))
    assert prefixed.endswith("Attach skill `x` to agent `y`")


# --- T004 / T008 / T009: rendering ------------------------------------------


def test_full_bundle_operations_lists_every_declared_pair() -> None:
    files = render_files(CompanyConfig(**_full_config_kwargs()))
    section = files["OPERATIONS.md"]
    assert "## Skill attachments" in section
    # full fixture: ceo→[release-checklist], cto→[architecture]
    assert parse_attach_steps(section) == {("ceo", "release-checklist"), ("cto", "architecture")}


def test_full_bundle_readme_points_to_operations() -> None:
    files = render_files(CompanyConfig(**_full_config_kwargs()))
    readme = files["README.md"]
    assert "## Skill attachments" in readme
    assert "OPERATIONS.md" in readme
    # the pointer form does not inline the steps
    assert parse_attach_steps(readme) == set()


def test_single_agent_readme_inlines_the_attach_steps() -> None:
    files = render_files(_config())  # single-agent: no OPERATIONS.md
    assert "OPERATIONS.md" not in files
    assert parse_attach_steps(files["README.md"]) == {("ceo", "release-checklist")}


# --- T010: closure check ----------------------------------------------------


def test_full_bundle_passes_attachment_closure() -> None:
    structural_check(render_files(CompanyConfig(**_full_config_kwargs())))  # must not raise


def test_single_bundle_passes_attachment_closure() -> None:
    structural_check(render_files(_config()))  # must not raise


def test_missing_attach_step_fails_closure() -> None:
    files = render_files(CompanyConfig(**_full_config_kwargs()))
    files["OPERATIONS.md"] = files["OPERATIONS.md"].replace(
        "Attach skill `architecture` to agent `cto`", ""
    )
    with pytest.raises(BundleError, match="missing pairs.*cto.*architecture"):
        structural_check(files)


def test_undeclared_attach_step_fails_closure() -> None:
    files = render_files(CompanyConfig(**_full_config_kwargs()))
    files["OPERATIONS.md"] = files["OPERATIONS.md"].replace(
        "## Budget review",
        "  - Attach skill `ghost` to agent `cto`\n\n## Budget review",
    )
    with pytest.raises(BundleError, match="undeclared pairs.*cto.*ghost"):
        structural_check(files)
