"""skill_generator — a SKILL.md capability document (Sonnet, ADR-004)."""

from __future__ import annotations

from ..config import STRUCTURAL_MODEL
from ..models.company import CompanyDefinition
from ..models.skill import SkillDefinition
from .client import GenerationError, LLMClient, render_prompt, strict_json_schema

_SYSTEM = "You write Paperclip agent skills. Follow the instructions exactly."


def generate_skill(
    slug: str,
    company: CompanyDefinition,
    used_by: list[str],
    client: LLMClient,
    *,
    canon: str | None = None,
    model: str | None = None,
) -> SkillDefinition:
    """Generate the SKILL.md content for one skill slug.

    Args:
        canon: The brief's section-11 operating canon (ADR-037), passed through
            wholesale and unmodified. The org planner reads section 11 and mints
            capability slugs from it, so without this the skill named after a rubric is
            written blind to the rubric — a slug carries a name, not a procedure.
            ``None`` ⇒ the prompt renders exactly as it did before.
    """
    prompt = render_prompt(
        "skill_generator",
        slug=slug,
        used_by=", ".join(used_by),
        we_are=company.we_are,
        north_star=company.north_star,
        constraints=company.constraints,
        operating_canon=canon,
    )
    payload = client.complete_json(
        model=model or STRUCTURAL_MODEL,
        system=_SYSTEM,
        user=prompt,
        what="skill",
        schema=strict_json_schema(SkillDefinition, exclude={"slug"}),
    )
    payload.setdefault("slug", slug)
    try:
        return SkillDefinition(**payload)
    except Exception as exc:  # noqa: BLE001
        raise GenerationError(f"skill failed validation: {exc}") from exc
