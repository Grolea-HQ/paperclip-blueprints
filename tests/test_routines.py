"""Focused tests for the PROVISIONAL routines emission (ADR-022, US3) — tasks-driven.

Routines come from tasks that carry a `recurrence` cadence: each becomes a `.paperclip.yaml`
routines.<task-slug> block, and the existing TASK.md is flagged `recurring: true` (no shadow
task). The cron honors the cadence; cron validity + the routines shape stay live-confirm only.
All offline. Isolated so a live correction is a contained, single-file change.
"""

from __future__ import annotations

from ruamel.yaml import YAML

from paperclip_blueprints.models.input import CompanyBrief
from paperclip_blueprints.models.output import CompanyConfig
from paperclip_blueprints.models.task import TaskDefinition
from paperclip_blueprints.renderers.render import render_files
from paperclip_blueprints.renderers.routines import (
    cron_for,
    derive_routines,
    wakes_per_active_month,
)
from paperclip_blueprints.validators.schema_shape import check_schema_shape
from test_models import _brief_kwargs, _full_config_kwargs
from test_templates import _config


def _task(
    slug: str, name: str, recurrence: str | None = None, assignee: str = "cto"
) -> TaskDefinition:
    return TaskDefinition(
        slug=slug,
        name=name,
        project="launch-v1",  # a real project in the full fixture
        assignee=assignee,  # "cto"/"ceo" are real agents in the full fixture
        objective="o",
        completion_criteria=["done"],
        recurrence=recurrence,
    )


# --- cadence → wakes per active month (ADR-012 amendment) --------------------


def test_wakes_counts_the_active_month_not_the_average_month() -> None:
    # Monthly, quarterly and yearly all wake ONCE in a month they run at all. Counting the
    # average calendar month instead would rank quarterly below monthly and starve the cap in
    # the single month the agent runs.
    assert wakes_per_active_month("monthly") == 1
    assert wakes_per_active_month("quarterly") == 1
    assert wakes_per_active_month("yearly") == 1


def test_wakes_for_frequent_cadences() -> None:
    assert wakes_per_active_month("daily") == 30
    assert wakes_per_active_month("weekly") == 4
    assert wakes_per_active_month("mon,wed,fri") == 12


def test_wakes_is_none_for_an_unscheduled_agent() -> None:
    assert wakes_per_active_month(None) is None


# --- cadence → cron translator ----------------------------------------------


def test_cron_for_named_cadences() -> None:
    assert cron_for("daily") == "0 9 * * *"
    assert cron_for("weekly") == "0 9 * * 1"
    assert cron_for("monthly") == "0 9 1 * *"
    assert cron_for("quarterly") == "0 9 1 1,4,7,10 *"


def test_cron_for_weekday_list_honors_the_brief_cadence() -> None:
    assert cron_for("mon,wed,fri") == "0 9 * * 1,3,5"
    assert cron_for("Monday, Wednesday, Friday") == "0 9 * * 1,3,5"
    assert cron_for("tue/thu") == "0 9 * * 2,4"


def test_cron_for_unknown_falls_back_to_weekly() -> None:
    assert cron_for("whenever") == "0 9 * * 1"


# --- derive_routines (tasks-driven) -----------------------------------------


def test_derive_routines_emits_only_recurring_tasks() -> None:
    tasks = [
        _task("scan-infra-landscape", "Scan the infra landscape"),  # not recurring
        _task("signal-scan", "Signal scan", recurrence="mon,wed,fri"),
        _task("board-package", "Monthly board package", recurrence="monthly"),
    ]
    routines = derive_routines(tasks)
    assert [r.slug for r in routines] == ["signal-scan", "board-package"]  # short, real slugs
    assert routines[0].cron == "0 9 * * 1,3,5"
    assert routines[1].cron == "0 9 1 * *"


def test_derive_routines_inherits_task_assignee_and_project() -> None:
    # Part-2 acceptance: each routine resolves a real assignee + project from its task.
    (routine,) = derive_routines([_task("signal-scan", "Signal scan", recurrence="mon,wed,fri")])
    assert routine.assignee == "cto"
    assert routine.project == "launch-v1"


def test_derive_routines_empty_when_no_task_is_scheduled() -> None:
    assert derive_routines([_task("ship", "Ship"), _task("review", "Review")]) == []


# --- render: one task set, recurring flagged, routines keyed off real slug ---


def test_recurring_task_renders_routine_block_and_recurring_flag() -> None:
    config = CompanyConfig(
        **_full_config_kwargs(
            tasks=[
                _task("ship", "Ship"),
                _task("signal-scan", "Signal scan", recurrence="mon,wed,fri"),
            ]
        )
    )
    files = render_files(config)
    y = files[".paperclip.yaml"]
    assert "routines:" in y
    assert "signal-scan:" in y
    assert 'cronExpression: "0 9 * * 1,3,5"' in y
    # the recurring task is the EXISTING task, flagged — no shadow task
    assert "recurring: true" in files["tasks/signal-scan/TASK.md"]
    assert "recurring: true" not in files["tasks/ship/TASK.md"]
    # one task set: exactly the two declared tasks, no extra routine task dir
    task_dirs = {p.split("/")[1] for p in files if p.startswith("tasks/")}
    assert task_dirs == {"ship", "signal-scan"}


def test_no_recurring_task_means_no_routines_block() -> None:
    files = render_files(CompanyConfig(**_full_config_kwargs()))  # fixture "ship" is not recurring
    assert "routines:" not in files[".paperclip.yaml"]
    assert "recurring: true" not in files["tasks/ship/TASK.md"]


def test_single_agent_bundle_has_no_routines() -> None:
    files = render_files(_config())  # single-agent: no tasks
    assert "routines:" not in files[".paperclip.yaml"]
    assert not any(p.startswith("tasks/") for p in files)


# --- S15 routines closure ----------------------------------------------------


def test_s15_clean_when_routines_match_recurring_tasks() -> None:
    config = CompanyConfig(
        **_full_config_kwargs(
            tasks=[_task("ship", "Ship"), _task("signal-scan", "Signal scan", recurrence="weekly")]
        )
    )
    files = render_files(config)
    assert not any(x.startswith("S15") for x in check_schema_shape(config, files))


def test_s15_flags_an_orphan_routine_block() -> None:
    config = CompanyConfig(**_full_config_kwargs())  # no recurring task → no routines
    files = render_files(config)
    files[".paperclip.yaml"] += "\nroutines:\n  ghost:\n    triggers: []\n"
    assert any(x.startswith("S15") and "ghost" in x for x in check_schema_shape(config, files))


# --- cadence-weighted budgets through the pipeline (ADR-012 amendment) -------


def _budget_for(agent: str, *tasks: TaskDefinition) -> int:
    config = CompanyConfig(
        **_full_config_kwargs(
            tasks=list(tasks),
            brief=CompanyBrief(**_brief_kwargs(capital_monthly_eur=400)),
        )
    )
    data = YAML(typ="safe").load(render_files(config)[".paperclip.yaml"])
    return data["agents"][agent]["budgetMonthlyCents"]


def test_a_daily_driven_agent_gets_a_larger_cap_than_a_quarterly_driven_one() -> None:
    # Same agent, same role bucket, cadence alone varied.
    daily = _budget_for("cto", _task("scan", "Scan", recurrence="daily", assignee="cto"))
    quarterly = _budget_for("cto", _task("scan", "Scan", recurrence="quarterly", assignee="cto"))
    assert daily > quarterly


def test_an_agents_busiest_cadence_sets_its_cap() -> None:
    # An agent driven by both a daily and a quarterly routine must be funded for the daily one.
    both = _budget_for(
        "cto",
        _task("scan", "Scan", recurrence="daily", assignee="cto"),
        _task("review", "Review", recurrence="quarterly", assignee="cto"),
    )
    daily_only = _budget_for("cto", _task("scan", "Scan", recurrence="daily", assignee="cto"))
    assert both == daily_only


# --- soft warning: a split scheduled activity (same cadence + assignee) ------


def _warnings_for(*tasks: TaskDefinition) -> list[str]:
    config = CompanyConfig(**_full_config_kwargs(tasks=list(tasks)))
    captured: list[str] = []
    render_files(config, warn=captured.append)
    return captured


def test_same_cadence_same_assignee_routines_warn() -> None:
    warnings = _warnings_for(
        _task("scan-landscape", "Scan", recurrence="mon,wed,fri", assignee="cto"),
        _task("log-signal-patterns", "Log", recurrence="mon,wed,fri", assignee="cto"),
    )
    smell = [w for w in warnings if "split into multiple recurring" in w]
    assert smell, warnings
    assert "scan-landscape" in smell[0] and "log-signal-patterns" in smell[0]
    assert "one-cadence rule" in smell[0]


def test_same_cadence_different_assignee_routines_do_not_warn() -> None:
    warnings = _warnings_for(
        _task("scan-landscape", "Scan", recurrence="mon,wed,fri", assignee="cto"),
        _task("board-package", "Board", recurrence="mon,wed,fri", assignee="ceo"),
    )
    assert not any("split into multiple recurring" in w for w in warnings)
