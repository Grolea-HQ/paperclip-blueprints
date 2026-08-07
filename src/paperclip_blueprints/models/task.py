"""TaskDefinition — a tasks/<slug>/TASK.md content (agentcompanies/v1)."""

from __future__ import annotations

from pydantic import BaseModel, field_validator

from .cadence import Cadence


class TaskDefinition(BaseModel):
    """A starter task linked by frontmatter to one project and one assignee agent."""

    slug: str
    name: str
    project: str
    assignee: str
    objective: str
    completion_criteria: list[str]
    recurrence: Cadence | None = None
    """Structured cadence for genuinely schedule-driven standing work (ADR-022 US3; feature 018).
    ``None`` = not recurring (handoff/heartbeat-driven). Set by org_planner, and the single
    source of frequency for both routine emission and budget wake-weighting. A legacy cadence
    string is coerced on input, so one type reaches every consumer."""
    depends_on: list[str] = []
    """Slugs of tasks whose output this task consumes (feature 018). Written by org_planner,
    which knows the relationship because it created the tasks; read by the producer/consumer
    ordering check. Generation-internal — never emitted into a bundle artifact, since the
    target platform has no dependency primitive to import it into (ADR-022)."""

    @field_validator("recurrence", mode="before")
    @classmethod
    def _coerce_recurrence(cls, v: object) -> object:
        return Cadence.coerce(v) if isinstance(v, str) else v

    @field_validator("completion_criteria")
    @classmethod
    def _at_least_one_criterion(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("a task must have at least one completion criterion")
        return v
