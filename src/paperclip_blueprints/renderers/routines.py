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

import hashlib
import re
from collections.abc import Sequence
from dataclasses import dataclass

from ..models.task import TaskDefinition

# Named cadence -> day-pattern cron fields (day-of-month, month, day-of-week). The minute and
# hour are NOT part of the cadence: the brief states days and frequencies, never clock times, so
# time-of-day is derived per task by `slot_for` (feature 015). PROVISIONAL, as before.
_NAMED_DAY_PATTERN = {
    "daily": "* * *",
    "weekly": "* * 1",
    "biweekly": "* * 1",
    "monthly": "1 * *",
    "quarterly": "1 1,4,7,10 *",
    "yearly": "1 1 *",
    "annual": "1 1 *",
}
_DEFAULT_DAY_PATTERN = "* * 1"  # weekly fallback for an unrecognized cadence

# --- time-of-day distribution (feature 015) ----------------------------------
#
# Every routine used to be pinned to 09:00, so a brief stating eight cadences produced eight
# routines firing at the same minute. The brief never states clock times, so nothing was
# mis-bound — it was a poor default. Each task now gets a slot derived from its own slug.
#
# The window is a policy default, not a correctness property: work an operator is expected to
# supervise should land during a working day, and an agent that wakes overnight into an approval
# gate stalls until morning anyway, so the small hours buy nothing. NOTE the window is applied in
# the routine's timezone, which is UTC, while the rationale is *human* working hours — those
# coincide only for a UTC-ish operator. See ADR-036.
START_HOUR = 6
END_HOUR = 17
MINUTE_STEP = 5

_HOURS = END_HOUR - START_HOUR + 1  # 12
_MINUTE_SLOTS = 60 // MINUTE_STEP  # 12 → 144 distinct slots


def slot_for(slug: str) -> tuple[int, int]:
    """Derive a task's ``(hour, minute)`` from its slug.

    Uses a ``hashlib`` digest, never the builtin ``hash()``: builtin string hashing is salted
    per interpreter process, so it would emit different schedules on different runs of the same
    brief — and a single-process test suite shares one salt, so no test here would ever catch
    it. Reproducibility across processes is the requirement (FR-003).

    The spread is **probabilistic**, not a guarantee. Over 144 slots, eight routines still
    collide with probability around 19% (hour-only spreading would collide ~95% of the time,
    which is why the minute participates). The guarantee comes from the collision check in
    ``render.py``, which reports whatever residue remains: distribution lowers the incidence,
    detection closes the gap.

    Args:
        slug: The task's slug — the only input, so a task's time does not shift when other
            tasks are added or removed.

    Returns:
        ``(hour, minute)`` with ``START_HOUR <= hour <= END_HOUR`` and ``minute`` on a
        ``MINUTE_STEP`` boundary.
    """
    digest = hashlib.blake2b(slug.encode("utf-8"), digest_size=8).digest()
    value = int.from_bytes(digest, "big")
    # Independent parts of the digest drive hour and minute so the two do not correlate.
    hour = START_HOUR + (value % _HOURS)
    minute = ((value // _HOURS) % _MINUTE_SLOTS) * MINUTE_STEP
    return hour, minute


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


def day_pattern_for(cadence: str) -> str:
    """The cron day fields (day-of-month, month, day-of-week) a cadence binds to.

    This is the part the brief actually states, and it is unchanged by feature 015. Split out
    so the collision checks can compare two routines' day patterns without re-parsing cron.
    """
    c = cadence.strip().lower()
    if c in _NAMED_DAY_PATTERN:
        return _NAMED_DAY_PATTERN[c]
    days = sorted({_DOW[tok[:3]] for tok in re.split(r"[^a-z]+", c) if tok[:3] in _DOW})
    if days:
        return f"* * {','.join(str(d) for d in days)}"
    return _DEFAULT_DAY_PATTERN


def cron_for(cadence: str, slug: str) -> str:
    """Translate a cadence hint + task slug to a cron expression (PROVISIONAL).

    The **day pattern** comes from the cadence, exactly as before (``mon,wed,fri`` → ``* * 1,3,5``,
    ``monthly`` → ``1 * *``). The **time of day** comes from :func:`slot_for`, because the brief
    states days and frequencies but never clock times — so pinning every routine to one hour was
    a default, not a binding. Unrecognized cadence → weekly day pattern.
    """
    hour, minute = slot_for(slug)
    return f"{minute} {hour} {day_pattern_for(cadence)}"


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
            cron=cron_for(t.recurrence, t.slug),
        )
        for t in tasks
        if t.recurrence
    ]
