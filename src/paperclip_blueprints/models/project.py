"""ProjectDefinition — a projects/<slug>/PROJECT.md content (agentcompanies/v1)."""

from __future__ import annotations

from pydantic import BaseModel


class ProjectDefinition(BaseModel):
    """A starter project: an owner, a one-paragraph summary, and a persistent
    success condition (not a one-off step)."""

    slug: str
    name: str
    owner: str
    summary: str
    success_condition: str
