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
