"""soul_generator — the 7-section SOUL.md persona (Opus, ADR-004)."""

from __future__ import annotations

from ..config import CONTENT_MODEL
from ..models.agent import AgentSoul
from ..models.company import CompanyDefinition
from .client import GenerationError, LLMClient, render_prompt, strict_json_schema
from .org import AgentStub

_SYSTEM = "You write first-person agent personas. Follow the instructions exactly."


def generate_soul(
    stub: AgentStub,
    company: CompanyDefinition,
    client: LLMClient,
    *,
    model: str | None = None,
) -> AgentSoul:
    """Generate the agent's persona, including the mandatory idle-state belief."""
    prompt = render_prompt(
        "soul_generator",
        name=stub.name,
        title=stub.title,
        north_star=company.north_star,
        we_are=company.we_are,
        we_are_not=company.we_are_not,
        constraints=company.constraints,
    )
    payload = client.complete_json(
        model=model or CONTENT_MODEL,
        system=_SYSTEM,
        user=prompt,
        what="soul",
        thinking=True,
        schema=strict_json_schema(AgentSoul),
    )
    try:
        return AgentSoul(**payload)
    except Exception as exc:  # noqa: BLE001 - includes the idle-state invariant
        raise GenerationError(f"soul failed validation: {exc}") from exc
