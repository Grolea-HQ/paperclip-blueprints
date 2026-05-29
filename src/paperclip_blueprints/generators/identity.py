"""identity_generator — CompanyBrief -> CompanyDefinition (COMPANY.md content).

Opus + extended thinking (ADR-004). The prompt instructs the model to return a
fenced JSON block matching CompanyDefinition's fields; this module parses and
validates it.
"""

from __future__ import annotations

import json

from ..config import CONTENT_MODEL
from ..models.company import CompanyDefinition
from ..models.input import CompanyBrief
from .client import GenerationError, LLMClient, extract_fenced_block, render_prompt

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
    raw = client.complete(
        model=model or CONTENT_MODEL, system=_SYSTEM, user=prompt, thinking=True
    )
    return _parse(raw)


def _parse(raw: str) -> CompanyDefinition:
    block = extract_fenced_block(raw, lang="json")
    try:
        payload = json.loads(block)
    except json.JSONDecodeError as exc:
        raise GenerationError(f"identity response was not valid JSON: {exc}") from exc
    try:
        return CompanyDefinition(**payload)
    except Exception as exc:  # noqa: BLE001 - pydantic ValidationError or type errors
        raise GenerationError(f"identity response failed validation: {exc}") from exc
