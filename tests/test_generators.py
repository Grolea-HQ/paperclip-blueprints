"""Tests for the generator layer.

T006: the Anthropic client seam (prompt loading, fenced-block extraction,
injectable transport, malformed-response handling). No live API calls.
"""

import json
from collections.abc import Callable

import pytest

from paperclip_blueprints.generators.agents import generate_agent
from paperclip_blueprints.generators.client import (
    APIRequestError,
    GenerationError,
    LLMClient,
    extract_fenced_block,
    load_prompt,
)
from paperclip_blueprints.generators.identity import generate_identity
from paperclip_blueprints.generators.org import AgentStub, generate_org, generate_org_plan
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
    out = client.complete(model="claude-opus-4-8", system="sys", user="usr")
    assert out == "canned response"
    assert calls[0]["model"] == "claude-opus-4-8"


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
    assert seen["model"] == "claude-opus-4-8"


# --- org / agents / souls / skills generators (T018) ------------------------


def _company() -> CompanyDefinition:
    return generate_identity(_brief(), LLMClient(_invoke=lambda **_: _IDENTITY_JSON))


_ORG_JSON = """\
```json
{"agents": [{"slug": "ceo", "name": "CEO", "title": "CEO",
 "reports_to": null, "skills": ["release-checklist"]}], "projects": [], "tasks": []}
```
"""

_SOUL_JSON = """\
```json
{
  "identity": "I am the CEO.",
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


def test_unrepresentable_cadence_is_rejected_at_the_plan_step(monkeypatch) -> None:
    """An unrepresentable cadence must fail at org planning, not during render.

    Feature 018 replaced the silent weekly-Monday fallback with a raise (FR-007). *Where* that
    raise lands decides what it costs: at the plan step it costs identity + org — two model
    calls — while at render time it would cost the full per-agent fan-out on a brief that looked
    valid. This pins it to the cheap point, because "generation fails late" is discovered by
    whoever runs it, not by the suite.
    """
    bad_plan = json.dumps(
        {
            "agents": [
                {
                    "slug": "ceo",
                    "name": "CEO",
                    "title": "CEO",
                    "reports_to": None,
                    "skills": ["release-checklist"],
                }
            ],
            "projects": [{"slug": "launch", "name": "Launch", "owner": "ceo"}],
            "tasks": [
                {
                    "slug": "board-package",
                    "name": "Board package",
                    "project": "launch",
                    "assignee": "ceo",
                    "recurrence": "monthly on the 5th",
                }
            ],
        }
    )
    calls: list[str] = []

    def counting(**kwargs: object) -> str:
        calls.append(str(kwargs.get("what", "")))
        return bad_plan

    with pytest.raises(GenerationError, match="org plan failed validation"):
        generate_org_plan(_brief(), _company(), LLMClient(_invoke=counting))

    # One org call, and nothing after it — no per-agent fan-out was attempted.
    assert len(calls) == 1


def test_soul_generator_builds_soul_with_idle_belief() -> None:
    stub = AgentStub(
        slug="ceo",
        name="CEO",
        title="CEO",
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
        name="CEO",
        title="CEO",
        reports_to=None,
        skills=["release-checklist"],
    )
    generate_soul(stub, _company(), LLMClient(_invoke=fake))
    assert seen["thinking"] is True
    assert seen["effort"] == "high"
    assert seen["model"] == "claude-opus-4-8"


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
        name="CEO",
        title="CEO",
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
        name="CEO",
        title="CEO",
        reports_to=None,
        skills=["release-checklist"],
    )
    with pytest.raises(GenerationError):
        generate_soul(stub, _company(), LLMClient(_invoke=lambda **_: bad))


def test_agents_generator_builds_agent_from_stub_and_soul() -> None:
    stub = AgentStub(
        slug="ceo",
        name="CEO",
        title="CEO",
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
        name="CEO",
        title="CEO",
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
        ["CEO"],
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


def test_generate_task_threads_assignee_skills_into_prompt() -> None:
    """ADR-024: the assignee's attached skills reach the prompt so the task can name and
    defer to the governing skill instead of restating its format/storage/protocol."""
    from paperclip_blueprints.generators.tasks import generate_task
    from paperclip_blueprints.models.org_plan import TaskStub

    seen: dict[str, str] = {}

    def capturing(**kwargs: object) -> str:
        seen["user"] = str(kwargs["user"])
        return '```json\n{"objective": "o", "completion_criteria": ["done"]}\n```'

    generate_task(
        TaskStub(slug="weekly-scan", name="Weekly scan", project="p", assignee="scout"),
        _company(),
        LLMClient(_invoke=capturing),
        assignee_skills=["market-scan-note"],
    )
    assert "market-scan-note" in seen["user"]


# --- US4 cost tracking (T051) -----------------------------------------------


def test_client_tallies_usage_from_usage_reporting_transport() -> None:
    def fake(**kwargs: object) -> tuple[str, tuple[int, int]]:
        return ("text", (10, 20))

    client = LLMClient(_invoke=fake)
    client.complete(model="claude-opus-4-8", system="s", user="u")
    client.complete(model="claude-sonnet-4-6", system="s", user="u")
    summary = client.usage_summary()
    assert summary["total"]["calls"] == 2
    assert summary["total"]["input_tokens"] == 20
    assert summary["total"]["output_tokens"] == 40
    assert summary["total"]["cost_usd"] > 0
    assert set(summary["by_model"]) == {"claude-opus-4-8", "claude-sonnet-4-6"}


def test_client_plain_text_transport_records_no_usage() -> None:
    client = LLMClient(_invoke=lambda **_: "text")
    client.complete(model="m", system="s", user="u")
    assert client.usage_summary()["total"]["calls"] == 0


def test_estimate_cost_uses_price_table() -> None:
    from paperclip_blueprints.config import estimate_cost

    # Opus list price: $5/Mtok in, $25/Mtok out → 1M+1M = $30.
    assert estimate_cost("claude-opus-4-8", 1_000_000, 1_000_000) == pytest.approx(30.0)
    # An unknown model falls back to the Sonnet price ($3 + $15 = $18).
    assert estimate_cost("mystery-model", 1_000_000, 1_000_000) == pytest.approx(18.0)


def test_estimate_cost_reconciles_with_real_billing() -> None:
    """Anchor the calculator to a real run so a stale rate can't drift silently.

    Token counts captured from a real generation run 2026-06-01 (13 Opus calls,
    37 Sonnet calls). Actual Anthropic billing for that run was ~$1.50; the
    encoded rates must reproduce it within ±5%.
    """
    from paperclip_blueprints.config import estimate_cost

    opus = estimate_cost("claude-opus-4-8", 27854, 25703)
    sonnet = estimate_cost("claude-sonnet-4-6", 37542, 42884)
    total = opus + sonnet
    assert total == pytest.approx(1.54, rel=0.05)


# --- resilient JSON: a malformed response self-heals at the generator (ADR-014) ---


def test_generator_recovers_from_malformed_then_valid_response() -> None:
    # US1: one malformed soul response is re-sampled, not fatal; the generator
    # returns a valid model and prior work is not regenerated.
    stub = AgentStub(
        slug="ceo",
        name="CEO",
        title="CEO",
        reports_to=None,
        skills=["release-checklist"],
    )
    calls = {"n": 0}

    def flaky(**_: object) -> str:
        calls["n"] += 1
        return _SOUL_JSON.replace("}", "", 1) if calls["n"] == 1 else _SOUL_JSON

    soul = generate_soul(stub, _company(), LLMClient(_invoke=flaky))
    assert isinstance(soul, AgentSoul)
    assert calls["n"] == 2  # one retry, then success


def test_generator_exhaustion_names_the_leaf() -> None:
    # US3: a never-valid response fails with a clear leaf-named error.
    stub = AgentStub(
        slug="ceo", name="CEO", title="CEO", reports_to=None, skills=["release-checklist"]
    )
    with pytest.raises(GenerationError) as exc:
        generate_soul(stub, _company(), LLMClient(_invoke=lambda **_: '{"broken"'))
    assert "soul" in str(exc.value)


# --- feature 016: operating-canon threading (US1) ----------------------------
#
# Section-11 canon is the operator's residual channel: material with no other
# carrier. These tests assert it reaches the four generators that write PROCEDURE,
# wholesale, and reaches none of the three that do not (contracts/canon-threading.md).

# Invented vocabulary — deliberately shaped like the real failing case (a named-dimension
# rubric plus a labelled evidence-class table) without borrowing its content.
_CANON = (
    "Score every prospect on five dimensions: Persuadability, Reach-Confidence, "
    "Timing-Fit, Margin-Headroom and Switch-Cost. Evidence classes carry half-lives: "
    "an Observed-Signal decays in 30 days, an Inferred-Signal in 10 days, and a "
    "Reported-Signal in 5 days. Never promote a prospect on a Reported-Signal alone."
)

_TASK_JSON = """\
```json
{"objective": "Ship the release candidate.", "completion_criteria": ["Smoke pass green."]}
```
"""

_PROJECT_JSON = """\
```json
{"summary": "Ship the first title.", "success_condition": "Title live in the store."}
```
"""

_CANNED = {
    "You write Paperclip agent skills. Follow the instructions exactly.": _SKILL_JSON,
    "You write Paperclip agent mandates. Follow the instructions exactly.": _AGENT_BODY_JSON,
    "You write Paperclip task definitions. Follow the instructions exactly.": _TASK_JSON,
    "You write Paperclip project briefs. Follow the instructions exactly.": _PROJECT_JSON,
}


def _brief_with_canon(canon: str = _CANON) -> CompanyBrief:
    return _brief().model_copy(update={"free_text": canon})


def _recorder() -> tuple[list[str], LLMClient]:
    """A client that records every rendered user prompt and returns canned payloads."""
    seen: list[str] = []

    def _invoke(**kw: object) -> str:
        seen.append(str(kw["user"]))
        return _CANNED.get(str(kw["system"]), "```json\n{}\n```")

    return seen, LLMClient(_invoke=_invoke)


def _render_four(brief: CompanyBrief) -> dict[str, str]:
    """Render all four procedure-carrier prompts; return {kind: prompt}."""
    from contextlib import suppress

    from paperclip_blueprints.generators.projects import generate_project
    from paperclip_blueprints.generators.tasks import generate_task
    from paperclip_blueprints.models.org_plan import ProjectStub, TaskStub

    company = _company()
    canon = brief.free_text
    stub = AgentStub(
        slug="ceo", name="CEO", title="CEO", reports_to=None, skills=["release-checklist"]
    )
    soul = generate_soul(stub, company, LLMClient(_invoke=lambda **_: _SOUL_JSON))
    out: dict[str, str] = {}
    for kind, call in (
        ("skill", lambda c: generate_skill("release-checklist", company, ["CEO"], c, canon=canon)),
        (
            "agent",
            lambda c: generate_agent(stub, company, brief, soul, c, single_agent=True, canon=canon),
        ),
        (
            "task",
            lambda c: generate_task(
                TaskStub(slug="ship-rc", name="Ship RC", project="first-title", assignee="ceo"),
                company,
                c,
                canon=canon,
            ),
        ),
        (
            "project",
            lambda c: generate_project(
                ProjectStub(slug="first-title", name="First Title", owner="ceo"),
                company,
                c,
                canon=canon,
            ),
        ),
    ):
        seen, client = _recorder()
        with suppress(Exception):
            call(client)
        out[kind] = seen[0] if seen else ""
    return out


def test_canon_reaches_all_four_procedure_carriers() -> None:
    """C-T1: the canon appears in every skill/agent/task/project prompt."""
    prompts = _render_four(_brief_with_canon())
    for kind, prompt in prompts.items():
        assert _CANON in prompt, f"operating canon missing from the {kind} prompt"


def test_canon_is_threaded_byte_identical() -> None:
    """C-T2: wholesale — no truncation, summarisation or per-consumer selection."""
    long_canon = _CANON + "\n\n" + ("Tail sentence that a truncating impl would drop. " * 40)
    prompts = _render_four(_brief_with_canon(long_canon))
    for kind, prompt in prompts.items():
        assert long_canon in prompt, f"{kind} prompt did not carry the canon verbatim"


def test_canon_only_content_reaches_a_generated_skill() -> None:
    """C-T7 / FR-017: the direct regression test for the observed defect.

    A phrase present ONLY in section 11 — in no other brief field — must reach the
    skill generator. This is the assertion that would have failed on the 13-agent
    bundle, where a rubric and a threshold table produced zero occurrences.
    """
    brief = _brief_with_canon()
    marker = "Margin-Headroom"
    others = " ".join(
        [
            brief.name,
            brief.description,
            brief.north_star,
            brief.we_are,
            *brief.goals,
            *brief.we_are_not,
            *brief.constraints,
        ]
    )
    assert marker not in others, "fixture error: the marker must be unique to section 11"
    assert marker in _render_four(brief)["skill"]


def test_canon_is_absent_from_the_excluded_generators() -> None:
    """C-T6: souls, operations and goal_hierarchy are never threaded.

    Two different kinds of exclusion, asserted identically here but recorded
    distinctly in the spec: souls is excluded on FITNESS (permanent — procedure is the
    wrong content for a persona artifact whose value depends on brevity); operations and
    goal_hierarchy are excluded on DELIVERY (platform-dependent per ADR-022, verified at
    v2026.626.0 — revisit if import behaviour changes).
    """
    from contextlib import suppress

    from paperclip_blueprints.generators.goal_hierarchy import generate_goal_hierarchy
    from paperclip_blueprints.generators.operations import generate_operations

    brief = _brief_with_canon()
    company = _company()
    stub = AgentStub(
        slug="ceo", name="CEO", title="CEO", reports_to=None, skills=["release-checklist"]
    )
    stub2 = AgentStub(
        slug="dev", name="Dev", title="Engineer", reports_to="ceo", skills=["release-checklist"]
    )
    soul = generate_soul(stub, company, LLMClient(_invoke=lambda **_: _SOUL_JSON))
    canned = LLMClient(_invoke=lambda **_: _AGENT_BODY_JSON)
    # Two agents: the goal hierarchy degrades deterministically (no LLM call) for a
    # single-agent org (ADR-025), so a one-agent list would render no prompt to inspect.
    agents = [
        generate_agent(s, company, brief, soul, canned, single_agent=False, canon=None)
        for s in (stub, stub2)
    ]

    for kind, call in (
        ("soul", lambda c: generate_soul(stub, company, c)),
        ("operations", lambda c: generate_operations(company, brief, [stub, stub2], c)),
        ("goal_hierarchy", lambda c: generate_goal_hierarchy(company, brief, agents, c)),
    ):
        seen, client = _recorder()
        with suppress(Exception):
            call(client)
        assert seen, f"the {kind} generator rendered no prompt"
        assert _CANON not in seen[0], f"operating canon leaked into the {kind} prompt"


def test_free_text_has_exactly_one_read_site_outside_its_prior_consumers() -> None:
    """C-T3: the structural guarantee behind wholesale threading.

    With one read site there is exactly one place a per-consumer transformation could
    be introduced — which makes FR-002 auditable rather than merely asserted.
    """
    import pathlib
    import re

    src = pathlib.Path(__file__).resolve().parent.parent / "src" / "paperclip_blueprints"
    prior = {"models/input.py", "generators/identity.py", "generators/org.py"}
    # Attribute ACCESS, not the bare word — prose in a docstring naming the field is
    # documentation, not a read site, and must not trip this assertion.
    access = re.compile(r"\.free_text\b")
    readers = sorted(
        p.relative_to(src).as_posix()
        for p in src.rglob("*.py")
        if access.search(p.read_text(encoding="utf-8"))
        and p.relative_to(src).as_posix() not in prior
    )
    # An explicit whitelist, one entry per job — the distinction is the point:
    #   renderers/bundle.py — the THREADING read. Exactly one, so there is exactly one
    #                         place a per-consumer transformation could be introduced.
    #   renderers/render.py — the COVERAGE read. Scans the rendered bundle for canon.
    #   cli.py              — the CALIBRATION read (`check-canon`), scanning a bundle
    #                         already on disk.
    #   api.py              — the ENTRY-POINT read (feature 020). Decides whether a brief
    #                         states canon at all, which is what separates "no canon
    #                         stated" from a scan that found nothing.
    # None of the latter three threads anything to a generator. A *generator* appearing
    # here means a carrier started reading the brief directly instead of receiving
    # `canon=`, which is exactly how the wholesale guarantee would decay — so this list is
    # meant to be edited deliberately, with the new reader's job named, never widened to
    # make a failure go away.
    assert readers == ["api.py", "cli.py", "renderers/bundle.py", "renderers/render.py"], (
        f"unexpected free_text read site(s): {readers}"
    )


# --- handoff targets are drawn from a closed set (feature 023) --------------
#
# Contract clauses from specs/023-closed-set-handoffs/contracts/handoff-generation.md.


_HANDOFF_TARGETS = ["cto", "qa-lead", "writer"]

_HANDOFF_BODY = """\
```json
{
  "mandate": "Owns the north star and ships the title.",
  "triggers": ["A release candidate is ready."],
  "receives_from": [{"agent": "qa-lead", "flow": "verified release candidates"}],
  "hands_to": [{"agent": "cto", "flow": "approved scope"},
               {"agent": "writer", "flow": "launch notes"}],
  "deliverables": ["Approved release builds."],
  "can_approve": ["Store metadata within the plan."],
  "must_escalate": ["Pricing changes."],
  "escalation_text": "Escalate to the operator on pricing.",
  "tools_role_specific": "Reviews build status in App Store Connect."
}
```
"""

_NEAR_MISS_BODY = _HANDOFF_BODY.replace('"agent": "qa-lead"', '"agent": "qa-led"')


def _ceo_stub() -> AgentStub:
    return AgentStub(
        slug="ceo", name="CEO", title="CEO", reports_to=None, skills=["release-checklist"]
    )


def _soul() -> AgentSoul:
    """The soul the pre-change baseline was captured with.

    Must stay identical to the one in the capture, or the parity assertion in
    :func:`test_assembled_handoffs_match_the_pre_change_baseline` fails on an input this
    feature does not touch — the soul is passed straight through.
    """
    return AgentSoul(
        identity="I am the CEO.",
        what_we_are="We are a single-title premium studio.",
        product_reality="The product is one polished game.",
        beliefs=["Focus is the moat.", "Idle is a success state; I wait between cycles."],
        how_i_act=["I decide quickly on scope."],
        what_i_dont_do=["I do not ship dark patterns."],
        my_north_star="$30,000 MRR within 12 months.",
    )


def _generate(
    invoke: Callable[..., str],
    *,
    single_agent: bool = False,
    handoff_targets: list[str] | None = None,
) -> AgentDefinition:
    return generate_agent(
        _ceo_stub(),
        _company(),
        _brief(),
        _soul(),
        LLMClient(_invoke=invoke),
        single_agent=single_agent,
        handoff_targets=handoff_targets,
    )


def test_handoff_request_constrains_both_fields_to_the_legal_set() -> None:
    """C1.1, C1.2, C1.3 (FR-001, FR-002, FR-003)."""
    seen: dict[str, object] = {}

    def invoke(**kwargs: object) -> str:
        seen.update(kwargs)
        return _HANDOFF_BODY

    _generate(invoke, handoff_targets=_HANDOFF_TARGETS)
    schema = seen["schema"]
    assert isinstance(schema, dict)
    for field in ("receives_from", "hands_to"):
        frag = schema["properties"][field]
        assert frag["type"] == "array", f"{field} must carry the target as a field"
        items = frag["items"]
        assert items["properties"]["agent"]["enum"] == _HANDOFF_TARGETS
        assert items["properties"]["flow"] == {"type": "string"}
        assert items["additionalProperties"] is False


def test_handoff_prompt_lists_the_same_slugs_the_schema_constrains() -> None:
    """C1.4 (FR-001). Instruction and constraint cannot be allowed to disagree."""
    seen: dict[str, object] = {}

    def invoke(**kwargs: object) -> str:
        seen.update(kwargs)
        return _HANDOFF_BODY

    _generate(invoke, handoff_targets=_HANDOFF_TARGETS)
    prompt = str(seen["user"])
    for slug in _HANDOFF_TARGETS:
        assert f"`{slug}`" in prompt, f"{slug} is constrained but never named in the prompt"


def test_single_agent_is_not_asked_for_a_handoff_at_all() -> None:
    """C1.5 (FR-009, R6). An empty enum has no satisfying value, so do not offer one."""
    seen: dict[str, object] = {}

    def invoke(**kwargs: object) -> str:
        seen.update(kwargs)
        return _AGENT_BODY_JSON

    agent = _generate(invoke, single_agent=True, handoff_targets=[])
    schema = seen["schema"]
    assert isinstance(schema, dict)
    for field in ("receives_from", "hands_to"):
        assert field not in schema["properties"]
        assert field not in schema["required"]
    assert '"agent":' not in str(seen["user"])
    assert agent.receives_from == [] and agent.hands_to == []


def test_a_near_miss_costs_one_call_not_the_run() -> None:
    """C2.3 (FR-005, SC-001). The operator's stated outcome."""
    calls = {"n": 0}

    def invoke(**_: object) -> str:
        calls["n"] += 1
        return _NEAR_MISS_BODY if calls["n"] == 1 else _HANDOFF_BODY

    agent = _generate(invoke, handoff_targets=_HANDOFF_TARGETS)
    assert calls["n"] == 2, "the rejection must re-sample this call, not abort the run"
    assert agent.receives_from == ["qa-lead — verified release candidates"]


def test_an_unrecoverable_near_miss_fails_at_this_agent_naming_the_target() -> None:
    """C2.5 (FR-006, SC-002)."""
    calls = {"n": 0}

    def invoke(**_: object) -> str:
        calls["n"] += 1
        return _NEAR_MISS_BODY

    with pytest.raises(GenerationError) as exc:
        _generate(invoke, handoff_targets=_HANDOFF_TARGETS)
    message = str(exc.value)
    assert "qa-led" in message and "ceo" in message
    assert calls["n"] == 3, "bounded by the existing per-leaf attempt budget"


def test_the_rejection_holds_when_the_schema_is_ignored_entirely() -> None:
    """C3.1, C3.2 (FR-007, SC-004).

    The transport never looks at the schema — the state the project is in if
    ``STRUCTURAL_MODEL`` does not support constrained output. The guarantee must not
    depend on it.

    The call count is the load-bearing half of this assertion, not the raise. A rejection
    also happens when the entries are rejoined after the call, so asserting only that it
    raises passes even with the post-parse check removed — it was written that way first,
    and a mutation check caught it. Three attempts mean the check ran inside the retry
    loop; one attempt would mean the run aborted on the first bad response, which is the
    behaviour this feature exists to replace.
    """
    calls = {"n": 0}

    def invoke(**_: object) -> str:
        calls["n"] += 1
        return _NEAR_MISS_BODY

    with pytest.raises(GenerationError) as exc:
        _generate(invoke, handoff_targets=_HANDOFF_TARGETS)
    assert "qa-led" in str(exc.value)
    assert calls["n"] == 3, "the check must run inside the retry loop, not after it"


def test_the_rejection_holds_when_the_model_declines_the_schema() -> None:
    """C3.1, C3.2 (FR-007, SC-004).

    ``complete_json`` drops a declined schema and retries unconstrained (ADR-014),
    silently. That is precisely when the check has to be the thing that holds.
    """
    saw_unconstrained = {"n": 0}

    def invoke(*, schema: object = None, **_: object) -> str:
        if schema is not None:
            raise APIRequestError("model does not support output_config.format")
        saw_unconstrained["n"] += 1
        return _NEAR_MISS_BODY

    with pytest.raises(GenerationError) as exc:
        _generate(invoke, handoff_targets=_HANDOFF_TARGETS)
    assert saw_unconstrained["n"] > 1, (
        "the check must run on every unconstrained attempt, not just abort on the first"
    )
    assert "qa-led" in str(exc.value)


def test_a_near_miss_is_never_resolved_to_the_real_slug() -> None:
    """C4.1 (FR-008, SC-003, SC-006). The prohibition, at generator level."""
    with pytest.raises(GenerationError):
        _generate(lambda **_: _NEAR_MISS_BODY, handoff_targets=_HANDOFF_TARGETS)


def test_assembled_handoffs_match_the_pre_change_baseline() -> None:
    """C5.1, C5.2 (FR-010, SC-005).

    ``tests/fixtures/baseline_023.json`` was captured from a detached worktree at the
    pre-change commit, driven by the OLD joined-string wire form. The new object form must
    assemble to exactly the same ``AgentDefinition`` — downstream (templates, renderers,
    validator I8) must not be able to tell this feature happened.
    """
    import json
    import pathlib

    baseline = json.loads(
        (pathlib.Path(__file__).resolve().parent / "fixtures" / "baseline_023.json").read_text(
            encoding="utf-8"
        )
    )
    multi = _generate(lambda **_: _HANDOFF_BODY, handoff_targets=_HANDOFF_TARGETS)
    single = _generate(lambda **_: _AGENT_BODY_JSON, single_agent=True, handoff_targets=[])

    assert multi.model_dump(mode="json") == baseline["multi"]
    assert single.model_dump(mode="json") == baseline["single"]
    # Guard against a baseline that would pass while covering nothing.
    assert baseline["multi"]["hands_to"], "the baseline must exercise handoffs"


def test_assembled_handoffs_still_yield_their_slug_to_the_i8_check() -> None:
    """C5.1, C5.3 (FR-010, FR-012). The validator is untouched and still reads these."""
    from paperclip_blueprints.validators.integrity import _handoff_head

    agent = _generate(lambda **_: _HANDOFF_BODY, handoff_targets=_HANDOFF_TARGETS)
    heads = [_handoff_head(e) for e in (*agent.receives_from, *agent.hands_to)]
    assert heads == ["qa-lead", "cto", "writer"]
