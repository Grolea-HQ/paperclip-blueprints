"""Tests that prompts are loadable and carry their required template variables."""

import pytest

from paperclip_blueprints.generators.client import GenerationError, load_prompt


def test_identity_prompt_loadable() -> None:
    text = load_prompt("identity_generator")
    assert text.strip()


@pytest.mark.parametrize(
    "var",
    ["name", "slug", "description", "north_star", "goals", "we_are", "we_are_not", "constraints"],
)
def test_identity_prompt_has_required_variables(var: str) -> None:
    text = load_prompt("identity_generator")
    assert "{{ " + var + " }}" in text or "{{" + var + "}}" in text or var in text


def test_identity_prompt_demands_json_output() -> None:
    text = load_prompt("identity_generator")
    assert "```json" in text


def test_unknown_prompt_raises() -> None:
    with pytest.raises(GenerationError):
        load_prompt("no_such_prompt")


# --- US1 prompts (T019) -----------------------------------------------------


@pytest.mark.parametrize(
    "name",
    ["org_planner", "agents_generator", "soul_generator", "skill_generator"],
)
def test_us1_prompt_loadable_and_demands_json(name: str) -> None:
    text = load_prompt(name)
    assert text.strip()
    assert "```json" in text


def test_org_planner_enforces_single_owner() -> None:
    text = load_prompt("org_planner")
    assert "reports_to" in text and "null" in text


def test_agents_generator_has_governance_and_approval_types() -> None:
    text = load_prompt("agents_generator")
    assert "{{ governance_position }}" in text
    for approval in ("strategy", "hire_agent", "budget_override", "custom"):
        assert approval in text


def test_soul_generator_requires_idle_state() -> None:
    text = load_prompt("soul_generator")
    assert "idle" in text.lower()
