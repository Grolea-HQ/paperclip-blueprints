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

The cadence→cron translation honors the brief's stated cadence (``mon,wed,fri`` → ``* * 1,3,5``,
``monthly`` → ``1 * *``); the time of day is derived per task by :func:`slot_for`. The **timezone**
is brief-bound (feature 017 / ADR-038): one company-level zone applied to every routine, defaulting
to UTC when the brief states none. Binding the zone changed nothing about *when* in the day a
routine lands — cadence day-patterns and time-of-day derivation are untouched by that feature.

What the brief still does NOT bind: stated clock times, stated days-of-month, and stated ordering
between routines. ``TaskDefinition.recurrence`` cannot hold any of them, so no amount of threading
prose to this module would change the emitted cron; that is the deferred schedule-grammar work
recorded in ADR-038.

The cron string and the ``routines.<slug>`` shape stay **PROVISIONAL** — confirmed only at live
import. Kept in this one module so a live correction is contained.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache
from zoneinfo import available_timezones

from ..models.task import TaskDefinition

# --- timezone (feature 017 / ADR-038) ----------------------------------------

DEFAULT_TIMEZONE = "UTC"
"""Emitted when the brief states no timezone. Named so the dataclass default, the
``derive_routines`` signature and the render call site cannot drift apart."""


@lru_cache(maxsize=1)
def _canonical_by_casefold() -> dict[str, str]:
    """``{casefolded zone name: canonical zone name}`` from the platform's zone database.

    Built once per process (598 zones on a system-tzdata macOS). Cached because it is consulted
    once per run in practice but is cheap to hold and awkward to thread.
    """
    return {name.casefold(): name for name in available_timezones()}


def resolve_timezone(value: str) -> str:
    """Canonicalise an IANA zone name, or reject it.

    Resolution matches against the **enumerated zone set**, never a ``ZoneInfo()`` lookup, and the
    returned spelling is the set's own member rather than any transformation of the input. Both
    choices are load-bearing:

    - ``ZoneInfo`` resolves by filesystem, so it inherits the *host's* case sensitivity.
      ``ZoneInfo("europe/helsinki")`` succeeds on macOS and fails on case-sensitive Linux, and it
      preserves whatever casing it was handed. The same brief would emit ``europe/helsinki`` on one
      machine and ``Europe/Helsinki`` on another — a silent cross-machine divergence of exactly the
      kind ``slot_for`` refuses builtin ``hash()`` to avoid.
    - Canonicalising by string manipulation (title-casing each segment) looks right on
      ``Region/City`` names and mangles the real entries that are not shaped that way —
      ``Etc/GMT-3``, ``US/Eastern``, ``EET``.

    This does **not** make resolution fully deterministic across machines: the installed zone
    database still varies by vintage and source, so a zone present on one machine can be absent on
    another. What it converts is the *failure mode* — divergence surfaces as a rejection naming the
    value, not as a bundle differing in a spelling nobody reads.

    Args:
        value: An IANA zone name in any letter casing, with optional surrounding whitespace.

    Returns:
        The canonical spelling as the zone database holds it.

    Raises:
        ValueError: If the value is not a zone the database recognises. There is no fallback —
            silently defaulting would schedule a whole company hours from where the operator asked,
            with no signal anywhere in the bundle.
    """
    stripped = value.strip()
    canonical = _canonical_by_casefold().get(stripped.casefold())
    if canonical is None:
        raise ValueError(
            f"{stripped!r} is not a known IANA timezone "
            "(expected a zone name such as 'Europe/Helsinki')"
        )
    return canonical


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
# gate stalls until morning anyway, so the small hours buy nothing. The window is applied in the
# routine's timezone, which the brief now binds (feature 017 / ADR-038) — so for a company that
# states its zone, these hours ARE the operator's hours, which is what the rationale always
# claimed. A brief that states no zone still emits UTC, and there the old caveat stands: the
# window means human working hours only for a UTC-ish operator. See ADR-036, ADR-038.
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
    timezone: str = DEFAULT_TIMEZONE
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


def derive_routines(
    tasks: Sequence[TaskDefinition], timezone: str = DEFAULT_TIMEZONE
) -> list[RoutineSpec]:
    """Build a RoutineSpec for each task that carries a ``recurrence`` cadence.

    Routines are keyed off the real task slug (short, stable) and inherit the task's own
    ``assignee`` + ``project`` (so each routine resolves to a real agent and project on import).
    Non-recurring tasks contribute nothing — this is what keeps emission to the genuinely
    scheduled work.

    Args:
        tasks: The bundle's full task set; non-recurring tasks are skipped.
        timezone: The company's zone (feature 017), applied to every routine. One value for the
            whole bundle, which is what makes a per-routine divergence unrepresentable (FR-002).
            Already canonicalised by ``CompanyBrief``; not re-validated here.
    """
    return [
        RoutineSpec(
            slug=t.slug,
            name=t.name,
            assignee=t.assignee,
            project=t.project,
            cron=cron_for(t.recurrence, t.slug),
            timezone=timezone,
        )
        for t in tasks
        if t.recurrence
    ]
