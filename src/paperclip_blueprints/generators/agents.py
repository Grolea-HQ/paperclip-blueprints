"""agents_generator — the AGENTS.md mandate, assembled into an AgentDefinition (Sonnet)."""

from __future__ import annotations

from ..config import STRUCTURAL_MODEL
from ..models.agent import AgentDefinition, AgentSoul
from ..models.company import CompanyDefinition
from ..models.input import CompanyBrief
from .client import GenerationError, LLMClient, parse_json_response, render_prompt
from .org import AgentStub

_SYSTEM = "You write Paperclip agent mandates. Follow the instructions exactly."

# Body fields the prompt produces; identity fields come from the stub.
_BODY_FIELDS = {
    "mandate",
    "triggers",
    "receives_from",
    "hands_to",
    "deliverables",
    "can_approve",
    "must_escalate",
    "escalation_text",
    "tools_role_specific",
}


def generate_agent(
    stub: AgentStub,
    company: CompanyDefinition,
    brief: CompanyBrief,
    soul: AgentSoul,
    client: LLMClient,
    *,
    model: str | None = None,
) -> AgentDefinition:
    """Generate the agent's mandate and assemble the full AgentDefinition."""
    prompt = render_prompt(
        "agents_generator",
        slug=stub.slug,
        name=stub.name,
        title=stub.title,
        north_star=company.north_star,
        we_are=company.we_are,
        we_are_not=company.we_are_not,
        constraints=company.constraints,
        governance_position=brief.governance_position,
        capital_monthly_eur=brief.capital_monthly_eur,
    )
    raw = client.complete(model=model or STRUCTURAL_MODEL, system=_SYSTEM, user=prompt)
    payload = parse_json_response(raw, what="agent mandate")
    # Keep only the body fields the prompt owns; a missing one is left out so
    # pydantic reports it (surfaced as GenerationError below).
    body = {k: payload[k] for k in _BODY_FIELDS if k in payload}
    try:
        return AgentDefinition(
            slug=stub.slug,
            name=stub.name,
            title=stub.title,
            reports_to=stub.reports_to,
            role="ceo",  # v0.1a: the lone agent is the CEO; v0.1b derives from reports_to
            skills=stub.skills,
            soul=soul,
            **body,
        )
    except Exception as exc:  # noqa: BLE001
        raise GenerationError(f"agent mandate failed validation: {exc}") from exc
