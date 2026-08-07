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
from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache
from zoneinfo import available_timezones

from ..models.cadence import Cadence
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
# Defaults for parts a cadence does not state — chosen to reproduce the pre-018 day patterns
# exactly, so a cadence stating only a frequency emits what it always did.
DEFAULT_DAY_OF_WEEK = 1  # Monday
DEFAULT_DAY_OF_MONTH = 1
DEFAULT_QUARTER_MONTHS = (1, 4, 7, 10)
DEFAULT_YEAR_MONTHS = (1,)

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


def day_pattern_for(cadence: Cadence | str) -> str:
    """The cron day fields (day-of-month, month, day-of-week) a cadence binds to.

    Every part the cadence states is honoured; every part it omits falls back to what the coarse
    token produced before feature 018, so a cadence stating only a frequency emits an unchanged
    pattern. A bare string is coerced (and raises if unrecognisable) — there is no silent default.
    """
    c = Cadence.coerce(cadence)
    if c.frequency == "daily":
        return "* * *"
    if c.frequency in ("weekly", "biweekly"):
        days = c.days_of_week or [DEFAULT_DAY_OF_WEEK]
        return f"* * {','.join(str(d) for d in days)}"
    dom = c.day_of_month or DEFAULT_DAY_OF_MONTH
    if c.frequency == "monthly":
        return f"{dom} * *"
    months = c.months or (
        DEFAULT_QUARTER_MONTHS if c.frequency == "quarterly" else DEFAULT_YEAR_MONTHS
    )
    return f"{dom} {','.join(str(m) for m in months)} *"


def _field_values(field: str) -> set[int] | None:
    """A cron day-field as a value set, or ``None`` when unrestricted (``*``)."""
    if field == "*":
        return None
    return {int(part) for part in field.split(",")}


def schedules_can_intersect(day_pattern_a: str, day_pattern_b: str) -> bool:
    """Whether two day patterns can ever fire on the same day.

    Feature 015 compared two routines' ordering only when their day patterns were *identical*,
    reasoning that "before" is otherwise undefined. That is true across genuinely disjoint
    schedules and false across overlapping ones: a daily consumer of a weekly producer does meet
    it, every week, on the producer's day. Equality under-catches the cross-cadence dependency.

    Disjointness is only claimed where it is provable — an unrestricted field constrains nothing,
    and a restricted day-of-month against a restricted day-of-week is treated as intersecting,
    since cron ORs the two and any day-of-month lands on any weekday across enough months.

    Args:
        day_pattern_a: The cron day fields (day-of-month, month, day-of-week) of one schedule.
        day_pattern_b: The same for the other.

    Returns:
        ``False`` only when the two provably share no firing day.
    """
    dom_a, month_a, dow_a = (_field_values(f) for f in day_pattern_a.split())
    dom_b, month_b, dow_b = (_field_values(f) for f in day_pattern_b.split())

    if month_a is not None and month_b is not None and not (month_a & month_b):
        return False
    if dom_a is not None and dom_b is not None and not (dom_a & dom_b):
        return False
    if dow_a is not None and dow_b is not None and not (dow_a & dow_b):
        return False
    return True


def cron_for(cadence: Cadence | str, slug: str) -> str:
    """Translate a cadence + task slug to a cron expression (PROVISIONAL).

    The **day pattern** comes from the cadence, including any day it states (feature 018). The
    **time of day** comes from :func:`slot_for` — no cadence part influences it.
    """
    hour, minute = slot_for(slug)
    return f"{minute} {hour} {day_pattern_for(cadence)}"


# Wakes per ACTIVE month per frequency — the months in which the routine runs at all, not the
# calendar average (see budget.wake_weight for why the distinction is load-bearing).
_WAKES_PER_FREQUENCY = {
    "daily": 30,
    "weekly": 4,
    "biweekly": 2,
    "monthly": 1,
    "quarterly": 1,
    "yearly": 1,
}


def wakes_per_active_month(cadence: Cadence | str | None) -> int | None:
    """How many times a cadence wakes its agent in a month where it runs at all.

    Reads the **same** :class:`Cadence` the schedule reads. That is the point: two parsers of one
    cadence are two answers to "how often does this run", and a silent divergence between what
    gets scheduled and what gets budgeted is the failure this shared reading prevents.

    A cadence's stated days change *which* days it fires on, and for a weekly cadence how many
    times per week; they never change its frequency class.

    Args:
        cadence: A task's cadence, or ``None`` for a non-recurring task.

    Returns:
        The wake count, or ``None`` when there is no cadence (an on-demand agent, whose wake
        count is unbounded and unknowable here).
    """
    if cadence is None:
        return None
    c = Cadence.coerce(cadence)
    if c.frequency in ("weekly", "biweekly") and c.days_of_week:
        return _WAKES_PER_FREQUENCY[c.frequency] * len(c.days_of_week)
    return _WAKES_PER_FREQUENCY[c.frequency]


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
