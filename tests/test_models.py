"""Tests for the input models — CompanyBrief parsing and validation (T005)."""

from typing import Any

import pytest
from pydantic import ValidationError

from paperclip_blueprints.models.agent import AgentDefinition, AgentSoul
from paperclip_blueprints.models.cadence import Cadence
from paperclip_blueprints.models.company import CompanyDefinition
from paperclip_blueprints.models.input import (
    BriefValidationError,
    CompanyBrief,
    parse_brief,
    slug_divergence_warning,
)
from paperclip_blueprints.models.operations import OperationsDefinition
from paperclip_blueprints.models.org_plan import (
    AgentStub,
    OrgPlan,
    ProjectStub,
    TaskStub,
)
from paperclip_blueprints.models.output import CompanyConfig
from paperclip_blueprints.models.project import ProjectDefinition
from paperclip_blueprints.models.skill import SkillDefinition
from paperclip_blueprints.models.task import TaskDefinition

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


def test_slug_divergence_warning_none_when_slug_matches_slugified_name() -> None:
    # "Indie Game Studio" slugifies to "indie-game-studio" — the default slug.
    brief = CompanyBrief(**_brief_kwargs())
    assert slug_divergence_warning(brief) is None


def test_slug_divergence_warning_names_both_values_on_divergence() -> None:
    brief = CompanyBrief(**_brief_kwargs(slug="keying-test"))
    warning = slug_divergence_warning(brief)
    assert warning is not None
    # names both the operator slug and the derived form, and stays advisory
    assert "keying-test" in warning
    assert "indie-game-studio" in warning
    assert "slugify(name)" in warning


def test_slug_divergence_warning_none_for_non_ascii_name() -> None:
    # An all-non-ASCII name has no derivable ASCII slug (slugify → ""), which is a
    # separate concern — no spurious "differs from ''" warning here.
    brief = CompanyBrief(**_brief_kwargs(name="株式会社", slug="kabushiki-gaisha"))
    assert slug_divergence_warning(brief) is None


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
    # Section-7 "Notes if customizing the pattern" prose is captured (the binding
    # org-customization channel threaded into org_planner — ADR-022 US3 follow-up).
    assert brief.use_case_notes == "Keep it lean."
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


# --- run-policy override channel (feature 014) ------------------------------

# --- structured cadence (feature 018) ----------------------------------------


def test_cadence_accepts_a_named_weekday() -> None:
    # C1.1
    c = Cadence.of("weekly", days_of_week=["tue"])
    assert c.frequency == "weekly"
    assert c.days_of_week == [2]


def test_cadence_accepts_a_day_of_month() -> None:
    # C1.2 — the case no cadence string could ever express.
    c = Cadence.of("monthly", day_of_month=5)
    assert c.day_of_month == 5


def test_cadence_accepts_a_day_and_months() -> None:
    # C1.3
    c = Cadence.of("quarterly", day_of_month=8, months=["jan", "apr", "jul", "oct"])
    assert c.day_of_month == 8
    assert c.months == [1, 4, 7, 10]


def test_cadence_rejects_inconsistent_parts() -> None:
    # C1.4 — a part that cannot apply to the stated frequency is a planning error, not a value
    # to silently ignore.
    with pytest.raises(ValidationError, match="days_of_week"):
        Cadence.of("monthly", days_of_week=["tue"])
    with pytest.raises(ValidationError, match="day_of_month"):
        Cadence.of("weekly", day_of_month=5)
    with pytest.raises(ValidationError, match="months"):
        Cadence.of("weekly", months=["jan"])
    with pytest.raises(ValidationError):
        Cadence.of("daily", day_of_month=5)


def test_cadence_rejects_empty_stated_lists() -> None:
    # C1.5 — state a value or omit the field; an empty list is neither.
    with pytest.raises(ValidationError):
        Cadence.of("weekly", days_of_week=[])
    with pytest.raises(ValidationError):
        Cadence.of("quarterly", months=[])


def test_cadence_rejects_out_of_range_day_of_month() -> None:
    with pytest.raises(ValidationError):
        Cadence.of("monthly", day_of_month=0)
    with pytest.raises(ValidationError):
        Cadence.of("monthly", day_of_month=32)


def test_cadence_day_above_28_is_accepted_and_reported() -> None:
    # C1.6 — valid, but it will not fire in February.
    c = Cadence.of("monthly", day_of_month=31)
    assert c.day_of_month == 31
    assert c.warnings(), "a day above 28 must be reported"
    assert not Cadence.of("monthly", day_of_month=28).warnings()


def test_cadence_coerces_legacy_strings() -> None:
    # C1.7 — an older plan, or a model that ignores the structured shape, still works.
    assert Cadence.coerce("weekly") == Cadence.of("weekly")
    assert Cadence.coerce("tue") == Cadence.of("weekly", days_of_week=["tue"])
    assert Cadence.coerce("tuesday") == Cadence.of("weekly", days_of_week=["tue"])
    assert Cadence.coerce("mon,wed,fri") == Cadence.of("weekly", days_of_week=["mon", "wed", "fri"])
    assert Cadence.coerce("monthly") == Cadence.of("monthly")
    assert Cadence.coerce("quarterly") == Cadence.of("quarterly")


def test_cadence_coercion_raises_rather_than_defaulting() -> None:
    # C1.8 / FR-007. Today an unrecognised cadence falls through to the default day pattern —
    # `* * 1`, weekly Monday — so "monthly on the 5th" silently becomes a WEEKLY routine. The
    # contract rewarded discarding the day. That path must not survive.
    for bad in ("monthly on the 5th", "whenever", "every other tuesday", ""):
        with pytest.raises(ValueError):
            Cadence.coerce(bad)


def test_task_definition_accepts_a_structured_cadence_and_coerces_a_string() -> None:
    # The field is one type downstream; legacy input is coerced at the boundary, not branched on.
    t = TaskDefinition(
        slug="s",
        name="n",
        project="p",
        assignee="a",
        objective="o",
        completion_criteria=["d"],
        recurrence=Cadence.coerce("tue"),
    )
    assert isinstance(t.recurrence, Cadence)
    assert t.recurrence.days_of_week == [2]


# --- section-9 timezone (feature 017 / ADR-038) ------------------------------


def _brief_with_timezone(value: str) -> str:
    """VALID_BRIEF with a section-9 timezone line carrying ``value``."""
    return VALID_BRIEF.replace(
        "- **Capital cap (EUR, one-time setup):** 400",
        f"- **Capital cap (EUR, one-time setup):** 400\n- **Timezone (optional):** {value}",
    )


def test_parse_brief_reads_section_9_timezone() -> None:
    # C1.1 through parse_brief, not just the validator.
    assert (
        parse_brief(_brief_with_timezone("Europe/Helsinki")).routine_timezone == "Europe/Helsinki"
    )


def test_parse_brief_canonicalises_timezone_casing() -> None:
    # C1.2 — recoverable intent accepted; the canonical spelling is stored.
    assert (
        parse_brief(_brief_with_timezone("europe/helsinki")).routine_timezone == "Europe/Helsinki"
    )


def test_parse_brief_timezone_none_when_line_absent() -> None:
    # C4.3 — every brief written before feature 017 has no such line and must still parse.
    assert parse_brief(VALID_BRIEF).routine_timezone is None


def test_parse_brief_timezone_none_for_placeholder_or_blank() -> None:
    # C1.7 / FR-005 — an unfilled template line is indistinguishable from an absent one.
    assert parse_brief(_brief_with_timezone("[e.g., Europe/Helsinki]")).routine_timezone is None
    assert parse_brief(_brief_with_timezone("")).routine_timezone is None


def test_parse_brief_rejects_an_unknown_timezone_naming_the_value() -> None:
    # C1.5 / SC-004 — no silent fallback: a typo must stop the run, not move the company 3 hours.
    for bad in ("Europe/Helsinky", "+03:00"):
        with pytest.raises(BriefValidationError) as excinfo:
            parse_brief(_brief_with_timezone(bad))
        assert bad in str(excinfo.value)


def test_parse_brief_accepts_a_non_region_city_database_zone() -> None:
    # C1.6 — the recognition set is the zone database, not a curated Region/City subset.
    assert parse_brief(_brief_with_timezone("EET")).routine_timezone == "EET"


def test_timezone_line_does_not_disturb_other_section_9_values() -> None:
    # C4.2 / FR-012 — _inline_value matches on substring across the section's lines, so a new
    # line in section 9 is exactly the place an existing binding could be silently stolen.
    brief = parse_brief(_brief_with_timezone("Europe/Helsinki"))
    assert brief.hours_per_week == 6
    assert brief.capital_monthly_eur == 150
    assert brief.capital_setup_eur == 400


_RUN_POLICY_SECTION = """

## 12. Run-policy overrides (optional)

**Your overrides:**

- engineer: max turns 8, heartbeat off
- ceo: max concurrent 1
"""


def test_parse_brief_reads_run_policy_section() -> None:
    brief = parse_brief(VALID_BRIEF + _RUN_POLICY_SECTION)
    assert brief.run_policy_preferences == [
        "engineer: max turns 8, heartbeat off",
        "ceo: max concurrent 1",
    ]


def test_parse_brief_run_policy_none_when_section_absent() -> None:
    # An otherwise-unchanged brief with no run-policy section yields None.
    assert parse_brief(VALID_BRIEF).run_policy_preferences is None


def test_run_policy_preferences_none_by_default() -> None:
    assert CompanyBrief(**_brief_kwargs()).run_policy_preferences is None


@pytest.mark.parametrize(
    "line",
    [
        "ceo: max turns 0",
        "ceo: max turns abc",
        "ceo: max concurrent -1",
        "ceo: heartbeat maybe",
        "ceo: frobnicate 5",
        "ceo:",  # no clause
        "no colon here",
    ],
)
def test_malformed_run_policy_value_rejected(line: str) -> None:
    with pytest.raises(ValidationError):
        CompanyBrief(**_brief_kwargs(run_policy_preferences=[line]))


def test_same_reference_conflicting_values_rejected() -> None:
    with pytest.raises(ValidationError):
        CompanyBrief(
            **_brief_kwargs(run_policy_preferences=["ceo: max turns 8", "ceo: max turns 5"])
        )


def test_malformed_run_policy_via_parse_brief_raises_brief_error() -> None:
    bad_section = (
        "\n\n## 12. Run-policy overrides (optional)\n\n**Your overrides:**\n\n- ceo: max turns 0\n"
    )
    with pytest.raises(BriefValidationError):
        parse_brief(VALID_BRIEF + bad_section)


def test_valid_run_policy_preferences_accepted() -> None:
    brief = CompanyBrief(
        **_brief_kwargs(run_policy_preferences=["engineer: max turns 8", "ceo: heartbeat off"])
    )
    assert brief.run_policy_preferences == ["engineer: max turns 8", "ceo: heartbeat off"]


# --- US1 models: agent, skill, output (T017) --------------------------------


def _soul_kwargs(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "identity": "I am the CEO of the studio.",
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
        "name": "CEO",
        "title": "CEO",
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
        mode="single",
        brief=CompanyBrief(**_brief_kwargs()),
        company=company,
        agents=[AgentDefinition(**_agent_kwargs())],
        skills=[skill],
    )
    assert config.agents[0].slug == "ceo"


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
    # The LLM must not emit a task-shaped goal (single-session work).
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


# --- v0.1b foundational models (T003) ---------------------------------------


def _stub(slug: str, reports_to: str | None, skills: list[str] | None = None) -> AgentStub:
    return AgentStub(
        slug=slug,
        name=slug.title(),
        title=slug.title(),
        reports_to=reports_to,
        skills=skills or [f"{slug}-skill"],
    )


def _valid_org() -> OrgPlan:
    return OrgPlan(
        agents=[
            _stub("ceo", None, ["pricing-strategy"]),
            _stub("cto", "ceo", ["architecture"]),
            _stub("engineer", "cto", ["coding"]),
        ],
        projects=[ProjectStub(slug="launch-v1", name="Launch v1", owner="cto")],
        tasks=[
            TaskStub(slug="ship-mvp", name="Ship the MVP", project="launch-v1", assignee="engineer")
        ],
    )


def test_orgplan_valid_constructs() -> None:
    org = _valid_org()
    assert {a.slug for a in org.agents} == {"ceo", "cto", "engineer"}
    assert org.skill_slugs == ["pricing-strategy", "architecture", "coding"]


def test_orgplan_requires_exactly_one_root() -> None:
    with pytest.raises(ValidationError, match="exactly one root"):
        OrgPlan(agents=[_stub("ceo", None), _stub("coo", None)])


def test_orgplan_rejects_unknown_manager() -> None:
    with pytest.raises(ValidationError, match="unknown manager"):
        OrgPlan(agents=[_stub("ceo", None), _stub("eng", "ghost")])


def test_orgplan_rejects_cycle() -> None:
    with pytest.raises(ValidationError, match="cycle"):
        OrgPlan(agents=[_stub("a", "b"), _stub("b", "a"), _stub("root", None)])


def test_orgplan_enforces_span_of_control() -> None:
    reports = [_stub(f"r{i}", "ceo") for i in range(8)]
    with pytest.raises(ValidationError, match="span-of-control"):
        OrgPlan(agents=[_stub("ceo", None), *reports])


def test_orgplan_allows_seven_reports() -> None:
    reports = [_stub(f"r{i}", "ceo") for i in range(7)]
    org = OrgPlan(agents=[_stub("ceo", None), *reports])
    assert len(org.agents) == 8


def test_orgplan_rejects_dangling_task_refs() -> None:
    with pytest.raises(ValidationError, match="unknown project"):
        OrgPlan(
            agents=[_stub("ceo", None)],
            tasks=[TaskStub(slug="t", name="T", project="ghost", assignee="ceo")],
        )
    with pytest.raises(ValidationError, match="unknown agent"):
        OrgPlan(
            agents=[_stub("ceo", None)],
            projects=[ProjectStub(slug="p", name="P", owner="ceo")],
            tasks=[TaskStub(slug="t", name="T", project="p", assignee="ghost")],
        )


def test_orgplan_rejects_duplicate_slugs() -> None:
    with pytest.raises(ValidationError, match="duplicate agent"):
        OrgPlan(agents=[_stub("ceo", None), _stub("ceo", "ceo")])


def test_project_and_task_definitions_construct() -> None:
    p = ProjectDefinition(
        slug="launch-v1",
        name="Launch v1",
        owner="cto",
        summary="Ship it.",
        success_condition="Live.",
    )
    t = TaskDefinition(
        slug="ship-mvp",
        name="Ship the MVP",
        project="launch-v1",
        assignee="engineer",
        objective="Cut the first build.",
        completion_criteria=["Build uploads", "Smoke pass green"],
    )
    assert p.owner == "cto"
    assert t.project == "launch-v1"


def test_task_requires_completion_criterion() -> None:
    with pytest.raises(ValidationError):
        TaskDefinition(
            slug="t", name="T", project="p", assignee="a", objective="x", completion_criteria=[]
        )


def _operations() -> OperationsDefinition:
    return OperationsDefinition(
        phase_model="Phase 1 then 2.",
        idle_state_protocol="Idle is a success state.",
        reporting_cadence="Weekly.",
        comm_conventions="Async first.",
        approval_merge_rules=(
            "The human Board is the sole approver of board-gated decisions. Agents mark "
            "such work ready for Board review and escalate; no agent self-approves."
        ),
        delegation_checklist=["Is the goal an outcome?"],
        # Must reproduce every constraint + "we are not" from _company_kwargs (P-PAT-10).
        anti_drift_checks=[
            "We are NOT a free-to-play studio.",
            "We are NOT a multi-title shop.",
            "One title at a time.",
            "No dark patterns.",
        ],
        duplicate_prevention="Check the inventory first.",
        routine_slots=["ceo: weekly review"],
        critical_rules=["Never ship without sign-off."],
    )


def _full_config_kwargs(**overrides: Any) -> dict[str, Any]:
    ceo = AgentDefinition(**_agent_kwargs())
    cto = AgentDefinition(
        **_agent_kwargs(
            slug="cto", name="CTO", title="CTO", reports_to="ceo", skills=["architecture"]
        )
    )
    skills = [
        SkillDefinition(**_skill_kwargs()),
        SkillDefinition(**_skill_kwargs(slug="architecture", name="architecture")),
    ]
    base: dict[str, Any] = {
        "mode": "full",
        "brief": CompanyBrief(**_brief_kwargs()),
        "company": CompanyDefinition(**_company_kwargs()),
        "agents": [ceo, cto],
        "skills": skills,
        "projects": [
            ProjectDefinition(
                slug="launch-v1", name="Launch v1", owner="cto", summary="s", success_condition="c"
            )
        ],
        "tasks": [
            TaskDefinition(
                slug="ship",
                name="Ship",
                project="launch-v1",
                assignee="cto",
                objective="o",
                completion_criteria=["done"],
            )
        ],
        "operations": _operations(),
    }
    base.update(overrides)
    return base


def _skill_kwargs(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "slug": "release-checklist",
        "name": "release-checklist",
        "description": "Pre-submission checklist.",
        "when_to_load": ["RC ready."],
        "inputs": ["build"],
        "procedure": ["check"],
        "outputs": ["signed build"],
        "anti_patterns": ["skip smoke"],
    }
    base.update(overrides)
    return base


def test_company_config_full_constructs() -> None:
    config = CompanyConfig(**_full_config_kwargs())
    assert config.mode == "full"
    assert len(config.agents) == 2
    assert config.operations is not None


def test_company_config_full_requires_operations() -> None:
    with pytest.raises(ValidationError, match="must have operations"):
        CompanyConfig(**_full_config_kwargs(operations=None))


def test_company_config_full_requires_single_root() -> None:
    ceo = AgentDefinition(**_agent_kwargs())
    coo = AgentDefinition(**_agent_kwargs(slug="coo", name="COO", title="COO", reports_to=None))
    with pytest.raises(ValidationError, match="exactly one root"):
        CompanyConfig(**_full_config_kwargs(agents=[ceo, coo]))


def test_company_config_full_rejects_unresolved_skill() -> None:
    cto = AgentDefinition(
        **_agent_kwargs(
            slug="cto", name="CTO", title="CTO", reports_to="ceo", skills=["ghost-skill"]
        )
    )
    ceo = AgentDefinition(**_agent_kwargs())
    with pytest.raises(ValidationError, match="no SKILL.md"):
        CompanyConfig(**_full_config_kwargs(agents=[ceo, cto]))


def test_company_config_single_rejects_projects() -> None:
    with pytest.raises(ValidationError, match="no projects or tasks"):
        CompanyConfig(
            mode="single",
            brief=CompanyBrief(**_brief_kwargs()),
            company=CompanyDefinition(**_company_kwargs()),
            agents=[AgentDefinition(**_agent_kwargs())],
            skills=[SkillDefinition(**_skill_kwargs())],
            projects=[
                ProjectDefinition(
                    slug="p", name="P", owner="ceo", summary="s", success_condition="c"
                )
            ],
        )


def test_skill_procedure_strips_a_step_s_own_ordinal_prefix() -> None:
    """The template numbers the list; a step numbering itself yields "1. 1. STEP".

    Normalised on the model so it holds for every consumer and does not depend on the
    prompt being obeyed.
    """
    from paperclip_blueprints.models.skill import SkillDefinition

    skill = SkillDefinition(
        slug="s",
        name="s",
        description="d",
        when_to_load=["w"],
        inputs=["i"],
        procedure=["1. INTAKE AND DOMAIN GATE", "2) Assign the evidence tier", "(3) Publish"],
        outputs=["o"],
        anti_patterns=["a"],
    )
    assert skill.procedure == ["INTAKE AND DOMAIN GATE", "Assign the evidence tier", "Publish"]


def test_skill_procedure_keeps_prose_that_legitimately_opens_with_a_number() -> None:
    """Stripping requires the ordinal separator, so a real quantity survives."""
    from paperclip_blueprints.models.skill import SkillDefinition

    skill = SkillDefinition(
        slug="s",
        name="s",
        description="d",
        when_to_load=["w"],
        inputs=["i"],
        procedure=["2 business days must pass before the entry is promoted"],
        outputs=["o"],
        anti_patterns=["a"],
    )
    assert skill.procedure == ["2 business days must pass before the entry is promoted"]


# --- feature 020: the exception hierarchy (C5.4) -----------------------------


def test_structural_and_field_failures_are_distinct_types_sharing_a_base() -> None:
    """C5.4 — a caller that does not care catches one thing; a caller that does separates.

    The distinction is in the type rather than in a flag, so a consumer reads it from the
    shape instead of parsing a field. The machine-readable documents carry the class as a
    declared vocabulary value regardless — an exception name is never the wire contract.
    """
    from paperclip_blueprints.models.input import (
        BriefError,
        BriefStructureError,
        BriefValidationError,
    )

    assert issubclass(BriefStructureError, BriefError)
    assert issubclass(BriefValidationError, BriefError)
    assert not issubclass(BriefStructureError, BriefValidationError)
    assert not issubclass(BriefValidationError, BriefStructureError)


def test_catching_the_base_catches_both_failure_kinds() -> None:
    """C5.4 — the arrangement exists so `except BriefError` is sufficient."""
    from paperclip_blueprints.models.brief_sections import StructuralFinding
    from paperclip_blueprints.models.input import (
        BriefError,
        BriefStructureError,
        BriefValidationError,
    )

    with pytest.raises(BriefError):
        raise BriefStructureError([StructuralFinding(kind="duplicate_ordinal", ordinal=9)])
    with pytest.raises(BriefError):
        raise BriefValidationError(["something"])


def test_the_existing_field_error_keeps_its_messages_and_rendering() -> None:
    """Introducing a base must not change what an existing caller sees.

    `cli._load_brief` prints `str(exc)` and the parity baselines record `exc.messages`, so
    both are behaviour, not implementation.
    """
    exc = BriefValidationError(["name: Field required", "slug: Field required"])
    assert exc.messages == ["name: Field required", "slug: Field required"]
    assert str(exc) == "  - name: Field required\n  - slug: Field required"


# --- feature 020: structure gates fields (C5.1-C5.3) -------------------------


def _renumbered_brief() -> str:
    """The motivating case: one inserted section renumbers everything below it."""
    return VALID_BRIEF.replace(
        "## 10. Adapter preferences (optional)",
        "## 10. Notes to self\n\nAnything.\n\n## 11. Adapter preferences (optional)",
    ).replace("## 11. Anything else", "## 12. Anything else")


def test_a_renumbered_brief_is_rejected_rather_than_losing_its_canon() -> None:
    """C5.1 — the failure this feature exists to convert into an error.

    Before this gate the same document parsed clean: section 11's anchor was not found,
    `free_text` fell out of the payload, and nothing downstream knew the operating canon
    had been stated.
    """
    from paperclip_blueprints.models.input import BriefStructureError

    with pytest.raises(BriefStructureError) as excinfo:
        parse_brief(_renumbered_brief())

    joined = "\n".join(excinfo.value.messages)
    assert "section 11" in joined
    assert "Operating canon" in joined


def test_a_structural_failure_reports_no_field_messages() -> None:
    """C5.1 — field errors from a misaligned brief are artifacts of parsing the wrong text.

    The renumbered brief below also has an unparseable governance position, because
    section 8's content now sits under a different number. That is a consequence, not a
    finding, and reporting it would present a guess as a result.
    """
    from paperclip_blueprints.models.input import BriefStructureError

    with pytest.raises(BriefStructureError) as excinfo:
        parse_brief(_renumbered_brief())

    assert not any("Field required" in m for m in excinfo.value.messages)
    assert not any("governance_position" in m for m in excinfo.value.messages)


def test_a_structural_failure_states_that_fields_were_not_checked() -> None:
    """C5.2 — an operator who fixes the structure and then meets field errors must not
    conclude the fix caused them."""
    from paperclip_blueprints.models.input import BriefStructureError

    with pytest.raises(BriefStructureError) as excinfo:
        parse_brief(_renumbered_brief())

    assert excinfo.value.fields_checked is False
    assert any("not attempted" in m for m in excinfo.value.messages)


def test_structural_failures_aggregate_in_one_run() -> None:
    """C5.3 — every misaligned section, not the first."""
    from paperclip_blueprints.models.input import BriefStructureError

    with pytest.raises(BriefStructureError) as excinfo:
        parse_brief(_renumbered_brief())

    ordinals = {f.ordinal for f in excinfo.value.findings}
    assert ordinals == {10, 11, 12}


def test_a_structurally_sound_brief_still_reports_its_field_errors() -> None:
    """The gate must not swallow the failures it defers to."""
    broken = VALID_BRIEF.replace("**Slug:** indie-game-studio", "**Slug:** Not A Slug")
    with pytest.raises(BriefValidationError) as excinfo:
        parse_brief(broken)
    assert any("slug" in m for m in excinfo.value.messages)


def test_field_validation_records_that_it_was_attempted() -> None:
    """The counterpart to C5.2 — the flag distinguishes the two states, not the message."""
    broken = VALID_BRIEF.replace("**Slug:** indie-game-studio", "**Slug:** Not A Slug")
    with pytest.raises(BriefValidationError) as excinfo:
        parse_brief(broken)
    assert excinfo.value.fields_checked is True
