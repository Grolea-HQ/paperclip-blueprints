"""Tests for the generator layer.

T006: the Anthropic client seam (prompt loading, fenced-block extraction,
injectable transport, malformed-response handling). No live API calls.
"""

import pytest

from paperclip_blueprints.generators.agents import generate_agent
from paperclip_blueprints.generators.client import (
    GenerationError,
    LLMClient,
    extract_fenced_block,
    load_prompt,
)
from paperclip_blueprints.generators.identity import generate_identity
from paperclip_blueprints.generators.org import AgentStub, generate_org
from paperclip_blueprints.generators.skills import generate_skill
from paperclip_blueprints.generators.souls import generate_soul
from paperclip_blueprints.models.agent import AgentDefinition, AgentSoul
from paperclip_blueprints.models.company import CompanyDefinition
from paperclip_blueprints.models.input import CompanyBrief
from paperclip_blueprints.models.skill import SkillDefinition

# --- fenced block extraction ------------------------------------------------


def test_extract_json_block() -> None:
    text = 'Here you go:\n```json\n{"a": 1}\n```\nthanks'
    assert extract_fenced_block(text, lang="json") == '{"a": 1}'


def test_extract_generic_block() -> None:
    text = "```\nhello\nworld\n```"
    assert extract_fenced_block(text) == "hello\nworld"


def test_extract_block_missing_raises() -> None:
    with pytest.raises(GenerationError):
        extract_fenced_block("no fences here", lang="json")


# --- client transport seam --------------------------------------------------


def test_client_uses_injected_transport() -> None:
    calls: list[dict] = []

    def fake_invoke(**kwargs: object) -> str:
        calls.append(kwargs)
        return "canned response"

    client = LLMClient(_invoke=fake_invoke)
    out = client.complete(model="claude-opus-4-7", system="sys", user="usr")
    assert out == "canned response"
    assert calls[0]["model"] == "claude-opus-4-7"


def test_client_does_not_construct_sdk_when_transport_injected() -> None:
    # Injecting a transport must not require an API key or touch the SDK.
    client = LLMClient(_invoke=lambda **_: "ok")
    assert client.complete(model="m", system="s", user="u") == "ok"


# --- prompt loading ---------------------------------------------------------


def test_load_prompt_unknown_raises() -> None:
    with pytest.raises(GenerationError):
        load_prompt("definitely_not_a_real_prompt")


# --- identity generator (T008) ----------------------------------------------

_IDENTITY_JSON = """\
Sure, here is the identity content:
```json
{
  "name": "Indie Game Studio",
  "description": "A solo-founder premium mobile puzzle studio.",
  "goals": ["4.6+ rating sustained", "refund rate below 3% per quarter"],
  "we_are": "We are a single-title premium mobile studio.",
  "we_are_not": ["We are NOT a free-to-play studio.", "We are NOT a multi-title shop."],
  "north_star": "$30,000 monthly net revenue within 12 months.",
  "constraints": ["One title at a time.", "No dark patterns."],
  "tone": "purple",
  "mono": "N",
  "version": "1.0.0",
  "tags": []
}
```
"""


def _brief() -> CompanyBrief:
    return CompanyBrief(
        name="Indie Game Studio",
        slug="indie-game-studio",
        description="A solo-founder premium mobile puzzle studio shipping one game a year.",
        north_star="$30,000 monthly net revenue within 12 months.",
        goals=["4.6+ App Store rating sustained", "refund rate below 3% per quarter"],
        we_are="We are a single-title premium mobile studio.",
        we_are_not=["We are NOT a free-to-play studio.", "We are NOT a multi-title shop."],
        constraints=["One title at a time.", "No dark patterns."],
        governance_position="balanced",
    )


def test_generate_identity_parses_response() -> None:
    client = LLMClient(_invoke=lambda **_: _IDENTITY_JSON)
    company = generate_identity(_brief(), client)
    assert isinstance(company, CompanyDefinition)
    assert company.tone == "purple"
    assert len(company.we_are_not) == 2
    assert len(company.constraints) == 2


def test_generate_identity_malformed_raises() -> None:
    client = LLMClient(_invoke=lambda **_: "no json here at all")
    with pytest.raises(GenerationError):
        generate_identity(_brief(), client)


def test_generate_identity_uses_thinking_and_content_model() -> None:
    seen: dict[str, object] = {}

    def fake(**kwargs: object) -> str:
        seen.update(kwargs)
        return _IDENTITY_JSON

    generate_identity(_brief(), LLMClient(_invoke=fake))
    assert seen["thinking"] is True
    assert seen["effort"] == "high"
    assert seen["model"] == "claude-opus-4-7"


# --- org / agents / souls / skills generators (T018) ------------------------


def _company() -> CompanyDefinition:
    return generate_identity(_brief(), LLMClient(_invoke=lambda **_: _IDENTITY_JSON))


_ORG_JSON = """\
```json
{"agents": [{"slug": "ceo", "name": "Founder / CEO", "title": "Founder / CEO",
 "reports_to": null, "skills": ["release-checklist"]}], "projects": [], "tasks": []}
```
"""

_SOUL_JSON = """\
```json
{
  "identity": "I am the Founder/CEO.",
  "what_we_are": "We are a single-title premium studio.",
  "product_reality": "The product is one polished game.",
  "beliefs": ["Focus is the moat.", "Idle is a success state; I wait between cycles."],
  "how_i_act": ["I decide quickly on scope."],
  "what_i_dont_do": ["I do not ship dark patterns."],
  "my_north_star": "$30,000 MRR within 12 months."
}
```
"""

_AGENT_BODY_JSON = """\
```json
{
  "mandate": "Owns the north star and ships the title.",
  "triggers": ["A release candidate is ready."],
  "receives_from": [],
  "hands_to": [],
  "deliverables": ["Approved release builds."],
  "can_approve": ["Store metadata within the plan."],
  "must_escalate": ["Pricing changes."],
  "escalation_text": "Escalate to the operator on pricing.",
  "tools_role_specific": "Reviews build status in App Store Connect."
}
```
"""

_SKILL_JSON = """\
```json
{
  "slug": "release-checklist",
  "name": "release-checklist",
  "description": "Pre-submission checklist for a store release.",
  "when_to_load": ["A build is a release candidate."],
  "inputs": ["The candidate build."],
  "procedure": ["Verify build number.", "Run smoke pass."],
  "outputs": ["A signed-off build."],
  "anti_patterns": ["Shipping without the smoke pass."],
  "references": []
}
```
"""


def test_org_planner_returns_single_owner() -> None:
    stub = generate_org(_brief(), _company(), LLMClient(_invoke=lambda **_: _ORG_JSON))
    assert isinstance(stub, AgentStub)
    assert stub.reports_to is None
    assert stub.skills == ["release-checklist"]


def test_soul_generator_builds_soul_with_idle_belief() -> None:
    stub = AgentStub(
        slug="ceo",
        name="Founder / CEO",
        title="Founder / CEO",
        reports_to=None,
        skills=["release-checklist"],
    )
    soul = generate_soul(stub, _company(), LLMClient(_invoke=lambda **_: _SOUL_JSON))
    assert isinstance(soul, AgentSoul)
    assert any("idle" in b.lower() for b in soul.beliefs)


def test_soul_generator_uses_thinking_and_high_effort() -> None:
    seen: dict[str, object] = {}

    def fake(**kwargs: object) -> str:
        seen.update(kwargs)
        return _SOUL_JSON

    stub = AgentStub(
        slug="ceo",
        name="Founder / CEO",
        title="Founder / CEO",
        reports_to=None,
        skills=["release-checklist"],
    )
    generate_soul(stub, _company(), LLMClient(_invoke=fake))
    assert seen["thinking"] is True
    assert seen["effort"] == "high"
    assert seen["model"] == "claude-opus-4-7"


def test_structural_calls_send_no_thinking_or_effort() -> None:
    """Guard: cheap-tier structural calls must not enable adaptive thinking.

    org/agents/skills run on the Sonnet structural model. Accidentally turning
    on thinking (and thus output_config effort) there would silently raise cost
    on every wakeup. This locks the contract: thinking off, effort unset.
    """
    company = _company()
    soul = AgentSoul(
        identity="I am the CEO.",
        what_we_are="We are a studio.",
        product_reality="One game.",
        beliefs=["Idle is a success state."],
        how_i_act=["I ship."],
        what_i_dont_do=["No dark patterns."],
        my_north_star="$30k MRR.",
    )
    stub = AgentStub(
        slug="ceo",
        name="Founder / CEO",
        title="Founder / CEO",
        reports_to=None,
        skills=["release-checklist"],
    )

    for label, run, payload in (
        ("org", lambda c: generate_org(_brief(), company, c), _ORG_JSON),
        ("agents", lambda c: generate_agent(stub, company, _brief(), soul, c), _AGENT_BODY_JSON),
        ("skills", lambda c: generate_skill("release-checklist", company, ["ceo"], c), _SKILL_JSON),
    ):
        seen: dict[str, object] = {}

        def fake(captured: dict[str, object] = seen, body: str = payload, **kwargs: object) -> str:
            captured.update(kwargs)
            return body

        run(LLMClient(_invoke=fake))
        assert seen.get("thinking") is False, f"{label} must not enable thinking"
        assert seen.get("effort") is None, f"{label} must not set effort"
        assert seen["model"] == "claude-sonnet-4-6", f"{label} must use the structural model"


def test_soul_generator_rejects_missing_idle_belief() -> None:
    bad = _SOUL_JSON.replace("Idle is a success state; I wait between cycles.", "Ship often.")
    stub = AgentStub(
        slug="ceo",
        name="Founder / CEO",
        title="Founder / CEO",
        reports_to=None,
        skills=["release-checklist"],
    )
    with pytest.raises(GenerationError):
        generate_soul(stub, _company(), LLMClient(_invoke=lambda **_: bad))


def test_agents_generator_builds_agent_from_stub_and_soul() -> None:
    stub = AgentStub(
        slug="ceo",
        name="Founder / CEO",
        title="Founder / CEO",
        reports_to=None,
        skills=["release-checklist"],
    )
    soul = AgentSoul(
        identity="I am the CEO.",
        what_we_are="We are a studio.",
        product_reality="One game.",
        beliefs=["Idle is a success state."],
        how_i_act=["I ship."],
        what_i_dont_do=["No dark patterns."],
        my_north_star="$30k MRR.",
    )
    agent = generate_agent(
        stub,
        _company(),
        _brief(),
        soul,
        LLMClient(_invoke=lambda **_: _AGENT_BODY_JSON),
    )
    assert isinstance(agent, AgentDefinition)
    assert agent.slug == "ceo"
    assert agent.reports_to is None
    assert agent.receives_from == []
    assert agent.soul is soul


def test_agents_generator_passes_governance_into_prompt() -> None:
    seen: dict[str, object] = {}
    stub = AgentStub(
        slug="ceo",
        name="Founder / CEO",
        title="Founder / CEO",
        reports_to=None,
        skills=["release-checklist"],
    )
    soul = AgentSoul(
        identity="I am the CEO.",
        what_we_are="Studio.",
        product_reality="Game.",
        beliefs=["Idle is a success state."],
        how_i_act=["Ship."],
        what_i_dont_do=["No dark patterns."],
        my_north_star="$30k.",
    )

    def fake(**kwargs: object) -> str:
        seen.update(kwargs)
        return _AGENT_BODY_JSON

    generate_agent(stub, _company(), _brief(), soul, LLMClient(_invoke=fake))
    # the governance position from the brief must reach the prompt text
    assert "balanced" in str(seen["user"])


def test_skill_generator_builds_skill() -> None:
    skill = generate_skill(
        "release-checklist",
        _company(),
        ["Founder / CEO"],
        LLMClient(_invoke=lambda **_: _SKILL_JSON),
    )
    assert isinstance(skill, SkillDefinition)
    assert skill.slug == "release-checklist"


# --- US1 full-bundle generators (T012) --------------------------------------

_ORG_FULL_JSON = """\
```json
{"agents": [
  {"slug": "ceo", "name": "CEO", "title": "CEO", "reports_to": null, "skills": ["strategy"]},
  {"slug": "eng", "name": "Engineer", "title": "Engineer",
   "reports_to": "ceo", "skills": ["coding"]}
 ],
 "projects": [{"slug": "launch", "name": "Launch", "owner": "eng"}],
 "tasks": [{"slug": "ship", "name": "Ship", "project": "launch", "assignee": "eng"}]}
```
"""

_OPERATIONS_JSON = """\
```json
{"phase_model": "Build then polish.", "idle_state_protocol": "Idle is a success state.",
 "reporting_cadence": "Weekly.", "comm_conventions": "Async.",
 "approval_merge_rules": "Board approves strategy.", "delegation_checklist": ["outcome?"],
 "anti_drift_checks": ["We are NOT a free-to-play studio."],
 "duplicate_prevention": "Check inventory.",
 "routine_slots": ["ceo: weekly review"], "critical_rules": ["Sign-off before ship."]}
```
"""


def test_generate_org_plan_full_multi_agent() -> None:
    from paperclip_blueprints.generators.org import generate_org_plan
    from paperclip_blueprints.models.org_plan import OrgPlan

    plan = generate_org_plan(_brief(), _company(), LLMClient(_invoke=lambda **_: _ORG_FULL_JSON))
    assert isinstance(plan, OrgPlan)
    assert {a.slug for a in plan.agents} == {"ceo", "eng"}
    assert plan.skill_slugs == ["strategy", "coding"]
    assert len(plan.projects) == 1 and len(plan.tasks) == 1


# --- US1: project slug normalization on the org plan (ADR-013) ---------------

_ORG_SLUG_MISMATCH_JSON = """\
```json
{"agents": [
  {"slug": "ceo", "name": "CEO", "title": "CEO", "reports_to": null, "skills": ["strategy"]},
  {"slug": "eng", "name": "Engineer", "title": "Engineer",
   "reports_to": "ceo", "skills": ["coding"]}
 ],
 "projects": [{"slug": "seo-foundation",
   "name": "SEO Content Foundation — First Keyword Cluster", "owner": "eng"}],
 "tasks": [{"slug": "kw1", "name": "First cluster", "project": "seo-foundation",
   "assignee": "eng"}]}
```
"""

_ORG_SLUG_COLLISION_JSON = """\
```json
{"agents": [
  {"slug": "ceo", "name": "CEO", "title": "CEO", "reports_to": null, "skills": ["strategy"]},
  {"slug": "eng", "name": "Engineer", "title": "Engineer",
   "reports_to": "ceo", "skills": ["coding"]}
 ],
 "projects": [
   {"slug": "launch-a", "name": "Launch", "owner": "eng"},
   {"slug": "launch-b", "name": "Launch!", "owner": "eng"}
 ],
 "tasks": [
   {"slug": "t1", "name": "T1", "project": "launch-a", "assignee": "eng"},
   {"slug": "t2", "name": "T2", "project": "launch-b", "assignee": "eng"}
 ]}
```
"""


def test_org_plan_normalizes_project_slug_to_slugify_name() -> None:
    from paperclip_blueprints.generators.org import generate_org_plan

    plan = generate_org_plan(
        _brief(), _company(), LLMClient(_invoke=lambda **_: _ORG_SLUG_MISMATCH_JSON)
    )
    (project,) = plan.projects
    assert project.slug == "seo-content-foundation-first-keyword-cluster"
    # the task's project ref was rewritten from "seo-foundation" to the new slug
    assert plan.tasks[0].project == project.slug


def test_org_plan_dedupes_colliding_project_slugs() -> None:
    from paperclip_blueprints.generators.org import generate_org_plan

    plan = generate_org_plan(
        _brief(), _company(), LLMClient(_invoke=lambda **_: _ORG_SLUG_COLLISION_JSON)
    )
    slugs = [p.slug for p in plan.projects]
    assert slugs == ["launch", "launch-2"]
    # each task follows its project to the de-duplicated slug
    assert {t.project for t in plan.tasks} == {"launch", "launch-2"}


def test_generate_operations_parses_and_uses_thinking() -> None:
    from paperclip_blueprints.generators.operations import generate_operations
    from paperclip_blueprints.models.operations import OperationsDefinition
    from paperclip_blueprints.models.org_plan import AgentStub

    seen: dict[str, object] = {}

    def fake(**kwargs: object) -> str:
        seen.update(kwargs)
        return _OPERATIONS_JSON

    stub = AgentStub(slug="ceo", name="CEO", title="CEO", reports_to=None, skills=["strategy"])
    ops = generate_operations(_company(), _brief(), [stub], LLMClient(_invoke=fake))
    assert isinstance(ops, OperationsDefinition)
    assert ops.anti_drift_checks
    assert seen["thinking"] is True  # operations is a content-synthesis Opus call


def test_generate_project_and_task() -> None:
    from paperclip_blueprints.generators.projects import generate_project
    from paperclip_blueprints.generators.tasks import generate_task
    from paperclip_blueprints.models.org_plan import ProjectStub, TaskStub

    proj = generate_project(
        ProjectStub(slug="launch", name="Launch", owner="eng"),
        _company(),
        LLMClient(_invoke=lambda **_: '```json\n{"summary": "s", "success_condition": "c"}\n```'),
    )
    assert proj.owner == "eng" and proj.success_condition == "c"

    task = generate_task(
        TaskStub(slug="ship", name="Ship", project="launch", assignee="eng"),
        _company(),
        LLMClient(
            _invoke=lambda **_: '```json\n{"objective": "o", "completion_criteria": ["done"]}\n```'
        ),
    )
    assert task.project == "launch" and task.completion_criteria == ["done"]


# --- US4 cost tracking (T051) -----------------------------------------------


def test_client_tallies_usage_from_usage_reporting_transport() -> None:
    def fake(**kwargs: object) -> tuple[str, tuple[int, int]]:
        return ("text", (10, 20))

    client = LLMClient(_invoke=fake)
    client.complete(model="claude-opus-4-7", system="s", user="u")
    client.complete(model="claude-sonnet-4-6", system="s", user="u")
    summary = client.usage_summary()
    assert summary["total"]["calls"] == 2
    assert summary["total"]["input_tokens"] == 20
    assert summary["total"]["output_tokens"] == 40
    assert summary["total"]["cost_usd"] > 0
    assert set(summary["by_model"]) == {"claude-opus-4-7", "claude-sonnet-4-6"}


def test_client_plain_text_transport_records_no_usage() -> None:
    client = LLMClient(_invoke=lambda **_: "text")
    client.complete(model="m", system="s", user="u")
    assert client.usage_summary()["total"]["calls"] == 0


def test_estimate_cost_uses_price_table() -> None:
    from paperclip_blueprints.config import estimate_cost

    # Opus list price: $5/Mtok in, $25/Mtok out → 1M+1M = $30.
    assert estimate_cost("claude-opus-4-7", 1_000_000, 1_000_000) == pytest.approx(30.0)
    # An unknown model falls back to the Sonnet price ($3 + $15 = $18).
    assert estimate_cost("mystery-model", 1_000_000, 1_000_000) == pytest.approx(18.0)


def test_estimate_cost_reconciles_with_real_billing() -> None:
    """Anchor the calculator to a real run so a stale rate can't drift silently.

    Token counts captured from real tenkay run 2026-06-01 (13 Opus calls,
    37 Sonnet calls). Actual Anthropic billing for that run was ~$1.50; the
    encoded rates must reproduce it within ±5%.
    """
    from paperclip_blueprints.config import estimate_cost

    opus = estimate_cost("claude-opus-4-7", 27854, 25703)
    sonnet = estimate_cost("claude-sonnet-4-6", 37542, 42884)
    total = opus + sonnet
    assert total == pytest.approx(1.54, rel=0.05)
