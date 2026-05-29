"""CompanyDefinition — the synthesized COMPANY.md content (agentcompanies/v1)."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class CompanyDefinition(BaseModel):
    """Identity content for COMPANY.md, synthesized from the brief.

    Preserves the brief's load-bearing distinctions: the north star, the goals,
    and the ``we_are`` / ``we_are_not`` / ``constraints`` framing (FR-006).
    """

    name: str
    description: str
    goals: list[str]
    we_are: str
    we_are_not: list[str]
    north_star: str
    constraints: list[str]
    tone: str = "green"
    mono: str = "N"
    version: str = "1.0.0"
    tags: list[str] = Field(default_factory=list)

    @field_validator("we_are_not")
    @classmethod
    def _at_least_two_negations(cls, v: list[str]) -> list[str]:
        if len(v) < 2:
            raise ValueError("COMPANY.md must keep at least 2 'we are not' entries")
        return v

    @field_validator("constraints")
    @classmethod
    def _at_least_two_constraints(cls, v: list[str]) -> list[str]:
        if len(v) < 2:
            raise ValueError("COMPANY.md must keep at least 2 constraints")
        return v
