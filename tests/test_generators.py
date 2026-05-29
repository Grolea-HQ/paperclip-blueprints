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
    assert seen["model"] == "claude-opus-4-7"


# --- org / agents / souls / skills generators (T018) ------------------------


def _company() -> CompanyDefinition:
    return generate_identity(_brief(), LLMClient(_invoke=lambda **_: _IDENTITY_JSON))


_ORG_JSON = """\
```json
{"slug": "ceo", "name": "Founder / CEO", "title": "Founder / CEO",
 "reports_to": null, "skills": ["release-checklist"]}
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
  "must_escalate": ["Pricing changes (budget_override)."],
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
