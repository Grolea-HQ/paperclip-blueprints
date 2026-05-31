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

    @field_validator("completion_criteria")
    @classmethod
    def _at_least_one_criterion(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("a task must have at least one completion criterion")
        return v
