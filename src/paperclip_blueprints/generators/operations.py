"""operations_generator — OPERATIONS.md content (Opus + thinking, ADR-004/008).

Runs after the agents exist (it needs the agent list for routine slots and
cadence). Its anti-drift checks must reproduce every constraint and "we are not"
negation; the bundle validator (US3) enforces that cross-file invariant.
"""

from __future__ import annotations

from ..config import CONTENT_MODEL
from ..models.company import CompanyDefinition
from ..models.input import CompanyBrief
from ..models.operations import OperationsDefinition
from ..models.org_plan import AgentStub
from .client import GenerationError, LLMClient, render_prompt, strict_json_schema

_SYSTEM = "You write Paperclip company operations manuals. Follow the instructions exactly."


def generate_operations(
    company: CompanyDefinition,
    brief: CompanyBrief,
    agents: list[AgentStub],
    client: LLMClient,
    *,
    model: str | None = None,
) -> OperationsDefinition:
    """Generate the OPERATIONS.md content from the identity and the agent list."""
    prompt = render_prompt(
        "operations_generator",
        name=company.name,
        north_star=company.north_star,
        we_are=company.we_are,
        we_are_not=company.we_are_not,
        constraints=company.constraints,
        governance_position=brief.governance_position,
        agents=agents,
    )
    payload = client.complete_json(
        model=model or CONTENT_MODEL,
        system=_SYSTEM,
        user=prompt,
        what="operations",
        thinking=True,
        schema=strict_json_schema(OperationsDefinition),
    )
    try:
        return OperationsDefinition(**payload)
    except Exception as exc:  # noqa: BLE001
        raise GenerationError(f"operations failed validation: {exc}") from exc
