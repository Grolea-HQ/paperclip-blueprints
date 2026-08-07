"""Focused tests for the PROVISIONAL routines emission (ADR-022, US3) — tasks-driven.

Routines come from tasks that carry a `recurrence` cadence: each becomes a `.paperclip.yaml`
routines.<task-slug> block, and the existing TASK.md is flagged `recurring: true` (no shadow
task). The cron honors the cadence; cron validity + the routines shape stay live-confirm only.
All offline. Isolated so a live correction is a contained, single-file change.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
from zoneinfo import available_timezones

import pytest
from ruamel.yaml import YAML

from paperclip_blueprints.models.cadence import Cadence
from paperclip_blueprints.models.input import CompanyBrief
from paperclip_blueprints.models.output import CompanyConfig
from paperclip_blueprints.models.task import TaskDefinition
from paperclip_blueprints.renderers.render import render_files
from paperclip_blueprints.renderers.routines import (
    DEFAULT_TIMEZONE,
    END_HOUR,
    MINUTE_STEP,
    START_HOUR,
    cron_for,
    day_pattern_for,
    derive_routines,
    resolve_timezone,
    schedules_can_intersect,
    slot_for,
    wakes_per_active_month,
)
from paperclip_blueprints.validators.schema_shape import check_schema_shape
from test_models import _brief_kwargs, _full_config_kwargs
from test_templates import _config


def _task(
    slug: str, name: str, recurrence: str | Cadence | None = None, assignee: str = "cto"
) -> TaskDefinition:
    return TaskDefinition(
        slug=slug,
        name=name,
        project="launch-v1",  # a real project in the full fixture
        assignee=assignee,  # "cto"/"ceo" are real agents in the full fixture
        objective="o",
        completion_criteria=["done"],
        recurrence=Cadence.coerce(recurrence) if recurrence is not None else None,
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


def test_cron_for_unknown_cadence_raises_rather_than_falling_back() -> None:
    # C1.8 / FR-007 — replaces the former "unknown falls back to weekly" behaviour, deliberately.
    # That fallback meant `monthly on the 5th` emitted a WEEKLY MONDAY routine: a planner that
    # tried to keep the stated day got a worse result than one that discarded it. Silent degrade
    # is the defect, not the safety net.
    with pytest.raises(ValueError, match="not a recognisable cadence"):
        cron_for("whenever", "a")
    with pytest.raises(ValueError):
        cron_for("monthly on the 5th", "a")


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
        _task("signal-scan", "Signal scan", recurrence=Cadence.coerce("mon,wed,fri")),
        _task("board-package", "Monthly board package", recurrence=Cadence.coerce("monthly")),
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
    (routine,) = derive_routines(
        [_task("signal-scan", "Signal scan", recurrence=Cadence.coerce("mon,wed,fri"))]
    )
    assert routine.assignee == "cto"
    assert routine.project == "launch-v1"


def test_derive_routines_empty_when_no_task_is_scheduled() -> None:
    assert derive_routines([_task("ship", "Ship"), _task("review", "Review")]) == []


# --- schedule intersection (feature 018, C4) ---------------------------------
#
# Feature 015 compared ordering only within an IDENTICAL day pattern, because "before" is not
# well defined across differing patterns. That was too blunt: a daily consumer of a weekly
# producer genuinely does fire on the producer's day, so their ordering is comparable there.
# Equality under-catches exactly the cross-cadence dependency this is meant to see.


def _dp(cadence: Cadence) -> str:
    return day_pattern_for(cadence)


def test_daily_and_weekly_schedules_intersect() -> None:
    # C4.1 — the case day-pattern equality misses.
    assert schedules_can_intersect(_dp(Cadence.of("daily")), _dp(Cadence.of("weekly")))
    assert schedules_can_intersect(
        _dp(Cadence.of("daily")), _dp(Cadence.of("weekly", days_of_week=["tue"]))
    )


def test_disjoint_weekdays_do_not_intersect() -> None:
    # C4.2
    tue = _dp(Cadence.of("weekly", days_of_week=["tue"]))
    thu = _dp(Cadence.of("weekly", days_of_week=["thu"]))
    assert not schedules_can_intersect(tue, thu)


def test_disjoint_months_do_not_intersect() -> None:
    # C4.3
    q1 = _dp(Cadence.of("quarterly", day_of_month=5, months=["jan", "apr"]))
    q2 = _dp(Cadence.of("quarterly", day_of_month=5, months=["feb", "may"]))
    assert not schedules_can_intersect(q1, q2)


def test_quarterly_and_monthly_intersect_on_shared_months() -> None:
    # C4.3 — a monthly schedule runs in every month, so it meets the quarterly one.
    monthly = _dp(Cadence.of("monthly", day_of_month=5))
    quarterly = _dp(Cadence.of("quarterly", day_of_month=5, months=["jan", "apr", "jul", "oct"]))
    assert schedules_can_intersect(monthly, quarterly)


def test_different_days_of_month_do_not_intersect() -> None:
    assert not schedules_can_intersect(
        _dp(Cadence.of("monthly", day_of_month=5)), _dp(Cadence.of("monthly", day_of_month=8))
    )


def test_day_of_month_and_weekday_schedules_can_intersect() -> None:
    # The 5th falls on a Tuesday sometimes. Cron ORs a restricted day-of-month with a restricted
    # day-of-week, and across months every day-of-month meets every weekday — so this pair is
    # comparable rather than provably disjoint.
    assert schedules_can_intersect(
        _dp(Cadence.of("monthly", day_of_month=5)),
        _dp(Cadence.of("weekly", days_of_week=["tue"])),
    )


# --- structured cadence → day pattern (feature 018) --------------------------


def test_structured_weekday_reaches_the_day_pattern() -> None:
    # C2.1 / SC-001 — the stated Tuesday that previously landed on Monday.
    assert day_pattern_for(Cadence.of("weekly", days_of_week=["tue"])) == "* * 2"
    assert day_pattern_for(Cadence.of("weekly", days_of_week=["mon", "wed", "fri"])) == "* * 1,3,5"


def test_structured_day_of_month_reaches_the_day_pattern() -> None:
    # C2.2 / SC-002 — no cadence string could ever produce this.
    assert day_pattern_for(Cadence.of("monthly", day_of_month=5)) == "5 * *"


def test_structured_day_and_months_reach_the_day_pattern() -> None:
    # C2.3
    c = Cadence.of("quarterly", day_of_month=8, months=["jan", "apr", "jul", "oct"])
    assert day_pattern_for(c) == "8 1,4,7,10 *"


def test_cadence_stating_no_day_emits_todays_pattern() -> None:
    # C2.4 — the no-op guarantee at the day-pattern level.
    assert day_pattern_for(Cadence.of("weekly")) == "* * 1"
    assert day_pattern_for(Cadence.of("monthly")) == "1 * *"
    assert day_pattern_for(Cadence.of("quarterly")) == "1 1,4,7,10 *"
    assert day_pattern_for(Cadence.of("daily")) == "* * *"


def test_structured_cadence_does_not_move_the_time_of_day() -> None:
    # C2.5 — a cadence part must never influence the slot.
    stated = cron_for(Cadence.of("monthly", day_of_month=5), "board-package")
    plain = cron_for(Cadence.of("monthly"), "board-package")
    assert _time_of_day(stated) == _time_of_day(plain) == slot_for("board-package")


def test_wakes_reads_the_same_cadence_object_as_the_schedule() -> None:
    # C5.1 / FR-016 — ONE source of frequency, not two implementations that agree today.
    # A cadence's day parts must not change how often it is budgeted for.
    for c in (
        Cadence.of("weekly", days_of_week=["tue"]),
        Cadence.of("monthly", day_of_month=5),
        Cadence.of("quarterly", day_of_month=8, months=["jan", "apr", "jul", "oct"]),
    ):
        assert wakes_per_active_month(c) == wakes_per_active_month(Cadence(frequency=c.frequency))
    assert wakes_per_active_month(Cadence.of("weekly", days_of_week=["mon", "wed", "fri"])) == 12


# --- pre-018 behaviour, pinned (feature 018) ---------------------------------
#
# Captured before `Cadence` exists. These two assert what the string cadence produces today, so the
# structured form can be shown to preserve it for cadences that state no day (C5.3) and so a change
# to budget weighting cannot pass unnoticed (C5.1).


def test_string_cadence_day_patterns_are_unchanged() -> None:
    # C5.3 anchor. Note `tue` already resolves to day-of-week 2 — the weekday case was always
    # representable; what was missing is the planner emitting it.
    assert day_pattern_for("weekly") == "* * 1"
    assert day_pattern_for("tue") == "* * 2"
    assert day_pattern_for("tuesday") == "* * 2"
    assert day_pattern_for("mon,wed,fri") == "* * 1,3,5"
    assert day_pattern_for("monthly") == "1 * *"
    assert day_pattern_for("quarterly") == "1 1,4,7,10 *"


def test_wake_counts_are_unchanged() -> None:
    # C5.1 anchor: budget weighting must not drift when the cadence type changes.
    assert wakes_per_active_month(None) is None
    assert wakes_per_active_month("daily") == 30
    assert wakes_per_active_month("weekly") == 4
    assert wakes_per_active_month("biweekly") == 2
    assert wakes_per_active_month("monthly") == 1
    assert wakes_per_active_month("quarterly") == 1
    assert wakes_per_active_month("mon,wed,fri") == 12


# --- timezone resolution (feature 017 / ADR-038) -----------------------------
#
# Resolution goes through the ENUMERATED zone set, never through a ZoneInfo() lookup. ZoneInfo
# resolves by filesystem, so it inherits the host's case sensitivity: "europe/helsinki" resolves on
# a case-insensitive filesystem and not on a case-sensitive one, and it keeps whatever casing it was
# handed rather than canonicalising. The same brief would then emit two different bundles on two
# machines — the salted-hash() failure of feature 015 in different clothes.


def test_resolve_timezone_accepts_a_canonical_zone() -> None:
    # C1.1
    assert resolve_timezone("Europe/Helsinki") == "Europe/Helsinki"
    assert resolve_timezone("UTC") == "UTC"


def test_resolve_timezone_canonicalises_casing_and_ignores_surrounding_space() -> None:
    # C1.2 / C1.3 — recoverable intent is accepted, not rejected.
    assert resolve_timezone("europe/helsinki") == "Europe/Helsinki"
    assert resolve_timezone("EUROPE/HELSINKI") == "Europe/Helsinki"
    assert resolve_timezone("  Europe/Helsinki  ") == "Europe/Helsinki"


def test_resolve_timezone_preserves_non_title_case_database_entries() -> None:
    # C1.8. The canonical spelling is the SET'S OWN MEMBER, never a string transformation. A
    # "capitalise each segment" implementation passes every test written against Region/City names
    # and silently mangles these — which are real database entries.
    assert resolve_timezone("Etc/GMT-3") == "Etc/GMT-3"
    assert resolve_timezone("etc/gmt-3") == "Etc/GMT-3"
    assert resolve_timezone("US/Eastern") == "US/Eastern"
    assert resolve_timezone("us/eastern") == "US/Eastern"


def test_resolve_timezone_matches_the_enumerated_set_not_the_filesystem() -> None:
    # C1.4 / FR-013 — host-independence asserted as a property, not trusted to the implementation.
    # Every accepted value must be a member of available_timezones() exactly as returned; a
    # filesystem-backed lookup would accept names this set does not contain.
    zones = available_timezones()
    for candidate in ("Europe/Helsinki", "europe/helsinki", "us/eastern", "etc/gmt-3"):
        assert resolve_timezone(candidate) in zones


def test_resolve_timezone_rejects_an_unknown_zone_naming_the_value() -> None:
    # C1.5 — unrecoverable intent. The message must carry the offending value.
    for bad in ("Europe/Helsinky", "+03:00", "Mars/Olympus", ""):
        with pytest.raises(ValueError) as excinfo:
            resolve_timezone(bad)
        assert bad.strip() in str(excinfo.value) or not bad.strip()


def test_resolve_timezone_accepts_database_entries_that_are_not_region_city() -> None:
    # C1.6 — the recognition set is the database, not a curated subset of it. "EET" is a real
    # entry; an implementation that required a "/" would reject it.
    assert resolve_timezone("EET") == "EET"


# --- timezone: the default, pinned (feature 017) -----------------------------
#
# Before feature 017 nothing in the suite asserted the emitted timezone at ANY level — a grep for
# "timezone" across tests/ and validators/ returned nothing. The regression guarantee for a brief
# that states no zone (FR-004 / SC-003) therefore rested on an unasserted constant. These two land
# first, before the brief field exists, so that guarantee has something under it.


def test_derive_routines_default_timezone_is_utc() -> None:
    # C4.1 anchor, dataclass level.
    routines = derive_routines(
        [
            _task("signal-scan", "Signal scan", recurrence=Cadence.coerce("mon,wed,fri")),
            _task("board-package", "Monthly board package", recurrence=Cadence.coerce("monthly")),
        ]
    )
    assert [r.timezone for r in routines] == [DEFAULT_TIMEZONE, DEFAULT_TIMEZONE]
    assert DEFAULT_TIMEZONE == "UTC"


def test_rendered_routine_block_declares_utc_by_default() -> None:
    # C4.1 anchor, emitted-artifact level. The dataclass default and the rendered YAML are two
    # different things to get wrong; pin both.
    config = CompanyConfig(
        **_full_config_kwargs(
            tasks=[
                _task("signal-scan", "Signal scan", recurrence=Cadence.coerce("mon,wed,fri")),
                _task(
                    "board-package", "Monthly board package", recurrence=Cadence.coerce("monthly")
                ),
            ]
        )
    )
    data = YAML(typ="safe").load(render_files(config)[".paperclip.yaml"])
    zones = [t["timezone"] for r in data["routines"].values() for t in r["triggers"]]
    assert zones == ["UTC", "UTC"]


# --- timezone: a stated zone binds (feature 017, US1) ------------------------


def _scheduled_tasks() -> list[TaskDefinition]:
    return [
        _task("signal-scan", "Signal scan", recurrence=Cadence.coerce("mon,wed,fri")),
        _task("board-package", "Monthly board package", recurrence=Cadence.coerce("monthly")),
    ]


def _zones_in(yaml_text: str) -> list[str]:
    data = YAML(typ="safe").load(yaml_text)
    return [t["timezone"] for r in data["routines"].values() for t in r["triggers"]]


def _rendered_with_timezone(zone: str | None) -> str:
    brief = CompanyBrief(**_brief_kwargs(routine_timezone=zone))
    config = CompanyConfig(**_full_config_kwargs(tasks=_scheduled_tasks(), brief=brief))
    return render_files(config)[".paperclip.yaml"]


def test_stated_timezone_reaches_every_routine() -> None:
    # C3.1 / C3.2 / SC-001 — all routines, one zone, none left on the default.
    zones = _zones_in(_rendered_with_timezone("Europe/Helsinki"))
    assert zones == ["Europe/Helsinki", "Europe/Helsinki"]
    assert DEFAULT_TIMEZONE not in zones


def test_absent_timezone_still_emits_the_default() -> None:
    # C3.3 / FR-004.
    assert _zones_in(_rendered_with_timezone(None)) == ["UTC", "UTC"]


def test_timezone_does_not_move_any_cron_field() -> None:
    # C3.4 / FR-010 / FR-011. This is the guard that keeps feature 017 inside its scope: the
    # zone changes, the schedule does not. A change to the spread or the day pattern breaks it.
    def _crons(zone: str | None) -> list[str]:
        data = YAML(typ="safe").load(_rendered_with_timezone(zone))
        return [t["cronExpression"] for r in data["routines"].values() for t in r["triggers"]]

    assert _crons("Europe/Helsinki") == _crons(None)


def test_timezone_does_not_change_the_advisory_findings() -> None:
    # C4.4 — the three routine checks are keyed on cron and objectives, never on the zone.
    def _warnings(zone: str | None) -> list[str]:
        brief = CompanyBrief(**_brief_kwargs(routine_timezone=zone))
        config = CompanyConfig(**_full_config_kwargs(tasks=_scheduled_tasks(), brief=brief))
        captured: list[str] = []
        render_files(config, warn=captured.append)
        return captured

    assert _warnings("Europe/Helsinki") == _warnings(None)


def test_bundle_with_no_recurring_task_emits_no_timezone() -> None:
    # C3.5 — a stated zone with nothing to schedule changes nothing.
    brief = CompanyBrief(**_brief_kwargs(routine_timezone="Europe/Helsinki"))
    files = render_files(CompanyConfig(**_full_config_kwargs(brief=brief)))
    assert "routines:" not in files[".paperclip.yaml"]
    assert "Europe/Helsinki" not in files[".paperclip.yaml"]


def test_stated_timezone_renders_identically_across_processes() -> None:
    """C4.5 / SC-006 — cross-process determinism of the RENDERED schedule, not just the resolver.

    A separate interpreter is the point. ``available_timezones()`` returns a set, and set
    iteration order over strings depends on the per-process hash salt; a canonicalisation that
    picked a member by iteration rather than by exact casefold key would agree with itself all
    through this suite — one process, one salt — and still emit differently on a real run. That
    is the same trap ``slot_for``'s subprocess guard exists for.

    Asserting only ``resolve_timezone`` here would be narrower than the contract, which is about
    the emitted schedule.
    """
    script = (
        "import pathlib, sys;"
        "root = pathlib.Path.cwd();"
        "sys.path.insert(0, str(root / 'tests'));"
        "from paperclip_blueprints.models.input import CompanyBrief;"
        "from paperclip_blueprints.models.output import CompanyConfig;"
        "from paperclip_blueprints.models.task import TaskDefinition;"
        "from paperclip_blueprints.renderers.render import render_files;"
        "from test_models import _brief_kwargs, _full_config_kwargs;"
        "t = lambda s, c: TaskDefinition(slug=s, name=s, project='launch-v1', assignee='cto',"
        " objective='o', completion_criteria=['done'], recurrence=c);"
        "brief = CompanyBrief(**_brief_kwargs(routine_timezone='europe/helsinki'));"
        "cfg = CompanyConfig(**_full_config_kwargs("
        " tasks=[t('signal-scan', 'mon,wed,fri'), t('board-package', 'monthly')], brief=brief));"
        "y = render_files(cfg)['.paperclip.yaml'];"
        "print([l.strip() for l in y.splitlines()"
        " if 'cronExpression' in l or 'timezone' in l])"
    )
    runs = {
        subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            check=True,
            cwd=pathlib.Path(__file__).resolve().parent.parent,
        ).stdout
        for _ in range(3)
    }
    assert len(runs) == 1, "the rendered schedule differed between interpreter processes"
    (only,) = runs
    assert "Europe/Helsinki" in only and "cronExpression" in only


# --- render: one task set, recurring flagged, routines keyed off real slug ---


def test_recurring_task_renders_routine_block_and_recurring_flag() -> None:
    config = CompanyConfig(
        **_full_config_kwargs(
            tasks=[
                _task("ship", "Ship"),
                _task("signal-scan", "Signal scan", recurrence=Cadence.coerce("mon,wed,fri")),
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
    # SC-002 / C2.6: an unchanged brief must regenerate byte-identically.
    def _yaml() -> str:
        config = CompanyConfig(
            **_full_config_kwargs(
                tasks=[
                    _task("signal-scan", "Scan", recurrence=Cadence.coerce("daily")),
                    _task("board-package", "Board", recurrence=Cadence.coerce("monthly")),
                ]
            )
        )
        return render_files(config)[".paperclip.yaml"]

    assert _yaml() == _yaml()


# --- S15 routines closure ----------------------------------------------------


def test_s15_clean_when_routines_match_recurring_tasks() -> None:
    config = CompanyConfig(
        **_full_config_kwargs(
            tasks=[
                _task("ship", "Ship"),
                _task("signal-scan", "Signal scan", recurrence=Cadence.coerce("weekly")),
            ]
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
    consumer_slug: str,
    producer_slug: str,
    cadence: str | Cadence,
    *,
    declare: bool = True,
    name_in_prose: bool = False,
) -> tuple[TaskDefinition, TaskDefinition]:
    """A consumer/producer pair, with the dependency declared, described in prose, or both."""
    producer = _task(producer_slug, producer_slug.replace("-", " ").title(), recurrence=cadence)
    consumer = TaskDefinition(
        slug=consumer_slug,
        name=consumer_slug.replace("-", " ").title(),
        project="launch-v1",
        assignee="cto",
        objective=(
            f"Summarise the output of the {producer_slug} task from today."
            if name_in_prose
            # How a planner actually writes it: the dependency is described, never named. This
            # is what produced ZERO findings on a real bundle containing the inversion.
            else "Assemble the current portfolio from the latest verified register entries."
        ),
        completion_criteria=["done"],
        recurrence=Cadence.coerce(cadence),
        depends_on=[producer_slug] if declare else [],
    )
    return consumer, producer


def _earlier_first(a: str, b: str) -> tuple[str, str]:
    """Order two slugs so the first has the earlier derived slot."""
    return (a, b) if slot_for(a) <= slot_for(b) else (b, a)


def test_declared_dependency_scheduled_before_its_producer_warns() -> None:
    # C3.1 — the ordering finding, now keyed on the declaration.
    early, late = _earlier_first("alpha-recap", "signal-scan")
    consumer, producer = _consumer_producer(early, late, "daily")
    warnings = _ordering(consumer, producer)
    assert warnings, "a consumer scheduled at or before its producer must be reported"
    assert consumer.slug in warnings[0] and producer.slug in warnings[0]


def test_dependency_finding_fires_without_the_producer_named_in_prose() -> None:
    # C3.2 — THE point of feature 018. The objective never mentions the producer, exactly as a
    # real generated objective does not; the declaration carries the relationship instead.
    early, late = _earlier_first("alpha-recap", "signal-scan")
    consumer, producer = _consumer_producer(early, late, "daily", name_in_prose=False)
    assert producer.slug not in consumer.objective
    assert _ordering(consumer, producer), "the declaration must be the signal, not the prose"


def test_prose_reference_without_a_declaration_produces_nothing() -> None:
    # C3.3 — proves the textual path is DELETED, not dormant. A leftover prose fallback would
    # satisfy every other test in this file while quietly restoring two signals for one fact.
    early, late = _earlier_first("alpha-recap", "signal-scan")
    consumer, producer = _consumer_producer(early, late, "daily", declare=False, name_in_prose=True)
    assert producer.slug in consumer.objective
    assert _ordering(consumer, producer) == []


def test_consumer_scheduled_after_its_producer_is_not_warned() -> None:
    # C3.4 — the healthy case.
    early, late = _earlier_first("alpha-recap", "signal-scan")
    consumer, producer = _consumer_producer(late, early, "daily")
    assert _ordering(consumer, producer) == []


def test_ordering_is_checked_across_intersecting_day_patterns() -> None:
    # C4.1 — a daily consumer of a weekly producer DOES meet it, on the producer's day. Feature
    # 015 skipped this pair because the patterns differ; that is the cross-cadence dependency
    # the equality gate could not see.
    daily_slug, weekly_slug = "alpha-recap", "signal-scan"
    if slot_for(daily_slug) > slot_for(weekly_slug):
        daily_slug, weekly_slug = weekly_slug, daily_slug
    producer = _task(weekly_slug, "Producer", recurrence=Cadence.of("weekly"))
    consumer = TaskDefinition(
        slug=daily_slug,
        name="Consumer",
        project="launch-v1",
        assignee="cto",
        objective="o",
        completion_criteria=["done"],
        recurrence=Cadence.of("daily"),
        depends_on=[weekly_slug],
    )
    assert _ordering(consumer, producer)


def test_ordering_is_not_checked_across_disjoint_schedules() -> None:
    # C4.2 / FR-015 — no shared firing day, so no well-defined "before".
    producer = _task(
        "signal-scan", "Producer", recurrence=Cadence.of("weekly", days_of_week=["thu"])
    )
    consumer = TaskDefinition(
        slug="alpha-recap",
        name="Consumer",
        project="launch-v1",
        assignee="cto",
        objective="o",
        completion_criteria=["done"],
        recurrence=Cadence.of("weekly", days_of_week=["tue"]),
        depends_on=["signal-scan"],
    )
    assert _ordering(consumer, producer) == []


def test_dependency_on_an_unknown_task_is_reported() -> None:
    # C3.5
    consumer = TaskDefinition(
        slug="alpha-recap",
        name="Consumer",
        project="launch-v1",
        assignee="cto",
        objective="o",
        completion_criteria=["done"],
        recurrence=Cadence.of("daily"),
        depends_on=["ghost-task"],
    )
    findings = [w for w in _warnings_for(consumer) if "ghost-task" in w]
    assert findings, "a dependency on a task that does not exist must be reported"


def test_dependency_on_a_non_recurring_task_produces_no_ordering_finding() -> None:
    # C3.7 — a non-recurring producer has no trigger to be "before".
    producer = _task("ship", "Ship")  # not recurring
    consumer = TaskDefinition(
        slug="alpha-recap",
        name="Consumer",
        project="launch-v1",
        assignee="cto",
        objective="o",
        completion_criteria=["done"],
        recurrence=Cadence.of("daily"),
        depends_on=["ship"],
    )
    assert _ordering(consumer, producer) == []


def test_dependency_cycle_terminates_and_reports_once() -> None:
    # C3.6 / FR-013 — mutual dependency must not loop.
    a = TaskDefinition(
        slug="alpha-recap",
        name="A",
        project="launch-v1",
        assignee="cto",
        objective="o",
        completion_criteria=["done"],
        recurrence=Cadence.of("daily"),
        depends_on=["signal-scan"],
    )
    b = TaskDefinition(
        slug="signal-scan",
        name="B",
        project="launch-v1",
        assignee="cto",
        objective="o",
        completion_criteria=["done"],
        recurrence=Cadence.of("daily"),
        depends_on=["alpha-recap"],
    )
    findings = _ordering(a, b)
    # Exactly one direction can be "at or before" the other; the pair must not loop ordouble-report.
    assert len(findings) == 1


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
    daily = _budget_for(
        "cto", _task("scan", "Scan", recurrence=Cadence.coerce("daily"), assignee="cto")
    )
    quarterly = _budget_for(
        "cto", _task("scan", "Scan", recurrence=Cadence.coerce("quarterly"), assignee="cto")
    )
    assert daily > quarterly


def test_an_agents_busiest_cadence_sets_its_cap() -> None:
    # An agent driven by both a daily and a quarterly routine must be funded for the daily one.
    both = _budget_for(
        "cto",
        _task("scan", "Scan", recurrence=Cadence.coerce("daily"), assignee="cto"),
        _task("review", "Review", recurrence=Cadence.coerce("quarterly"), assignee="cto"),
    )
    daily_only = _budget_for(
        "cto", _task("scan", "Scan", recurrence=Cadence.coerce("daily"), assignee="cto")
    )
    assert both == daily_only


# --- soft warning: a split scheduled activity (same cadence + assignee) ------


def _warnings_for(*tasks: TaskDefinition) -> list[str]:
    config = CompanyConfig(**_full_config_kwargs(tasks=list(tasks)))
    captured: list[str] = []
    render_files(config, warn=captured.append)
    return captured


def test_same_cadence_same_assignee_routines_warn() -> None:
    warnings = _warnings_for(
        _task("scan-landscape", "Scan", recurrence=Cadence.coerce("mon,wed,fri"), assignee="cto"),
        _task(
            "log-signal-patterns", "Log", recurrence=Cadence.coerce("mon,wed,fri"), assignee="cto"
        ),
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
    # C5.5 — every finding is advisory; none converts a passing bundle into a failing one.
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
                _task("signal-scan", "Scan", recurrence=Cadence.coerce("daily"), assignee="cto"),
                _task("board-package", "Board", recurrence=Cadence.coerce("daily"), assignee="ceo"),
            ]
        )
    )
    files = render_files(config)
    assert not any(x.startswith("S15") for x in check_schema_shape(config, files))


def test_same_cadence_different_assignee_routines_do_not_warn() -> None:
    warnings = _warnings_for(
        _task("scan-landscape", "Scan", recurrence=Cadence.coerce("mon,wed,fri"), assignee="cto"),
        _task("board-package", "Board", recurrence=Cadence.coerce("mon,wed,fri"), assignee="ceo"),
    )
    assert not any("split into multiple recurring" in w for w in warnings)


def test_depends_on_is_not_emitted_into_any_bundle_artifact() -> None:
    """C5.4 — the dependency is generation-internal.

    The target platform has no dependency primitive to import (ADR-022), so emitting one would
    invent a field the importer ignores. It exists to drive the ordering check and stops there.
    """
    consumer = TaskDefinition(
        slug="alpha-recap",
        name="Alpha Recap",
        project="launch-v1",
        assignee="cto",
        objective="o",
        completion_criteria=["done"],
        recurrence=Cadence.of("daily"),
        depends_on=["signal-scan"],
    )
    producer = _task("signal-scan", "Signal scan", recurrence=Cadence.of("daily"))
    files = render_files(CompanyConfig(**_full_config_kwargs(tasks=[consumer, producer])))
    for path, content in files.items():
        assert "depends_on" not in content, f"{path} leaked the internal dependency field"
        assert "dependsOn" not in content, f"{path} leaked the internal dependency field"
