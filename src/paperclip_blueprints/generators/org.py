"""org_planner — produce the OrgPlan skeleton (Sonnet, ADR-004 / R-001).

The planner fixes every agent, project, and task slug and all their cross-references
before content fan-out. ``OrgPlan`` and the stub models live in ``models/org_plan.py``
and are re-exported here for callers that import them from the generator.
"""

from __future__ import annotations

from ..config import STRUCTURAL_MODEL
from ..models.company import CompanyDefinition
from ..models.input import CompanyBrief
from ..models.org_plan import AgentStub, OrgPlan, ProjectStub, TaskStub
from .client import GenerationError, LLMClient, parse_json_response, render_prompt

__all__ = [
    "AgentStub",
    "OrgPlan",
    "ProjectStub",
    "TaskStub",
    "generate_org_plan",
    "generate_org",
]

_SYSTEM = "You design Paperclip company org structures. Follow the instructions exactly."


def generate_org_plan(
    brief: CompanyBrief,
    company: CompanyDefinition,
    client: LLMClient,
    *,
    single_agent: bool = False,
    seed: str | None = None,
    model: str | None = None,
) -> OrgPlan:
    """Plan the org skeleton (agents + projects + tasks), fully cross-referenced.

    Args:
        single_agent: when True, the planner returns exactly one owner agent and no
            projects/tasks (the v0.1a size-one path).
        seed: optional pattern-seed context (US2) injected into the prompt.
    """
    prompt = render_prompt(
        "org_planner",
        name=company.name,
        north_star=company.north_star,
        we_are=company.we_are,
        governance_position=brief.governance_position,
        single_agent=single_agent,
        seed=seed,
    )
    raw = client.complete(model=model or STRUCTURAL_MODEL, system=_SYSTEM, user=prompt)
    payload = parse_json_response(raw, what="org plan")
    try:
        plan = OrgPlan(**payload)
    except Exception as exc:  # noqa: BLE001 - pydantic ValidationError or type errors
        raise GenerationError(f"org plan failed validation: {exc}") from exc
    if single_agent and len(plan.agents) != 1:
        raise GenerationError("single-agent org must have exactly one agent")
    return plan


def generate_org(
    brief: CompanyBrief, company: CompanyDefinition, client: LLMClient, *, model: str | None = None
) -> AgentStub:
    """Plan a single-agent org and return its one owner stub (v0.1a convenience)."""
    return generate_org_plan(brief, company, client, single_agent=True, model=model).agents[0]
