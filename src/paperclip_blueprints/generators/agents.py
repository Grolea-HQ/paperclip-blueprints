"""agents_generator — the AGENTS.md mandate, assembled into an AgentDefinition (Sonnet).

The agent's place in the org (manager, direct reports, peers) is passed in so the
prompt can populate ``receives_from``/``hands_to`` with real agent slugs. The
Paperclip importer ``role`` is derived structurally: the root (``reports_to is
None``) imports as ``ceo``; every other agent leaves ``role`` unset so the importer
applies its own ``agent`` default (company-portability.ts).
"""

from __future__ import annotations

from ..config import STRUCTURAL_MODEL
from ..models.agent import AgentDefinition, AgentSoul
from ..models.company import CompanyDefinition
from ..models.input import CompanyBrief
from .client import GenerationError, LLMClient, render_prompt, strict_json_schema
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
    manager: str | None = None,
    reports: list[str] | None = None,
    peers: list[str] | None = None,
    single_agent: bool = False,
    canon: str | None = None,
    model: str | None = None,
) -> AgentDefinition:
    """Generate the agent's mandate and assemble the full AgentDefinition.

    Args:
        canon: The brief's section-11 operating canon (ADR-037), passed through wholesale
            and unmodified. Taken as an explicit argument rather than read from ``brief``
            here, so that ``free_text`` has exactly one read site in the orchestrator —
            that single read is what makes "wholesale, no selector" auditable rather than
            merely asserted. ``None`` ⇒ the prompt renders exactly as it did before.
    """
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
        single_agent=single_agent,
        manager=manager,
        reports=reports or [],
        peers=peers or [],
        operating_canon=canon,
    )
    payload = client.complete_json(
        model=model or STRUCTURAL_MODEL,
        system=_SYSTEM,
        user=prompt,
        what="agent mandate",
        schema=strict_json_schema(AgentDefinition, include=_BODY_FIELDS),
    )
    # Keep only the body fields the prompt owns; a missing one is left out so
    # pydantic reports it (surfaced as GenerationError below).
    body = {k: payload[k] for k in _BODY_FIELDS if k in payload}
    # The root agent imports as the CEO; every other agent leaves role unset.
    role = "ceo" if stub.reports_to is None else None
    try:
        return AgentDefinition(
            slug=stub.slug,
            name=stub.name,
            title=stub.title,
            reports_to=stub.reports_to,
            role=role,
            skills=stub.skills,
            soul=soul,
            **body,
        )
    except Exception as exc:  # noqa: BLE001
        raise GenerationError(f"agent mandate failed validation: {exc}") from exc
