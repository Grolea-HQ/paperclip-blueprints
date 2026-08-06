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

from ..paperclip_slug import slugify_project_name

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
    use_case_notes: str | None = None
    """Section-7 "Notes if customizing the pattern" prose — the operator's binding
    org-customization channel (explicit roster, headcount cap, which work is scheduled).
    Threaded into org_planner so a stated roster/cadence is honored, not expanded past."""
    hours_per_week: int | None = None
    capital_monthly_eur: int | None = None
    capital_setup_eur: int | None = None
    routine_timezone: str | None = None
    """Section-9 optional IANA timezone (feature 017 / ADR-038) — the zone every generated
    routine's schedule trigger is expressed in. ``None`` ⇒ the emitted default (UTC), so a
    brief that states nothing renders byte-identically to before the field existed.

    Stored **canonicalised**: validated here against the platform's zone database, so the value
    downstream is always a real zone in the database's own spelling and nothing re-validates it.
    An unrecognised value raises rather than falling back — a silent default would schedule the
    whole company hours from where the operator asked, with no signal in the bundle.

    Company-level by construction: ``derive_routines`` takes one zone for all routines, so a
    per-routine divergence is not representable."""
    adapter_preferences: list[str] | None = None
    run_policy_preferences: list[str] | None = None
    """Section-12 optional per-agent run-policy override lines (feature 014 / ADR-034), e.g.
    ``"research-analyst: max turns 8, heartbeat off"``. Free-text, one override per line,
    naming an agent and any of max turns / max concurrent / heartbeat on|off. ``None`` ⇒ the
    role-derived caps stand unchanged. Values are validated here; agent matching happens at
    render time."""
    free_text: str | None = None
    """Section-11 **operating canon** (feature 016 / ADR-037) — the operator's residual
    channel for rules, rubrics, thresholds and classification schemes that no structured
    brief field captures. Its defining property is that **nothing else carries it**: unlike
    a roster directive (which ``org_planner`` materialises into stubs) or a constraint
    (which reaches every generator via ``CompanyDefinition``), canon stated here has no
    other path into the bundle. If it is not threaded, it is gone — silently, because
    nothing downstream knows it existed.

    Consumed by ``identity_generator`` and ``org_planner``, and by the four carriers that
    write procedure: ``skill_generator``, ``agents_generator``, ``task_generator`` and
    ``project_generator``. Threaded **wholesale and unmodified** — read once in
    ``renderers/bundle.py`` and passed through unchanged; never summarised, ranked, or
    selected from per consumer, since a selector is a second place to lose canon silently.

    NOT threaded to souls (procedure is the wrong content for a persona artifact whose
    value depends on brevity), nor to operations/goal-hierarchy (their artifacts do not
    reach a running agent under current import behaviour, ADR-022 — revisit if that
    changes)."""

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

    @field_validator("routine_timezone")
    @classmethod
    def _valid_routine_timezone(cls, v: str | None) -> str | None:
        """Canonicalise the stated zone, or reject the brief (feature 017, FR-006/FR-009).

        Rejecting here rather than at render time is what makes FR-007 true for free: both
        ``generate`` and ``validate`` construct the brief before any Anthropic call or file
        write, so a mistyped zone costs nothing. Local import mirrors the run-policy validator
        below — models depend on renderers only for a pure shared parser, and ``routines``
        imports models only for ``TaskDefinition``, so there is no runtime cycle.
        """
        if v is None:
            return None
        from ..renderers.routines import resolve_timezone

        return resolve_timezone(v)

    @field_validator("run_policy_preferences")
    @classmethod
    def _valid_run_policy_lines(cls, v: list[str] | None) -> list[str] | None:
        """Syntactic validation of run-policy override lines (feature 014, FR-010).

        Rejects a malformed value (non-positive / non-integer turns or concurrency, unknown
        clause or heartbeat token, a line with no clause/agent) and the same reference given
        conflicting values for one field. No agent knowledge here — matching is a render
        concern. Imported locally so the model stays loadable without the renderers package.
        """
        if not v:
            return v
        # Local import (mirrors the KNOWN_PATTERNS pattern) — models depend on renderers only
        # for this pure, shared line parser; no runtime cycle (run_policy imports models only
        # under TYPE_CHECKING).
        from ..renderers.run_policy import parse_run_policy_line

        errors: list[str] = []
        by_ref: dict[str, dict[str, object]] = {}
        for line in v:
            try:
                ref, override = parse_run_policy_line(line)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            prior = by_ref.setdefault(slugify_project_name(ref), {})
            for field in ("max_turns_per_run", "max_concurrent_runs", "heartbeat_enabled"):
                new = getattr(override, field)
                if new is None:
                    continue
                if field in prior and prior[field] != new:
                    errors.append(
                        f"run-policy override for {ref!r} sets {field} to conflicting "
                        f"values ({prior[field]!r} then {new!r})"
                    )
                else:
                    prior[field] = new
        if errors:
            raise ValueError("; ".join(errors))
        return v


def slug_divergence_warning(brief: CompanyBrief) -> str | None:
    """Return a non-blocking warning if ``brief.slug`` differs from ``slugify(name)``.

    Paperclip may key a company/project on the derived ``slugify(name)`` form, and the
    v0.2 deployer reconciles on that same derived form (ADR-013). An operator-set
    ``slug`` that diverges can therefore mis-key on import. This is advisory only:
    divergence is sometimes intended (e.g. a keying-test company whose name and slug
    differ on purpose), so the model stays pure and generation still proceeds — the
    caller (CLI) decides how to surface the string. No printing happens here.

    Args:
        brief: The parsed, validated company brief.

    Returns:
        A human-readable warning naming both values, or ``None`` when they already
        match — or when the name has no derivable ASCII slug (an empty derived form,
        a separate non-ASCII concern the slug module handles with a UUID suffix).
    """
    derived = slugify_project_name(brief.name)
    if not derived or derived == brief.slug:
        return None
    return (
        f"brief slug {brief.slug!r} differs from slugify(name) {derived!r}; "
        "Paperclip may key on the derived form while the deployer reconciles on "
        "slugify(name) — align them unless the divergence is intended."
    )


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
    if (v := _anchored_block(sec.get(7, ""), "Notes if customizing")) is not None:
        data["use_case_notes"] = v
    if (v := _inline_value(sec.get(8, ""), "choice")) is not None:
        data["governance_position"] = v

    s9 = sec.get(9, "")
    data["hours_per_week"] = _to_int(_inline_value(s9, "Hours per week"))
    data["capital_monthly_eur"] = _to_int(_inline_value(s9, "EUR/month"))
    data["capital_setup_eur"] = _to_int(_inline_value(s9, "one-time"))
    data["routine_timezone"] = _inline_value(s9, "Timezone")

    if overrides := _list_items(_anchored_block(sec.get(10, ""), "overrides")):
        data["adapter_preferences"] = overrides
    if (v := _anchored_block(sec.get(11, ""), "other context")) is not None:
        data["free_text"] = v
    if rp := _list_items(_anchored_block(sec.get(12, ""), "overrides")):
        data["run_policy_preferences"] = rp

    data = {k: v for k, v in data.items() if v is not None}

    try:
        return CompanyBrief(**data)
    except ValidationError as exc:
        raise BriefValidationError.from_pydantic(exc) from exc
