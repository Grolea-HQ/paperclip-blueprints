"""CompanyDefinition — the synthesized COMPANY.md content (agentcompanies/v1)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .input import _is_task_shaped


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
    tone: Literal["green", "blue", "purple", "orange", "red", "slate"] = "green"
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

    @field_validator("goals")
    @classmethod
    def _goals_outcome_shaped(cls, v: list[str]) -> list[str]:
        # Failure mode: reject task-shaped goals (single-session work) the LLM
        # emits, using the same heuristic the input gate applies to the brief.
        bad = [g for g in v if _is_task_shaped(g)]
        if bad:
            raise ValueError(
                "COMPANY.md goal is task-shaped; it must be a persistent outcome, "
                f"not a one-off task: {bad!r}"
            )
        return v

    @field_validator("north_star")
    @classmethod
    def _north_star_outcome_shaped(cls, v: str) -> str:
        if _is_task_shaped(v):
            raise ValueError(
                "COMPANY.md north star is task-shaped; it must be a persistent, measurable outcome"
            )
        return v
