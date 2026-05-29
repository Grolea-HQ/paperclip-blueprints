"""Tests for the input models — CompanyBrief parsing and validation (T005)."""

from typing import Any

import pytest
from pydantic import ValidationError

from paperclip_blueprints.models.agent import AgentDefinition, AgentSoul
from paperclip_blueprints.models.company import CompanyDefinition
from paperclip_blueprints.models.input import (
    BriefValidationError,
    CompanyBrief,
    parse_brief,
)
from paperclip_blueprints.models.output import CompanyConfig
from paperclip_blueprints.models.skill import SkillDefinition

# A minimal but complete filled-in brief, structured like examples/input-template.md.
# Section bodies appear AFTER each "**Your ...:**" anchor so the parser ignores the
# instructional examples that precede the anchors.
VALID_BRIEF = """\
# Company Brief

## 1. Company name and slug

**Name:** Indie Game Studio

**Slug:** indie-game-studio

**One-sentence description:** A solo-founder studio shipping one premium mobile puzzle game a year.

## 2. North star

**Your north star:**

$30,000 monthly net revenue from premium sales within 12 months of launch.

## 3. Goals

**Your goals:**

1. Maintain a 4.6+ App Store rating across the live title
2. Ship one major content update every 6 weeks on cadence
3. Keep refund rate below 3% quarter over quarter

## 4. We are

**Your "we are" paragraph:**

We are a single-title premium mobile studio. One game, polished relentlessly,
sold once at a fair price. We do not chase engagement metrics.

## 5. We are NOT

**Your "we are not" list:**

1. **We are NOT** a free-to-play studio. No loot boxes, no energy timers; one-time purchase only.
2. **We are NOT** a multi-title shop. We do not split focus; the live title gets all attention.

## 6. Constraints

**Your constraints:**

1. One title at a time. Focus is the moat.
2. No dark patterns. Every monetization decision is honest by default.

## 7. Use case pattern (optional)

**Your choice:** custom

**Notes if customizing the pattern:** Keep it lean.

## 8. Governance spectrum position

**Your choice:** balanced

**Notes:** Tighter on anything store-facing for the first 30 days.

## 9. Operator working pattern

- **Hours per week (operator review time):** 6
- **Capital cap (EUR/month, for AI infrastructure spend):** 150
- **Capital cap (EUR, one-time setup):** 400

## 10. Adapter preferences (optional)

**Your overrides:**

- CEO → claudelocal opus

## 11. Anything else

**Other context:**

Evenings only; optimize for async review.
"""


def _brief_kwargs(**overrides: Any) -> dict[str, Any]:
    """Valid kwargs for constructing a CompanyBrief directly, with overrides."""
    base: dict[str, Any] = {
        "name": "Indie Game Studio",
        "slug": "indie-game-studio",
        "description": "A solo-founder studio shipping one polished premium puzzle game per year.",
        "north_star": "$30,000 monthly net revenue from premium sales within 12 months.",
        "goals": [
            "Maintain a 4.6+ App Store rating across the live title",
            "Keep refund rate below 3% quarter over quarter",
        ],
        "we_are": "We are a single-title premium mobile studio.",
        "we_are_not": [
            "We are NOT a free-to-play studio.",
            "We are NOT a multi-title shop.",
        ],
        "constraints": ["One title at a time.", "No dark patterns."],
        "governance_position": "balanced",
    }
    base.update(overrides)
    return base


# --- Direct model validation ------------------------------------------------


def test_valid_brief_constructs() -> None:
    brief = CompanyBrief(**_brief_kwargs())
    assert brief.slug == "indie-game-studio"
    assert brief.governance_position == "balanced"


def test_slug_must_be_lowercase_hyphenated() -> None:
    with pytest.raises(ValueError):
        CompanyBrief(**_brief_kwargs(slug="Indie Game Studio"))


def test_description_word_limit() -> None:
    long_desc = " ".join(["word"] * 35)
    with pytest.raises(ValueError):
        CompanyBrief(**_brief_kwargs(description=long_desc))


def test_we_are_not_requires_two_entries() -> None:
    with pytest.raises(ValueError):
        CompanyBrief(**_brief_kwargs(we_are_not=["We are NOT a free-to-play studio."]))


def test_constraints_requires_two_entries() -> None:
    with pytest.raises(ValueError):
        CompanyBrief(**_brief_kwargs(constraints=["One title at a time."]))


def test_governance_position_enum() -> None:
    with pytest.raises(ValueError):
        CompanyBrief(**_brief_kwargs(governance_position="anarchic"))


def test_task_shaped_north_star_rejected() -> None:
    with pytest.raises(ValueError):
        CompanyBrief(**_brief_kwargs(north_star="Launch a landing page for the product"))


def test_task_shaped_goal_rejected() -> None:
    with pytest.raises(ValueError):
        CompanyBrief(
            **_brief_kwargs(
                goals=[
                    "Build a marketing website",
                    "Keep refund rate below 3% quarter over quarter",
                ]
            )
        )


def test_outcome_shaped_goal_without_leading_verb_passes() -> None:
    # "Weekly send shipped ..." has no leading task verb -> not flagged.
    brief = CompanyBrief(
        **_brief_kwargs(
            goals=[
                "Weekly send shipped on cadence with the founder as the only author",
                "Free-to-paid conversion above 2.5%",
            ]
        )
    )
    assert len(brief.goals) == 2


# --- Markdown parsing -------------------------------------------------------


def test_parse_valid_brief() -> None:
    brief = parse_brief(VALID_BRIEF)
    assert brief.name == "Indie Game Studio"
    assert brief.slug == "indie-game-studio"
    assert brief.description.startswith("A solo-founder studio")
    assert "30,000" in brief.north_star
    assert len(brief.goals) == 3
    assert len(brief.we_are_not) == 2
    assert len(brief.constraints) == 2
    assert brief.use_case_pattern == "custom"
    assert brief.governance_position == "balanced"
    assert brief.hours_per_week == 6
    assert brief.capital_monthly_eur == 150


def test_parse_aggregates_all_errors() -> None:
    # Leave required placeholders unfilled in two sections and break the slug.
    broken = VALID_BRIEF.replace("indie-game-studio", "Indie Studio").replace(
        "$30,000 monthly net revenue from premium sales within 12 months of launch.",
        "[Replace with one measurable, time-bound, persistent-outcome statement.]",
    )
    with pytest.raises(BriefValidationError) as exc:
        parse_brief(broken)
    messages = str(exc.value)
    # both the slug problem and the missing north star should be reported together
    assert "slug" in messages.lower()
    assert "north" in messages.lower()


# --- US1 models: agent, skill, output (T017) --------------------------------


def _soul_kwargs(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "identity": "I am the Founder/CEO of the studio.",
        "what_we_are": "We are a single-title premium studio.",
        "product_reality": "The product is one polished game.",
        "beliefs": [
            "Focus is the moat.",
            "Idle is a success state — between cycles, I wait rather than invent work.",
        ],
        "how_i_act": ["I decide quickly on scope, slowly on price."],
        "what_i_dont_do": ["I do not ship dark patterns."],
        "my_north_star": "$30,000 monthly net revenue within 12 months.",
    }
    base.update(overrides)
    return base


def _agent_kwargs(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "slug": "ceo",
        "name": "Founder / CEO",
        "title": "Founder / CEO",
        "reports_to": None,
        "skills": ["release-checklist"],
        "mandate": "Owns the north star and ships the title.",
        "triggers": ["A release candidate is ready for sign-off."],
        "receives_from": [],
        "hands_to": [],
        "deliverables": ["Approved release builds."],
        "can_approve": ["Store metadata within the published plan."],
        "must_escalate": ["Pricing changes."],
        "escalation_text": "Escalate to the operator on pricing or scope cuts.",
        "tools_role_specific": "Uses App Store Connect to review build status only.",
        "soul": AgentSoul(**_soul_kwargs()),
    }
    base.update(overrides)
    return base


def test_agent_definition_constructs() -> None:
    agent = AgentDefinition(**_agent_kwargs())
    assert agent.reports_to is None
    assert agent.skills == ["release-checklist"]
    assert isinstance(agent.soul, AgentSoul)


def test_soul_requires_idle_state_belief() -> None:
    with pytest.raises(ValueError):
        AgentSoul(**_soul_kwargs(beliefs=["Focus is the moat.", "Ship often."]))


def test_skill_definition_constructs() -> None:
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
    assert skill.references == []


def test_company_config_single_agent() -> None:
    company = CompanyDefinition(
        name="Indie Game Studio",
        description="A solo-founder premium mobile puzzle studio.",
        goals=["4.6+ rating sustained", "refund rate below 3% per quarter"],
        we_are="We are a single-title premium mobile studio.",
        we_are_not=["We are NOT a free-to-play studio.", "We are NOT a multi-title shop."],
        north_star="$30,000 monthly net revenue within 12 months.",
        constraints=["One title at a time.", "No dark patterns."],
    )
    skill = SkillDefinition(
        slug="release-checklist",
        name="release-checklist",
        description="Pre-submission checklist.",
        when_to_load=["RC ready."],
        inputs=["build"],
        procedure=["check"],
        outputs=["signed build"],
        anti_patterns=["skip smoke"],
    )
    config = CompanyConfig(
        brief=CompanyBrief(**_brief_kwargs()),
        company=company,
        agent=AgentDefinition(**_agent_kwargs()),
        skill=skill,
    )
    assert config.license_kind == "Proprietary"
    assert config.agent.slug == "ceo"


def _company_kwargs(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "name": "Indie Game Studio",
        "description": "A solo-founder premium mobile puzzle studio.",
        "goals": ["4.6+ rating sustained", "refund rate below 3% per quarter"],
        "we_are": "We are a single-title premium mobile studio.",
        "we_are_not": ["We are NOT a free-to-play studio.", "We are NOT a multi-title shop."],
        "north_star": "$30,000 monthly net revenue within 12 months.",
        "constraints": ["One title at a time.", "No dark patterns."],
    }
    base.update(overrides)
    return base


def test_company_definition_rejects_task_shaped_goal() -> None:
    # Q5: the LLM must not emit a task-shaped goal (CLAUDE.md failure-mode #8).
    with pytest.raises(ValidationError):
        CompanyDefinition(**_company_kwargs(goals=["Launch the game", "Build the brand"]))


def test_company_definition_rejects_task_shaped_north_star() -> None:
    with pytest.raises(ValidationError):
        CompanyDefinition(**_company_kwargs(north_star="Launch the game"))


def test_company_definition_rejects_unknown_tone() -> None:
    # Q8: tone is a closed set mirroring the identity prompt's offered colors.
    with pytest.raises(ValidationError):
        CompanyDefinition(**_company_kwargs(tone="teal"))


def test_company_definition_accepts_prompt_offered_tone() -> None:
    assert CompanyDefinition(**_company_kwargs(tone="purple")).tone == "purple"
