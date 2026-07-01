"""TaskDefinition — a tasks/<slug>/TASK.md content (agentcompanies/v1)."""

from __future__ import annotations

from pydantic import BaseModel, field_validator


class TaskDefinition(BaseModel):
    """A starter task linked by frontmatter to one project and one assignee agent."""

    slug: str
    name: str
    project: str
    assignee: str
    objective: str
    completion_criteria: list[str]
    recurrence: str | None = None
    """Cadence hint for genuinely schedule-driven standing work (ADR-022, US3): a normalized
    token (``daily``/``weekly``/``monthly``/``quarterly``) or a comma-separated lowercase
    weekday list (e.g. ``mon,wed,fri``). ``None`` = not recurring (handoff/heartbeat-driven).
    Set by org_planner (whole-org structural decision); drives routine emission."""

    @field_validator("completion_criteria")
    @classmethod
    def _at_least_one_criterion(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("a task must have at least one completion criterion")
        return v
