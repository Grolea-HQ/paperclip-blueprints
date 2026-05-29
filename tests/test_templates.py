"""Tests that templates render the exact single-agent bundle shape (T020).

Asserts against contracts/bundle-output.md: file set, schema strings, frontmatter
keys, section headings, single-agent mermaid (no edges), and the HEARTBEAT stub.
"""

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
        skills=["release-checklist"],
        mandate="Owns the north star and ships the title.",
        triggers=["A release candidate is ready."],
        receives_from=[],
        hands_to=[],
        deliverables=["Approved release builds."],
        can_approve=["Store metadata within the plan."],
        must_escalate=["Pricing changes (budget_override)."],
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
    return CompanyConfig(brief=brief, company=company, agent=agent, skill=skill)


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


def test_company_md_schema_and_sections() -> None:
    out = render_files(_config())["COMPANY.md"]
    assert out.startswith("---\nschema: agentcompanies/v1")
    assert "## Identity" in out
    assert "**We are not.**" in out
    assert "**North star.**" in out
    assert "**Constraints.**" in out


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
