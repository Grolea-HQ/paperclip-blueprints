"""Cadence — a task's recurrence, structured (feature 018 / ADR-038 amendment).

Replaces the coarse string token ``recurrence`` carried before. The token could hold a frequency
and, via a weekday list, a day of the week — but nothing else. A brief stating "the 5th of each
quarter month" had nowhere to land, and the failure was not a benign default: an unrecognised
cadence string fell through to the weekly fallback, so ``"monthly on the 5th"`` produced a *weekly
Monday* routine. The contract rewarded discarding information, because discarding the day at least
kept the frequency right.

Structured input has no such path. A ``Cadence`` either validates or is rejected, and coercion of a
legacy string raises rather than defaulting.

**One representation downstream.** A bare string is coerced at the boundary, so every consumer —
the day-pattern emitter and the budget wake-weighting — reads the same object. Two parsers of one
cadence would be two answers to "how often does this run", and a silent divergence between what is
scheduled and what is funded is exactly what the shared vocabulary existed to prevent.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Frequency = Literal["daily", "weekly", "biweekly", "monthly", "quarterly", "yearly"]

# Weekday token -> cron day-of-week (Sun=0 … Sat=6), keyed on the 3-letter prefix so both "mon"
# and "monday" resolve. Shared with the routine emitter's vocabulary by construction.
DOW = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6}
MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

_FREQ_ALIASES = {"annual": "yearly", "annually": "yearly", "fortnightly": "biweekly"}

# Frequencies that a given part may qualify. A part outside its set is a planning error.
_WEEKDAY_FREQUENCIES = {"weekly", "biweekly"}
_MONTHDAY_FREQUENCIES = {"monthly", "quarterly", "yearly"}

# Above this, a day-of-month does not occur in every month the cadence covers.
_SHORTEST_MONTH = 28


def _as_dow(v: int | str) -> int:
    if isinstance(v, int):
        if v not in range(7):
            raise ValueError(f"day of week must be 0–6 (Sun–Sat), got {v}")
        return v
    key = v.strip().lower()[:3]
    if key not in DOW:
        raise ValueError(f"unknown weekday {v!r}")
    return DOW[key]


def _as_month(v: int | str) -> int:
    if isinstance(v, int):
        if v not in range(1, 13):
            raise ValueError(f"month must be 1–12, got {v}")
        return v
    key = v.strip().lower()[:3]
    if key not in MONTHS:
        raise ValueError(f"unknown month {v!r}")
    return MONTHS[key]


class Cadence(BaseModel):
    """How often a recurring task runs, and on which days.

    The day parts are optional: a cadence stating only a frequency behaves exactly as the old
    string token did. What is new is that a stated day now has somewhere to go.
    """

    frequency: Frequency
    days_of_week: list[int] | None = None
    """Cron day-of-week values (Sun=0). Weekly cadences only. Accepts names on input."""
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    """Monthly-or-rarer cadences only."""
    months: list[int] | None = None
    """Month numbers (Jan=1). Quarterly/yearly cadences only. Accepts names on input."""

    @field_validator("frequency", mode="before")
    @classmethod
    def _normalise_frequency(cls, v: object) -> object:
        if isinstance(v, str):
            key = v.strip().lower()
            return _FREQ_ALIASES.get(key, key)
        return v

    @field_validator("days_of_week", mode="before")
    @classmethod
    def _coerce_days(cls, v: object) -> object:
        if v is None or not isinstance(v, list):
            return v
        return sorted({_as_dow(d) for d in v})

    @field_validator("months", mode="before")
    @classmethod
    def _coerce_months(cls, v: object) -> object:
        if v is None or not isinstance(v, list):
            return v
        return sorted({_as_month(m) for m in v})

    @model_validator(mode="after")
    def _parts_match_frequency(self) -> Cadence:
        """Reject a part that cannot qualify the stated frequency.

        A day-of-month on a weekly cadence is not a value to quietly drop — it means the plan
        contradicts itself, and dropping it is how the stated day was lost in the first place.
        """
        if self.days_of_week is not None:
            if not self.days_of_week:
                raise ValueError("days_of_week must state at least one day, or be omitted")
            if self.frequency not in _WEEKDAY_FREQUENCIES:
                raise ValueError(
                    f"days_of_week applies to {sorted(_WEEKDAY_FREQUENCIES)} cadences, "
                    f"not {self.frequency!r}"
                )
        if self.day_of_month is not None and self.frequency not in _MONTHDAY_FREQUENCIES:
            raise ValueError(
                f"day_of_month applies to {sorted(_MONTHDAY_FREQUENCIES)} cadences, "
                f"not {self.frequency!r}"
            )
        if self.months is not None:
            if not self.months:
                raise ValueError("months must state at least one month, or be omitted")
            if self.frequency not in _MONTHDAY_FREQUENCIES:
                raise ValueError(
                    f"months applies to {sorted(_MONTHDAY_FREQUENCIES)} cadences, "
                    f"not {self.frequency!r}"
                )
        return self

    def warnings(self) -> list[str]:
        """Advisory notes about a valid but consequential cadence."""
        if self.day_of_month is not None and self.day_of_month > _SHORTEST_MONTH:
            return [
                f"day {self.day_of_month} of the month does not occur in every month — "
                "this routine will not fire in the short ones"
            ]
        return []

    @classmethod
    def of(
        cls,
        frequency: str,
        *,
        days_of_week: Sequence[int | str] | None = None,
        day_of_month: int | None = None,
        months: Sequence[int | str] | None = None,
    ) -> Cadence:
        """Construct a Cadence from human-readable parts (``"tue"``, ``"jan"``).

        The field types stay strictly numeric so every consumer reads one representation; this
        is the typed door for callers holding names. The model's own validators do the same
        conversion for data arriving as JSON from the planner.
        """
        return cls.model_validate(
            {
                "frequency": frequency,
                "days_of_week": list(days_of_week) if days_of_week is not None else None,
                "day_of_month": day_of_month,
                "months": list(months) if months is not None else None,
            }
        )

    @classmethod
    def coerce(cls, value: object) -> Cadence:
        """Build a Cadence from a structured value or a legacy cadence string.

        Raises:
            ValueError: If a string names no recognisable cadence. There is deliberately no
                fallback — the fallback is what turned an unparseable cadence into a silent
                weekly-Monday routine.
        """
        if isinstance(value, Cadence):
            return value
        if isinstance(value, dict):
            return cls(**value)
        if not isinstance(value, str):
            raise ValueError(f"cannot read a cadence from {type(value).__name__}")

        text = value.strip().lower()
        if not text:
            raise ValueError("cadence is empty")
        normalised = _FREQ_ALIASES.get(text, text)
        if normalised in ("daily", "weekly", "biweekly", "monthly", "quarterly", "yearly"):
            return cls(frequency=normalised)  # type: ignore[arg-type]

        tokens = [t for t in re.split(r"[^a-z]+", text) if t]
        days = sorted({DOW[t[:3]] for t in tokens if t[:3] in DOW})
        if days and all(t[:3] in DOW for t in tokens):
            return cls(frequency="weekly", days_of_week=days)
        raise ValueError(
            f"{value!r} is not a recognisable cadence — state a frequency "
            "(daily/weekly/monthly/quarterly/yearly) or a weekday list (e.g. 'mon,wed,fri'), "
            "and put a day of the month in `day_of_month`"
        )
