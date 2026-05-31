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


def test_agents_generator_calibrates_governance_without_token_enum() -> None:
    text = load_prompt("agents_generator")
    assert "{{ governance_position }}" in text
    # Decision rights are plain prose; the prompt must NOT instruct embedding
    # Paperclip's internal approval-flow tokens (ADR-007 / CONTEXT.md).
    for token in (
        "hire_agent",
        "budget_override",
        "approve_ceo_strategy",
        "request_board_approval",
    ):
        assert token not in text


def test_soul_generator_requires_idle_state() -> None:
    text = load_prompt("soul_generator")
    assert "idle" in text.lower()


def test_agents_generator_preserves_north_star_currency_verbatim() -> None:
    """Guard against the $→€ currency-conversion bug in the agent mandate.

    The north star is woven into mandate prose by the model, so the only
    deterministic regression guard is the prompt instruction itself: it must
    tell the model to quote the figure verbatim and never convert currency.
    """
    text = load_prompt("agents_generator").lower()
    assert "verbatim" in text
    assert "currency" in text
    assert "convert" in text


# --- US1 full-bundle prompts (T011) -----------------------------------------


@pytest.mark.parametrize(
    "name",
    ["operations_generator", "project_generator", "task_generator"],
)
def test_full_bundle_prompt_loadable_and_demands_json(name: str) -> None:
    text = load_prompt(name)
    assert text.strip()
    assert "```json" in text


def test_org_planner_supports_full_org_with_span_of_control() -> None:
    text = load_prompt("org_planner")
    for key in ("agents", "projects", "tasks"):
        assert key in text
    assert "span of control" in text.lower() or "span-of-control" in text.lower()
    assert "7" in text  # the span-of-control limit


def test_operations_prompt_demands_anti_drift_echo() -> None:
    text = load_prompt("operations_generator")
    assert "anti_drift_checks" in text
    # The prompt must require reproducing every constraint and "we are not".
    assert "we are not" in text.lower()
    assert "constraint" in text.lower()


def test_agents_generator_supports_multi_agent_handoffs() -> None:
    text = load_prompt("agents_generator")
    assert "{{ manager }}" in text or "manager" in text
    assert "receives_from" in text and "hands_to" in text
