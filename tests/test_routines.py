"""Focused tests for the PROVISIONAL routines emission (ADR-022, US3) — tasks-driven.

Routines come from tasks that carry a `recurrence` cadence: each becomes a `.paperclip.yaml`
routines.<task-slug> block, and the existing TASK.md is flagged `recurring: true` (no shadow
task). The cron honors the cadence; cron validity + the routines shape stay live-confirm only.
All offline. Isolated so a live correction is a contained, single-file change.
"""

from __future__ import annotations

import subprocess
import sys

from ruamel.yaml import YAML

from paperclip_blueprints.models.input import CompanyBrief
from paperclip_blueprints.models.output import CompanyConfig
from paperclip_blueprints.models.task import TaskDefinition
from paperclip_blueprints.renderers.render import render_files
from paperclip_blueprints.renderers.routines import (
    END_HOUR,
    MINUTE_STEP,
    START_HOUR,
    cron_for,
    derive_routines,
    slot_for,
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


# --- slot derivation (feature 015) ------------------------------------------


def test_slot_is_inside_the_window_and_on_a_minute_step() -> None:
    # T1: hours stay inside the supervised window; minutes land on a step boundary so the
    # generated schedule stays human-legible.
    for slug in ("signal-scan", "board-package", "daily-recap", "register-refresh"):
        hour, minute = slot_for(slug)
        assert START_HOUR <= hour <= END_HOUR
        assert minute % MINUTE_STEP == 0
        assert 0 <= minute < 60


def test_slots_spread_rather_than_concentrate() -> None:
    # T4: the point of the feature. Twenty distinct slugs must not pile onto one or two slots.
    slugs = [f"routine-task-{i}" for i in range(20)]
    slots = {slot_for(s) for s in slugs}
    hours = {h for h, _ in (slot_for(s) for s in slugs)}
    assert len(slots) >= 15  # near-distinct across 144 slots
    assert len(hours) >= 6  # and not all in one part of the day


def test_slot_is_identical_in_a_separate_interpreter_process() -> None:
    # T2 / FR-003. This is the guard that an in-process test CANNOT provide: builtin hash() on
    # str is salted per process (PYTHONHASHSEED), so an implementation using it would agree with
    # itself all through this suite — one process, one salt — and still emit a different schedule
    # on every real run. The subprocess is the point of the test, not incidental setup.
    slugs = ["signal-scan", "board-package", "daily-recap"]
    script = (
        "from paperclip_blueprints.renderers.routines import slot_for;"
        f"print([slot_for(s) for s in {slugs!r}])"
    )
    out = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == str([slot_for(s) for s in slugs])


def test_slot_depends_only_on_the_slug() -> None:
    # T3: a task's time must not shift because other tasks exist — that is what makes the
    # per-task hash preferable to assigning slots by position in a sorted list.
    assert slot_for("signal-scan") == slot_for("signal-scan")
    assert slot_for("signal-scan") != slot_for("signal-scan-2")


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


def _day_pattern(cron: str) -> str:
    """The cron fields that encode WHICH days — everything after minute and hour."""
    return " ".join(cron.split()[2:])


def _time_of_day(cron: str) -> tuple[int, int]:
    minute, hour = cron.split()[0], cron.split()[1]
    return int(hour), int(minute)


def test_cron_for_named_cadences_keeps_the_day_pattern() -> None:
    # T5: the cadence binding is correct today and must not change — only time-of-day moves.
    assert _day_pattern(cron_for("daily", "a")) == "* * *"
    assert _day_pattern(cron_for("weekly", "a")) == "* * 1"
    assert _day_pattern(cron_for("monthly", "a")) == "1 * *"
    assert _day_pattern(cron_for("quarterly", "a")) == "1 1,4,7,10 *"


def test_cron_for_weekday_list_honors_the_brief_cadence() -> None:
    assert _day_pattern(cron_for("mon,wed,fri", "a")) == "* * 1,3,5"
    assert _day_pattern(cron_for("Monday, Wednesday, Friday", "a")) == "* * 1,3,5"
    assert _day_pattern(cron_for("tue/thu", "a")) == "* * 2,4"


def test_cron_for_unknown_falls_back_to_weekly() -> None:
    assert _day_pattern(cron_for("whenever", "a")) == "* * 1"  # T8


def test_cron_time_of_day_comes_from_the_slug_slot() -> None:
    # T6/T7: same cadence, different slugs → same days, different times.
    assert _time_of_day(cron_for("daily", "signal-scan")) == slot_for("signal-scan")
    a, b = cron_for("daily", "signal-scan"), cron_for("daily", "daily-recap")
    assert _day_pattern(a) == _day_pattern(b)
    assert _time_of_day(a) != _time_of_day(b)


# --- derive_routines (tasks-driven) -----------------------------------------


def test_derive_routines_emits_only_recurring_tasks() -> None:
    tasks = [
        _task("scan-infra-landscape", "Scan the infra landscape"),  # not recurring
        _task("signal-scan", "Signal scan", recurrence="mon,wed,fri"),
        _task("board-package", "Monthly board package", recurrence="monthly"),
    ]
    routines = derive_routines(tasks)
    assert [r.slug for r in routines] == ["signal-scan", "board-package"]  # short, real slugs
    # Day pattern comes from the cadence (unchanged); time-of-day from the task's own slot.
    assert _day_pattern(routines[0].cron) == "* * 1,3,5"
    assert _day_pattern(routines[1].cron) == "1 * *"
    assert _time_of_day(routines[0].cron) == slot_for("signal-scan")
    assert _time_of_day(routines[1].cron) == slot_for("board-package")


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
    hour, minute = slot_for("signal-scan")
    assert f'cronExpression: "{minute} {hour} * * 1,3,5"' in y
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


def test_two_renders_of_one_config_produce_identical_triggers() -> None:
    # SC-002: an unchanged brief must regenerate byte-identically.
    def _yaml() -> str:
        config = CompanyConfig(
            **_full_config_kwargs(
                tasks=[
                    _task("signal-scan", "Scan", recurrence="daily"),
                    _task("board-package", "Board", recurrence="monthly"),
                ]
            )
        )
        return render_files(config)[".paperclip.yaml"]

    assert _yaml() == _yaml()


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


# --- producer/consumer ordering (feature 015, US3) ---------------------------
#
# FR-008: fires when one task names another, they share a day pattern, and the referencing task
# is scheduled AT OR BEFORE the one it names. Keying on trigger EQUALITY (the originally drafted
# rule) would have gone silent exactly when US1's spread separated the pair — leaving a recap
# scheduled hours before the scan it summarises, unreported.


def _ordering(*tasks: TaskDefinition) -> list[str]:
    return [w for w in _warnings_for(*tasks) if "before the" in w]


def _consumer_producer(
    consumer_slug: str, producer_slug: str, cadence: str
) -> tuple[TaskDefinition, TaskDefinition]:
    producer = _task(producer_slug, producer_slug.replace("-", " ").title(), recurrence=cadence)
    consumer = TaskDefinition(
        slug=consumer_slug,
        name=consumer_slug.replace("-", " ").title(),
        project="launch-v1",
        assignee="cto",
        objective=f"Summarise the output of the {producer_slug} task from today.",
        completion_criteria=["done"],
        recurrence=cadence,
    )
    return consumer, producer


def test_consumer_scheduled_before_its_named_producer_warns() -> None:
    # T15/FR-008a. The slugs are chosen so the consumer's slot precedes the producer's.
    consumer, producer = _consumer_producer("alpha-recap", "signal-scan", "daily")
    if slot_for("alpha-recap") > slot_for("signal-scan"):
        consumer, producer = _consumer_producer("signal-scan", "alpha-recap", "daily")
    warnings = _ordering(consumer, producer)
    assert warnings, "a consumer scheduled at or before its producer must be reported"
    assert consumer.slug in warnings[0] and producer.slug in warnings[0]


def test_consumer_scheduled_after_its_producer_is_not_warned() -> None:
    # T16 — the healthy case.
    consumer, producer = _consumer_producer("alpha-recap", "signal-scan", "daily")
    if slot_for(consumer.slug) <= slot_for(producer.slug):
        consumer, producer = _consumer_producer(producer.slug, consumer.slug, "daily")
    assert _ordering(consumer, producer) == []


def test_ordering_is_not_checked_across_different_day_patterns() -> None:
    # T17/FR-008b — no single well-defined "before" across differing patterns.
    consumer, producer = _consumer_producer("alpha-recap", "signal-scan", "daily")
    weekly_producer = _task("signal-scan", "Signal Scan", recurrence="weekly")
    assert _ordering(consumer, weekly_producer) == []


def test_ordering_reference_matching_is_word_boundaried() -> None:
    # T18/FR-009 — "scan" inside "scandal" is not a reference to the scan task.
    producer = _task("scan", "Scan", recurrence="daily")
    consumer = TaskDefinition(
        slug="alpha-report",
        name="Alpha Report",
        project="launch-v1",
        assignee="cto",
        objective="Review any scandal coverage and file a summary.",
        completion_criteria=["done"],
        recurrence="daily",
    )
    assert _ordering(consumer, producer) == []


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


# --- shared-trigger collisions (feature 015, US2) ----------------------------
#
# A SECOND check, keyed differently from the split-activity smell above on purpose. That one
# asks "was one activity split into two tasks?" and rightly ignores pairs with different
# owners. This one asks "will these fire at the same moment and contend?", for which the owner
# is irrelevant. Neither subsumes the other.


def _collisions(*tasks: TaskDefinition) -> list[str]:
    return [w for w in _warnings_for(*tasks) if "same trigger" in w]


def test_two_recurring_tasks_sharing_a_trigger_warn_across_different_owners() -> None:
    # T9/T10 — the operator-required regression test. Construct the collision directly by
    # giving two tasks the same slug-derived slot is impossible, so share the cadence and force
    # the same slot via slugs that hash together; instead assert on a constructed routine set.
    from paperclip_blueprints.renderers.render import _routine_trigger_collisions
    from paperclip_blueprints.renderers.routines import RoutineSpec

    routines = [
        RoutineSpec("daily-scan", "Scan", "cto", "launch-v1", "0 9 * * *"),
        RoutineSpec("daily-recap", "Recap", "ceo", "launch-v1", "0 9 * * *"),
    ]
    (warning,) = _routine_trigger_collisions(routines)
    assert "daily-scan" in warning and "daily-recap" in warning
    assert "0 9 * * *" in warning


def test_routines_with_distinct_triggers_do_not_collide() -> None:
    # T11
    from paperclip_blueprints.renderers.render import _routine_trigger_collisions
    from paperclip_blueprints.renderers.routines import RoutineSpec

    routines = [
        RoutineSpec("a", "A", "cto", "launch-v1", "0 9 * * *"),
        RoutineSpec("b", "B", "cto", "launch-v1", "30 14 * * *"),
    ]
    assert _routine_trigger_collisions(routines) == []


def test_both_checks_fire_on_a_pair_matching_both_conditions() -> None:
    # T14 — the two checks are independent; neither replaces the other. A pair sharing a cadence
    # AND an assignee AND a trigger must produce both findings, each about its own concern.
    from paperclip_blueprints.renderers.render import (
        _routine_cadence_smells,
        _routine_trigger_collisions,
    )
    from paperclip_blueprints.renderers.routines import RoutineSpec

    routines = [
        RoutineSpec("scan-a", "A", "cto", "launch-v1", "0 9 * * *"),
        RoutineSpec("scan-b", "B", "cto", "launch-v1", "0 9 * * *"),
    ]
    assert len(_routine_cadence_smells(routines)) == 1
    assert len(_routine_trigger_collisions(routines)) == 1


def test_collision_findings_are_stably_ordered_and_never_block_validation() -> None:
    # T12/T13
    from paperclip_blueprints.renderers.render import _routine_trigger_collisions
    from paperclip_blueprints.renderers.routines import RoutineSpec

    routines = [
        RoutineSpec("z", "Z", "cto", "launch-v1", "30 14 * * *"),
        RoutineSpec("a", "A", "cto", "launch-v1", "0 9 * * *"),
        RoutineSpec("y", "Y", "ceo", "launch-v1", "30 14 * * *"),
        RoutineSpec("b", "B", "ceo", "launch-v1", "0 9 * * *"),
    ]
    assert _routine_trigger_collisions(routines) == _routine_trigger_collisions(routines)
    assert len(_routine_trigger_collisions(routines)) == 2

    # and a colliding bundle still renders and passes the shape validator
    config = CompanyConfig(
        **_full_config_kwargs(
            tasks=[
                _task("signal-scan", "Scan", recurrence="daily", assignee="cto"),
                _task("board-package", "Board", recurrence="daily", assignee="ceo"),
            ]
        )
    )
    files = render_files(config)
    assert not any(x.startswith("S15") for x in check_schema_shape(config, files))


def test_same_cadence_different_assignee_routines_do_not_warn() -> None:
    warnings = _warnings_for(
        _task("scan-landscape", "Scan", recurrence="mon,wed,fri", assignee="cto"),
        _task("board-package", "Board", recurrence="mon,wed,fri", assignee="ceo"),
    )
    assert not any("split into multiple recurring" in w for w in warnings)
