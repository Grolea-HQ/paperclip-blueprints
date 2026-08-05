"""SkillDefinition — a SKILL.md content (agentcompanies/v1)."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator

_LEADING_ORDINAL = re.compile(r"^\s*\(?\d{1,2}[.)]\s+")
"""A step's own ordinal prefix: ``1. ``, ``2) `` or ``(3) ``.

Requires the ``.``/``)`` separator, so prose that legitimately opens with a number —
"2 business days must pass" — is left alone.
"""


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

    @field_validator("procedure")
    @classmethod
    def _strip_leading_ordinals(cls, steps: list[str]) -> list[str]:
        """Drop a step's own ordinal prefix; the template numbers the list.

        ``skill_md.j2`` renders the procedure as a numbered markdown list via
        ``loop.index``. A model that also writes "1. " into the step text produces
        ``1. 1. INTAKE AND DOMAIN GATE`` — in every procedure step of every skill.

        Normalised here rather than in the template so it holds for any consumer of the
        model, and holds whether or not the prompt is obeyed. The prompt asks for
        unnumbered steps as well; this is the half that does not depend on compliance.
        """
        return [_LEADING_ORDINAL.sub("", step).strip() for step in steps]
