"""org_planner — produce the single owner agent stub (Sonnet, ADR-004).

The stub is a transient intermediate (not a bundle artifact), so it lives here
rather than in ``models/``.
"""

from __future__ import annotations

from pydantic import BaseModel

from ..config import STRUCTURAL_MODEL
from ..models.company import CompanyDefinition
from ..models.input import CompanyBrief
from .client import GenerationError, LLMClient, parse_json_response, render_prompt

_SYSTEM = "You design Paperclip company org structures. Follow the instructions exactly."


class AgentStub(BaseModel):
    """The org_planner's output: enough to drive per-agent generation."""

    slug: str
    name: str
    title: str
    reports_to: str | None
    skills: list[str]


def generate_org(
    brief: CompanyBrief, company: CompanyDefinition, client: LLMClient, *, model: str | None = None
) -> AgentStub:
    """Plan a single-agent org: the top-level owner who owns the north star."""
    prompt = render_prompt(
        "org_planner",
        name=company.name,
        north_star=company.north_star,
        we_are=company.we_are,
    )
    raw = client.complete(model=model or STRUCTURAL_MODEL, system=_SYSTEM, user=prompt)
    payload = parse_json_response(raw, what="org plan")
    try:
        stub = AgentStub(**payload)
    except Exception as exc:  # noqa: BLE001
        raise GenerationError(f"org plan failed validation: {exc}") from exc
    if stub.reports_to is not None:
        raise GenerationError("single-agent org owner must have reports_to = null")
    if len(stub.skills) != 1:
        raise GenerationError("single-agent owner must have exactly one primary skill")
    return stub
