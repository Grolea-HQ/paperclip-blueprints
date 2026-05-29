"""SkillDefinition — a SKILL.md content (agentcompanies/v1)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SkillDefinition(BaseModel):
    """A reusable capability document."""

    slug: str
    name: str
    description: str
    when_to_load: list[str]
    inputs: list[str]
    procedure: list[str]
    outputs: list[str]
    anti_patterns: list[str]
    references: list[str] = Field(default_factory=list)
