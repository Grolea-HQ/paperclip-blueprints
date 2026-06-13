"""Tests that templates render the exact single-agent bundle shape (T020).

Asserts against contracts/bundle-output.md: file set, schema strings, frontmatter
keys, section headings, single-agent mermaid (no edges), and the HEARTBEAT stub.
"""

from pathlib import Path

from paperclip_blueprints.models.agent import AgentDefinition, AgentSoul
from paperclip_blueprints.models.company import CompanyDefinition
from paperclip_blueprints.models.input import CompanyBrief
from paperclip_blueprints.models.output import CompanyConfig
from paperclip_blueprints.models.skill import SkillDefinition
from paperclip_blueprints.renderers.render import render_files


def _config() -> CompanyConfig:
    brief = CompanyBrief(
        name="Indie Game Studio",
        slug="indie-game-studio",
        description="A solo-founder premium mobile puzzle studio shipping one game a year.",
        north_star="$30,000 monthly net revenue within 12 months.",
        goals=["4.6+ rating sustained", "refund rate below 3% per quarter"],
        we_are="We are a single-title premium mobile studio.",
        we_are_not=["We are NOT a free-to-play studio.", "We are NOT a multi-title shop."],
        constraints=["One title at a time.", "No dark patterns."],
        governance_position="balanced",
    )
    company = CompanyDefinition(
        name="Indie Game Studio",
        description="A solo-founder premium mobile puzzle studio.",
        goals=["4.6+ rating sustained", "refund rate below 3% per quarter"],
        we_are="We are a single-title premium mobile studio.",
        we_are_not=["We are NOT a free-to-play studio.", "We are NOT a multi-title shop."],
        north_star="$30,000 monthly net revenue within 12 months.",
        constraints=["One title at a time.", "No dark patterns."],
        tone="purple",
    )
    soul = AgentSoul(
        identity="I am the Founder/CEO.",
        what_we_are="We are a single-title premium studio.",
        product_reality="One polished game.",
        beliefs=["Focus is the moat.", "Idle is a success state; I wait between cycles."],
        how_i_act=["I decide quickly on scope, slowly on price."],
        what_i_dont_do=["I do not ship dark patterns."],
        my_north_star="$30,000 monthly net revenue within 12 months.",
    )
    agent = AgentDefinition(
        slug="ceo",
        name="Founder / CEO",
        title="Founder / CEO",
        reports_to=None,
        role="ceo",
        skills=["release-checklist"],
        mandate="Owns the north star and ships the title.",
        triggers=["A release candidate is ready."],
        receives_from=[],
        hands_to=[],
        deliverables=["Approved release builds."],
        can_approve=["Store metadata within the plan."],
        must_escalate=["Pricing changes."],
        escalation_text="Escalate to the operator on pricing.",
        tools_role_specific="Reviews build status in App Store Connect.",
        soul=soul,
    )
    skill = SkillDefinition(
        slug="release-checklist",
        name="release-checklist",
        description="Pre-submission checklist for a store release.",
        when_to_load=["A build is a release candidate."],
        inputs=["The candidate build."],
        procedure=["Verify the build number.", "Run the smoke pass."],
        outputs=["A signed-off build."],
        anti_patterns=["Shipping without the smoke pass."],
    )
    return CompanyConfig(
        mode="single", brief=brief, company=company, agents=[agent], skills=[skill]
    )


def test_exact_file_set() -> None:
    files = render_files(_config())
    assert set(files) == {
        ".paperclip.yaml",
        "COMPANY.md",
        "README.md",
        "LICENSE.txt",
        "agents/ceo/AGENTS.md",
        "agents/ceo/SOUL.md",
        "agents/ceo/HEARTBEAT.md",
        "agents/ceo/TOOLS.md",
        "skills/release-checklist/SKILL.md",
    }


def test_paperclip_yaml_schema_and_sidebar() -> None:
    out = render_files(_config())[".paperclip.yaml"]
    assert "schema: paperclip/v1" in out
    assert "agents: [ceo]" in out
    assert "projects: []" in out


def test_paperclip_yaml_emits_ceo_role_not_empty() -> None:
    """The CEO must import as role=ceo, not fall through to "agent".

    Paperclip's importer reads agents.<slug>.role and, via asString(""),
    treats '' as null → falls back to "agent" (company-portability.ts:2600,
    665-669), stripping CEO permissions. So role must be "ceo" — never '',
    never omitted — for the single-agent CEO bundle.
    """
    from ruamel.yaml import YAML

    out = render_files(_config())[".paperclip.yaml"]
    assert "role: ''" not in out  # the empty string that triggers the fallback
    role = YAML(typ="safe").load(out)["agents"]["ceo"]["role"]
    assert role == "ceo"


def test_paperclip_yaml_omits_role_when_unset() -> None:
    """When agent.role is None (v0.1b non-CEO agents), the role line is omitted.

    Guards the v0.1b code path before it exists: an unset role must produce no
    `role:` line at all — not `role:`, `role: null`, or `role: ''` — so the
    importer applies its own "agent" default rather than reading a junk value.
    """
    config = _config()
    config.agents[0].role = None
    out = render_files(config)[".paperclip.yaml"]
    assert "role:" not in out


def test_company_md_schema_and_sections() -> None:
    out = render_files(_config())["COMPANY.md"]
    assert out.startswith("---\nschema: agentcompanies/v1")
    assert "## Identity" in out
    assert "**We are not.**" in out
    assert "**North star.**" in out
    assert "**Constraints.**" in out


def test_company_md_sources_is_metadata_sibling_not_under_paperclip() -> None:
    """Guard: `sources` lives at metadata.sources, not metadata.paperclip.sources.

    The reference companies put `sources` as a sibling of `paperclip` under
    `metadata`. A one-level YAML-nesting slip would bury it inside `paperclip` —
    invisible to string/section checks, so assert the parsed shape directly.
    """
    from ruamel.yaml import YAML

    out = render_files(_config())["COMPANY.md"]
    block = out.split("---\n", 2)[1]  # frontmatter between the first two fences
    metadata = YAML(typ="safe").load(block)["metadata"]
    assert "sources" in metadata, "metadata.sources must exist (sibling of paperclip)"
    assert "sources" not in metadata["paperclip"], (
        "sources must NOT be nested under metadata.paperclip"
    )
    assert metadata["sources"] == [{"kind": "url"}]


def test_agents_md_frontmatter_and_sections() -> None:
    out = render_files(_config())["agents/ceo/AGENTS.md"]
    assert "schema: agentcompanies/v1" in out
    assert "reportsTo: null" in out
    assert "skills: [release-checklist]" in out
    for heading in (
        "## Mandate",
        "## Triggers",
        "## Workflow handoffs",
        "## Deliverables",
        "## Decision rights",
        "## Escalation",
    ):
        assert heading in out


def test_soul_md_has_seven_sections_no_frontmatter() -> None:
    out = render_files(_config())["agents/ceo/SOUL.md"]
    assert not out.startswith("---")
    for heading in (
        "## Identity",
        "## What we are",
        "## Product reality",
        "## What I believe in",
        "## How I act",
        "## What I don't do",
        "## My north star",
    ):
        assert heading in out
    assert "idle" in out.lower()


def test_heartbeat_is_stub() -> None:
    out = render_files(_config())["agents/ceo/HEARTBEAT.md"]
    assert "intentionally near-empty" in out
    assert "*(Empty" in out
    # Everything below the H1 must match the canonical stub verbatim (Q2): the
    # stub is hand-authored, so the generated file must not drift from it. The
    # canonical body is frozen in a first-party fixture (the reference-companies
    # oracle was removed from the public repo — see open-source release prep).
    ref = Path("tests/fixtures/heartbeat_canonical_body.md").read_text(encoding="utf-8")
    assert out.split("\n", 1)[1].rstrip("\n") == ref.rstrip("\n")


def test_readme_single_agent_mermaid_no_edges() -> None:
    out = render_files(_config())["README.md"]
    assert "```mermaid" in out
    assert 'ceo["Founder / CEO — Founder / CEO"]' in out
    assert "-->" not in out  # single agent has no reporting edges


def test_skill_md_frontmatter_and_sections() -> None:
    out = render_files(_config())["skills/release-checklist/SKILL.md"]
    assert "schema: agentcompanies/v1" in out
    assert "## Procedure" in out
    assert "1. Verify the build number." in out


def test_license_default_proprietary() -> None:
    out = render_files(_config())["LICENSE.txt"]
    assert "Proprietary" in out


# --- full-bundle templates (T013) -------------------------------------------

from paperclip_blueprints.models.output import CompanyConfig  # noqa: E402
from test_models import _full_config_kwargs  # noqa: E402


def _full_files() -> dict[str, str]:
    return render_files(CompanyConfig(**_full_config_kwargs()))


def test_full_operations_md_sections() -> None:
    out = _full_files()["OPERATIONS.md"]
    assert "# Operations —" in out
    assert "## Anti-drift checks" in out
    assert "## Routine slots" in out


def test_full_project_and_task_md() -> None:
    files = _full_files()
    proj = files["projects/launch-v1/PROJECT.md"]
    assert "schema: agentcompanies/v1" in proj
    assert "## Success condition" in proj
    task = files["tasks/ship/TASK.md"]
    assert "project: launch-v1" in task
    assert "assignee: cto" in task
    assert "## Completion criteria" in task


def test_full_project_inventory_seeded() -> None:
    out = _full_files()["PROJECT-INVENTORY.md"]
    assert "## Starter projects" in out
    assert "### Launch v1" in out
    assert "`in_progress`" in out


def test_full_readme_multi_node_mermaid_with_edges() -> None:
    out = _full_files()["README.md"]
    assert "| Agents | 2 |" in out
    assert "ceo --> cto" in out
    assert 'cto["CTO — CTO"]' in out


def test_full_paperclip_yaml_maps() -> None:
    out = _full_files()[".paperclip.yaml"]
    assert "agents: [ceo, cto]" in out
    assert "projects: [launch-v1]" in out
    assert "launch-v1:" in out  # bare project key in the projects map


# --- per-agent budgets (ADR-012, US1/US2/US3) -------------------------------

from ruamel.yaml import YAML  # noqa: E402

from test_models import _brief_kwargs  # noqa: E402


def _capped_full(eur: int = 100, governance: str = "balanced") -> CompanyConfig:
    """A full bundle whose brief states a monthly capital cap."""
    brief = CompanyBrief(**_brief_kwargs(capital_monthly_eur=eur, governance_position=governance))
    return CompanyConfig(**_full_config_kwargs(brief=brief))


def test_budgets_render_when_cap_present() -> None:
    # US1: every agent carries a budgetMonthlyCents; owner highest; sum within cap.
    out = render_files(_capped_full(100, "balanced"))[".paperclip.yaml"]
    data = YAML(typ="safe").load(out)
    ceo = data["agents"]["ceo"]["budgetMonthlyCents"]
    cto = data["agents"]["cto"]["budgetMonthlyCents"]
    assert isinstance(ceo, int) and isinstance(cto, int)
    assert ceo > cto  # owner outweighs a generic report
    assert ceo + cto == 100 * 70  # balanced pool, exact
    assert ceo + cto <= 100 * 100  # within the cap


def test_no_budget_keys_when_no_cap() -> None:
    # US2: default fixture has no cap → no budget figures at all.
    out = _full_files()[".paperclip.yaml"]
    assert "budgetMonthlyCents" not in out


def test_operations_note_capped() -> None:
    # US2 / FR-009: capped bundle tells the operator the caps are starting points.
    out = render_files(_capped_full())["OPERATIONS.md"]
    assert "## Budget review" in out
    assert "conservative starting caps" in out


def test_operations_note_uncapped() -> None:
    # US2 / FR-008: cap-less bundle tells the operator to set budgets first.
    out = _full_files()["OPERATIONS.md"]
    assert "## Budget review" in out
    assert "before enabling heartbeats" in out
    assert "no" in out.lower()


def test_single_agent_gets_full_scaled_pool() -> None:
    # US3 / FR-010: the lone owner receives the whole governance-scaled pool.
    config = _config()
    config.brief.capital_monthly_eur = 40
    config.brief.governance_position = "loose"
    out = render_files(config)[".paperclip.yaml"]
    data = YAML(typ="safe").load(out)
    assert data["agents"]["ceo"]["budgetMonthlyCents"] == 40 * 90
    assert data["agents"]["ceo"]["budgetMonthlyCents"] <= 40 * 100


def test_pool_too_small_warns_via_sink() -> None:
    # FR-006: a tiny cap over the org triggers the advisory warning through warn().
    warnings: list[str] = []
    render_files(_capped_full(1, "tight"), warn=warnings.append)
    assert warnings and "too small" in warnings[0]
