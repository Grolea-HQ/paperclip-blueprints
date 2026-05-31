"""CompanyBrief — the operator's parsed input, and the Markdown brief parser.

The brief mirrors ``examples/input-template.md`` (ADR-003). Parsing reads the
operator's content that appears AFTER each ``**Your ...:**`` anchor, so the
instructional examples that precede the anchors are ignored. Validation enforces
the input-side best-practice rules (goal-as-outcome, anti-drift minimums) without
any Anthropic API call.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ValidationError, field_validator

GovernancePosition = Literal["tight", "balanced", "loose"]

_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_DIGIT_RE = re.compile(r"\d")

# Leading verbs that signal a one-off task rather than a persistent outcome.
_TASK_VERBS = {
    "launch",
    "build",
    "write",
    "create",
    "set",
    "setup",
    "make",
    "ship",
    "design",
    "add",
    "publish",
    "implement",
    "draft",
    "produce",
    "release",
    "develop",
}


def _is_task_shaped(text: str) -> bool:
    """Heuristic: a goal is task-shaped if it leads with a task verb and names no
    measurable threshold (no digit). Conservative — ambiguous goals pass."""
    stripped = text.strip()
    if not stripped:
        return False
    first = re.split(r"[\s,]", stripped.lower(), maxsplit=1)[0]
    return first in _TASK_VERBS and not _DIGIT_RE.search(stripped)


class CompanyBrief(BaseModel):
    """The operator's company brief. Source of truth for the whole bundle."""

    name: str
    slug: str
    description: str
    north_star: str
    goals: list[str]
    we_are: str
    we_are_not: list[str]
    constraints: list[str]
    governance_position: GovernancePosition
    use_case_pattern: str | None = None
    hours_per_week: int | None = None
    capital_monthly_eur: int | None = None
    capital_setup_eur: int | None = None
    adapter_preferences: list[str] | None = None
    free_text: str | None = None

    @field_validator("name", "description", "north_star", "we_are")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must not be empty")
        return v.strip()

    @field_validator("slug")
    @classmethod
    def _slug_shape(cls, v: str) -> str:
        if not _SLUG_RE.match(v):
            raise ValueError("slug must be lowercase-hyphenated (e.g. 'newsletter-press')")
        return v

    @field_validator("description")
    @classmethod
    def _description_word_limit(cls, v: str) -> str:
        if len(v.split()) > 30:
            raise ValueError("one-sentence description must be 30 words or fewer")
        return v

    @field_validator("we_are_not")
    @classmethod
    def _at_least_two_negations(cls, v: list[str]) -> list[str]:
        if len(v) < 2:
            raise ValueError("'we are not' requires at least 2 entries (anti-drift core)")
        return v

    @field_validator("constraints")
    @classmethod
    def _at_least_two_constraints(cls, v: list[str]) -> list[str]:
        if len(v) < 2:
            raise ValueError("at least 2 constraints are required")
        return v

    @field_validator("goals")
    @classmethod
    def _goals_outcome_shaped(cls, v: list[str]) -> list[str]:
        if len(v) < 2:
            raise ValueError("at least 2 goals are required")
        if len(v) > 5:
            raise ValueError("at most 5 goals (2-5 is the typical range)")
        bad = [g for g in v if _is_task_shaped(g)]
        if bad:
            raise ValueError(
                "goal is task-shaped (completable in one session); reshape as a "
                f"persistent outcome: {bad!r}"
            )
        return v

    @field_validator("north_star")
    @classmethod
    def _north_star_outcome_shaped(cls, v: str) -> str:
        if _is_task_shaped(v):
            raise ValueError(
                "north star is task-shaped; it must be a persistent, measurable outcome"
            )
        return v

    @field_validator("use_case_pattern")
    @classmethod
    def _known_use_case_pattern(cls, v: str | None) -> str | None:
        # FR-015: an unrecognized pattern is reported with the available set,
        # not silently ignored. Imported locally so the model stays loadable
        # without importing the patterns package at module load.
        if v is None:
            return v
        from ..patterns import KNOWN_PATTERNS

        if v not in KNOWN_PATTERNS:
            raise ValueError(
                f"unknown use-case pattern {v!r}; available: {', '.join(KNOWN_PATTERNS)}"
            )
        return v


class BriefValidationError(Exception):
    """Raised when a brief fails to parse or validate. Carries all messages."""

    def __init__(self, messages: list[str]) -> None:
        self.messages = messages
        super().__init__("\n".join(f"  - {m}" for m in messages))

    @classmethod
    def from_pydantic(cls, exc: ValidationError) -> BriefValidationError:
        messages = []
        for err in exc.errors():
            loc = ".".join(str(p) for p in err["loc"]) or "(brief)"
            messages.append(f"{loc}: {err['msg']}")
        return cls(messages)


# --- Markdown parsing -------------------------------------------------------

_SECTION_RE = re.compile(r"^##\s+(\d+)\.\s+(.*)$", re.MULTILINE)


def _split_sections(text: str) -> dict[int, str]:
    """Split a brief into ``{section_number: body}``."""
    sections: dict[int, str] = {}
    matches = list(_SECTION_RE.finditer(text))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[int(m.group(1))] = text[start:end].strip()
    return sections


def _is_placeholder(value: str) -> bool:
    s = value.strip()
    return not s or (s.startswith("[") and s.endswith("]"))


def _inline_value(body: str, *keywords: str) -> str | None:
    """Return the value after ``...:**`` on a line matching any keyword."""
    for line in body.splitlines():
        if "**" in line and ":**" in line and any(k.lower() in line.lower() for k in keywords):
            value = line.rsplit(":**", 1)[1].strip()
            return None if _is_placeholder(value) else value
    return None


def _anchored_block(body: str, anchor: str) -> str | None:
    """Return the text after a ``**anchor:**`` line, up to the section end."""
    lines = body.splitlines()
    for idx, line in enumerate(lines):
        if anchor.lower() in line.lower() and ":**" in line:
            tail = line.rsplit(":**", 1)[1].strip()
            rest = "\n".join(lines[idx + 1 :]).strip()
            block = (tail + "\n" + rest).strip() if tail else rest
            return None if _is_placeholder(block) else block
    return None


def _list_items(block: str | None) -> list[str]:
    """Parse numbered or bulleted list items, dropping placeholders."""
    if not block:
        return []
    items: list[str] = []
    for line in block.splitlines():
        s = line.strip()
        m = re.match(r"^(?:\d+\.|[-*])\s+(.*)$", s)
        if m:
            item = m.group(1).strip()
            if not _is_placeholder(item):
                items.append(item)
    return items


def _to_int(value: str | None) -> int | None:
    if value is None:
        return None
    digits = re.sub(r"[^\d]", "", value)
    return int(digits) if digits else None


def parse_brief(markdown: str) -> CompanyBrief:
    """Parse a filled-in brief Markdown document into a validated CompanyBrief.

    Raises:
        BriefValidationError: if any required field is missing/unfilled or any
            validation rule fails. All problems are reported together.
    """
    sec = _split_sections(markdown)

    data: dict[str, Any] = {}
    s1 = sec.get(1, "")
    if (v := _inline_value(s1, "Name")) is not None:
        data["name"] = v
    if (v := _inline_value(s1, "Slug")) is not None:
        data["slug"] = v
    if (v := _inline_value(s1, "One-sentence description", "description")) is not None:
        data["description"] = v

    if (v := _anchored_block(sec.get(2, ""), "north star")) is not None:
        data["north_star"] = v
    if goals := _list_items(_anchored_block(sec.get(3, ""), "goals")):
        data["goals"] = goals
    if (v := _anchored_block(sec.get(4, ""), "we are")) is not None:
        data["we_are"] = v
    if wan := _list_items(_anchored_block(sec.get(5, ""), "we are not")):
        data["we_are_not"] = wan
    if cons := _list_items(_anchored_block(sec.get(6, ""), "constraints")):
        data["constraints"] = cons

    if (v := _inline_value(sec.get(7, ""), "choice")) is not None:
        data["use_case_pattern"] = v
    if (v := _inline_value(sec.get(8, ""), "choice")) is not None:
        data["governance_position"] = v

    s9 = sec.get(9, "")
    data["hours_per_week"] = _to_int(_inline_value(s9, "Hours per week"))
    data["capital_monthly_eur"] = _to_int(_inline_value(s9, "EUR/month"))
    data["capital_setup_eur"] = _to_int(_inline_value(s9, "one-time"))

    if overrides := _list_items(_anchored_block(sec.get(10, ""), "overrides")):
        data["adapter_preferences"] = overrides
    if (v := _anchored_block(sec.get(11, ""), "other context")) is not None:
        data["free_text"] = v

    data = {k: v for k, v in data.items() if v is not None}

    try:
        return CompanyBrief(**data)
    except ValidationError as exc:
        raise BriefValidationError.from_pydantic(exc) from exc
