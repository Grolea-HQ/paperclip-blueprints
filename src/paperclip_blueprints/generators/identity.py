"""identity_generator — CompanyBrief -> CompanyDefinition (COMPANY.md content).

Opus + extended thinking (ADR-004). The prompt instructs the model to return a
fenced JSON block matching CompanyDefinition's fields; this module parses and
validates it.
"""

from __future__ import annotations

from ..config import CONTENT_MODEL
from ..models.company import CompanyDefinition
from ..models.input import CompanyBrief
from .client import GenerationError, LLMClient, render_prompt, strict_json_schema

_SYSTEM = "You generate Paperclip company identity content. Follow the instructions exactly."


def generate_identity(
    brief: CompanyBrief, client: LLMClient, *, model: str | None = None
) -> CompanyDefinition:
    """Synthesize the COMPANY.md identity content from the brief.

    Raises:
        GenerationError: if the response is not parseable JSON or fails validation.
    """
    prompt = render_prompt(
        "identity_generator",
        name=brief.name,
        slug=brief.slug,
        description=brief.description,
        north_star=brief.north_star,
        goals=brief.goals,
        we_are=brief.we_are,
        we_are_not=brief.we_are_not,
        constraints=brief.constraints,
        governance_position=brief.governance_position,
        free_text=brief.free_text,
    )
    payload = client.complete_json(
        model=model or CONTENT_MODEL,
        system=_SYSTEM,
        user=prompt,
        what="identity",
        thinking=True,
        schema=strict_json_schema(CompanyDefinition),
    )
    try:
        return CompanyDefinition(**payload)
    except Exception as exc:  # noqa: BLE001 - pydantic ValidationError or type errors
        raise GenerationError(f"identity response failed validation: {exc}") from exc
