"""Routine emission (ADR-022, US3) — PROVISIONAL cron, pending live-import confirmation.

Routines are driven by the **tasks**: a task carries a ``recurrence`` cadence (set by org_planner
for genuinely schedule-driven standing work, else ``None``). Each recurring task becomes a
Paperclip Routine — two coordinated pieces:

1. the **existing** ``tasks/<slug>/TASK.md`` is flagged ``recurring: true`` (it keeps its real
   ``assignee`` + ``project`` — the routine runs as that agent, in that project; the importer
   requires the project). There is **no** separate "routine task": one task set, recurring ones
   flagged.
2. a top-level ``.paperclip.yaml`` ``routines.<task-slug>`` block with a ``schedule`` trigger
   (``cronExpression`` + ``timezone``) and concurrency/catch-up policies (defaults
   ``coalesce_if_active`` / ``skip_missed``).

The cadence→cron translation honors the brief's stated cadence (``mon,wed,fri`` → ``0 9 * * 1,3,5``,
``monthly`` → ``0 9 1 * *``). The cron string and the ``routines.<slug>`` shape stay **PROVISIONAL**
— confirmed only at live import. Kept in this one module so a live correction is contained.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from ..models.task import TaskDefinition

# Named cadence -> 09:00 cron (provisional defaults; live import confirms cron validity).
_NAMED_CRON = {
    "daily": "0 9 * * *",
    "weekly": "0 9 * * 1",
    "biweekly": "0 9 * * 1",
    "monthly": "0 9 1 * *",
    "quarterly": "0 9 1 1,4,7,10 *",
    "yearly": "0 9 1 1 *",
    "annual": "0 9 1 1 *",
}
_DEFAULT_CRON = "0 9 * * 1"  # weekly fallback for an unrecognized cadence

# Weekday token -> cron day-of-week (Sun=0 … Sat=6). Keyed on the 3-letter prefix so both
# "mon" and "monday" resolve.
_DOW = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6}


@dataclass(frozen=True)
class RoutineSpec:
    """One routine: the recurring task's identity + its ``.paperclip.yaml`` schedule trigger."""

    slug: str  # == the recurring task's slug (short, stable)
    name: str
    assignee: str
    project: str
    cron: str
    timezone: str = "UTC"
    concurrency_policy: str = "coalesce_if_active"
    catch_up_policy: str = "skip_missed"


def cron_for(cadence: str) -> str:
    """Translate a cadence hint to a cron expression (PROVISIONAL — live import confirms validity).

    Handles the named cadences (daily/weekly/monthly/quarterly/…) and a weekday list
    (``mon,wed,fri`` / ``monday wednesday friday`` → ``0 9 * * 1,3,5``). Unrecognized → weekly.
    """
    c = cadence.strip().lower()
    if c in _NAMED_CRON:
        return _NAMED_CRON[c]
    days = sorted({_DOW[tok[:3]] for tok in re.split(r"[^a-z]+", c) if tok[:3] in _DOW})
    if days:
        return f"0 9 * * {','.join(str(d) for d in days)}"
    return _DEFAULT_CRON


# Wakes per ACTIVE month per named cadence — the months in which the routine runs at all, not
# the calendar average (see budget.wake_weight for why the distinction is load-bearing).
# Monthly-or-rarer cadences all wake exactly once in an active month.
_NAMED_WAKES = {
    "daily": 30,
    "weekly": 4,
    "biweekly": 2,
    "monthly": 1,
    "quarterly": 1,
    "yearly": 1,
    "annual": 1,
}
_DEFAULT_WAKES = 4  # matches the weekly cron fallback for an unrecognized cadence


def wakes_per_active_month(cadence: str | None) -> int | None:
    """How many times a cadence wakes its agent in a month where it runs at all.

    Shares the cadence vocabulary with :func:`cron_for` deliberately: two parsers of the same
    operator-written cadence strings would drift, and a silent divergence between what gets
    scheduled and what gets budgeted is the failure this is meant to prevent.

    Args:
        cadence: A task's ``recurrence`` cadence, or ``None`` for a non-recurring task.

    Returns:
        The wake count, or ``None`` when there is no cadence (an on-demand agent, whose wake
        count is unbounded and unknowable here).
    """
    if cadence is None:
        return None
    c = cadence.strip().lower()
    if c in _NAMED_WAKES:
        return _NAMED_WAKES[c]
    days = {_DOW[tok[:3]] for tok in re.split(r"[^a-z]+", c) if tok[:3] in _DOW}
    if days:
        return len(days) * 4
    return _DEFAULT_WAKES


def derive_routines(tasks: Sequence[TaskDefinition]) -> list[RoutineSpec]:
    """Build a RoutineSpec for each task that carries a ``recurrence`` cadence.

    Routines are keyed off the real task slug (short, stable) and inherit the task's own
    ``assignee`` + ``project`` (so each routine resolves to a real agent and project on import).
    Non-recurring tasks contribute nothing — this is what keeps emission to the genuinely
    scheduled work.
    """
    return [
        RoutineSpec(
            slug=t.slug,
            name=t.name,
            assignee=t.assignee,
            project=t.project,
            cron=cron_for(t.recurrence),
        )
        for t in tasks
        if t.recurrence
    ]
