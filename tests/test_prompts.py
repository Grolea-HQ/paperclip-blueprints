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


def test_task_generator_defers_to_governing_skill() -> None:
    # ADR-024: a task that maps to a skill-governed process must reference the governing
    # skill and NOT restate its format/storage/step-by-step process. The prompt must (a)
    # be given the assignee's attached skills, and (b) instruct deference.
    text = load_prompt("task_generator")
    assert "assignee_skills" in text  # the attached-skills context is threaded in
    low = text.lower()
    assert "skill" in low
    # deference wording: name the governing skill, do not duplicate its how
    assert "per the" in low  # "perform <work> per the <skill> skill"
    assert "do not" in low or "must not" in low
    for how_word in ("format", "storage"):
        assert how_word in low  # names the things a task must NOT restate


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


# --- governance naming & board-gate anti-drift (ADR-016) --------------------


def test_org_planner_has_naming_guard_and_ceo_example() -> None:
    text = load_prompt("org_planner")  # P-1
    low = text.lower()
    assert "naming guard" in low
    assert "founder" in low and "board" in low
    assert "Founder / CEO" not in text  # the banned example name is gone
    assert '"name": "CEO"' in text


def test_org_planner_has_ownership_chain() -> None:
    low = load_prompt("org_planner").lower()  # P-2
    assert "ownership chain" in low
    assert "backstop" in low and "orphan" in low


def test_identity_prompt_keeps_human_principal_out_of_agents() -> None:
    low = load_prompt("identity_generator").lower()  # P-3
    assert "principal" in low
    assert "never personify" in low or "not an agent" in low or "never assign final" in low


def test_operations_prompt_encodes_board_authority() -> None:
    low = load_prompt("operations_generator").lower()  # P-4
    assert "sole approver" in low
    assert "ready for board review" in low
    assert "auto-close" in low or "auto close" in low
    assert "self-approve" in low or "never approves on the board" in low


def test_agents_prompt_encodes_board_gate_and_ownership() -> None:
    low = load_prompt("agents_generator").lower()  # P-5
    assert "board" in low and "must_escalate" in low
    assert "ready for board review" in low
    assert "primary owner" in low and "backstop" in low


# --- routines: org_planner sets recurrence only for scheduled work (ADR-022 US3) -----------


def test_org_planner_recurrence_rule_is_scheduled_work_only() -> None:
    text = load_prompt("org_planner")
    low = text.lower()
    assert "recurrence" in low
    # gated to genuinely scheduled standing work, default null
    assert "null" in low and ("standing schedule" in low or "scheduled" in low)
    # the cadence vocabulary incl. a weekday-list example
    assert "mon,wed,fri" in low
    assert '"recurrence"' in text  # emitted in the task output shape


def test_org_planner_treats_customization_notes_as_binding() -> None:
    low = load_prompt("org_planner").lower()
    assert "{{ use_case_notes }}" in load_prompt("org_planner")  # the notes reach the prompt
    assert "binding" in low
    assert "roster" in low and "headcount" in low
    # an explicit roster must not be expanded or split into sub-teams
    assert "do not add roles" in low or "exactly the stated agents" in low
    assert "sub-team" in low


def test_org_planner_one_cadence_one_recurring_task() -> None:
    low = load_prompt("org_planner").lower()
    assert "one cadence" in low and "one recurring task" in low
    # a single scheduled activity must not become multiple recurring tasks
    assert "do not split" in low
    assert "sub-step" in low and ("fold" in low or "handoff" in low)
    # genuinely-distinct cadences still get separate recurring tasks
    assert "distinct cadences" in low
