"""agents_generator — the AGENTS.md mandate, assembled into an AgentDefinition (Sonnet).

The agent's place in the org (manager, direct reports, peers) is passed in so the
prompt can populate ``receives_from``/``hands_to`` with real agent slugs. The
Paperclip importer ``role`` is derived structurally: the root (``reports_to is
None``) imports as ``ceo``; every other agent leaves ``role`` unset so the importer
applies its own ``agent`` default (company-portability.ts).
"""

from __future__ import annotations

from typing import Any

from ..config import STRUCTURAL_MODEL
from ..models.agent import AgentDefinition, AgentSoul
from ..models.company import CompanyDefinition
from ..models.input import CompanyBrief
from .client import GenerationError, LLMClient, render_prompt, strict_json_schema
from .handoffs import handoff_schema, parse_handoffs
from .org import AgentStub

_SYSTEM = "You write Paperclip agent mandates. Follow the instructions exactly."

# The two fields whose values are agent slugs rather than prose. Everything else the
# prompt produces is free text; these are chosen from a closed set (ADR-043).
_HANDOFF_FIELDS = ("receives_from", "hands_to")

# Body fields the prompt produces; identity fields come from the stub.
_BODY_FIELDS = {
    "mandate",
    "triggers",
    *_HANDOFF_FIELDS,
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
    handoff_targets: list[str] | None = None,
    model: str | None = None,
) -> AgentDefinition:
    """Generate the agent's mandate and assemble the full AgentDefinition.

    Args:
        canon: The brief's section-11 operating canon (ADR-037), passed through wholesale
            and unmodified. Taken as an explicit argument rather than read from ``brief``
            here, so that ``free_text`` has exactly one read site in the orchestrator —
            that single read is what makes "wholesale, no selector" auditable rather than
            merely asserted. ``None`` ⇒ the prompt renders exactly as it did before.
        handoff_targets: the closed set of agent slugs this agent may name in a handoff —
            every other agent in the company (ADR-043). Passed in rather than derived from
            ``manager``/``reports``/``peers``, which are the *adjacent* set: a cross-branch
            agent appears in none of the three, so the wide set cannot be reconstructed
            from them. Empty or ``None`` ⇒ there is no legal target, so the fields are not
            requested at all and both come back empty.
    """
    targets = list(handoff_targets or [])
    # A single-agent company has no legal target; an empty enum has no satisfying value,
    # so the honest expression of "nothing to choose from" is not to ask.
    wants_handoffs = bool(targets) and not single_agent
    body_fields = _BODY_FIELDS if wants_handoffs else _BODY_FIELDS - set(_HANDOFF_FIELDS)

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
        handoff_targets=targets if wants_handoffs else [],
    )

    schema = strict_json_schema(AgentDefinition, include=body_fields)
    if wants_handoffs:
        # The model's own field types are list[str]; replace them with the target/prose
        # split, which is what makes the closed set expressible as an enum at all.
        for field in _HANDOFF_FIELDS:
            schema["properties"][field] = handoff_schema(targets)

    def _check(payload: dict[str, Any]) -> None:
        """Reject an out-of-set target at this call, not at the end of the run.

        Runs on every attempt whether or not the schema above was accepted — see
        ``generators.handoffs`` for why both mechanisms exist and why removing either
        is a real loss.
        """
        for field in _HANDOFF_FIELDS if wants_handoffs else ():
            parse_handoffs(payload.get(field), targets=targets, field=field, owner=stub.slug)

    payload = client.complete_json(
        model=model or STRUCTURAL_MODEL,
        system=_SYSTEM,
        user=prompt,
        what="agent mandate",
        schema=schema,
        check=_check,
    )
    # Keep only the body fields the prompt owns; a missing one is left out so
    # pydantic reports it (surfaced as GenerationError below).
    body = {k: payload[k] for k in body_fields if k in payload}
    if wants_handoffs:
        # Rejoin into the form the templates, renderers and validator I8 already consume.
        for field in _HANDOFF_FIELDS:
            body[field] = parse_handoffs(
                payload.get(field), targets=targets, field=field, owner=stub.slug
            )
    else:
        body["receives_from"] = []
        body["hands_to"] = []
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
