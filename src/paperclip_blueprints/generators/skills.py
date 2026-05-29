"""skill_generator — a SKILL.md capability document (Sonnet, ADR-004)."""

from __future__ import annotations

from ..config import STRUCTURAL_MODEL
from ..models.company import CompanyDefinition
from ..models.skill import SkillDefinition
from .client import GenerationError, LLMClient, parse_json_response, render_prompt

_SYSTEM = "You write Paperclip agent skills. Follow the instructions exactly."


def generate_skill(
    slug: str,
    company: CompanyDefinition,
    used_by: list[str],
    client: LLMClient,
    *,
    model: str | None = None,
) -> SkillDefinition:
    """Generate the SKILL.md content for one skill slug."""
    prompt = render_prompt(
        "skill_generator",
        slug=slug,
        used_by=", ".join(used_by),
        we_are=company.we_are,
        north_star=company.north_star,
        constraints=company.constraints,
    )
    raw = client.complete(model=model or STRUCTURAL_MODEL, system=_SYSTEM, user=prompt)
    payload = parse_json_response(raw, what="skill")
    payload.setdefault("slug", slug)
    try:
        return SkillDefinition(**payload)
    except Exception as exc:  # noqa: BLE001
        raise GenerationError(f"skill failed validation: {exc}") from exc
