"""operations_generator — OPERATIONS.md content (Opus + thinking, ADR-004/008).

Runs after the agents exist (it needs the agent list for routine slots and
cadence). Its anti-drift checks must reproduce every constraint and "we are not"
negation; the bundle validator (US3) enforces that cross-file invariant.
"""

from __future__ import annotations

from typing import Any

from ..config import CONTENT_MODEL
from ..models.company import CompanyDefinition
from ..models.input import CompanyBrief
from ..models.operations import OperationsDefinition
from ..models.org_plan import AgentStub
from ..validators.integrity import schedule_mechanism_claims
from .client import GenerationError, LLMClient, render_prompt, strict_json_schema

_SYSTEM = "You write Paperclip company operations manuals. Follow the instructions exactly."


def generate_operations(
    company: CompanyDefinition,
    brief: CompanyBrief,
    agents: list[AgentStub],
    client: LLMClient,
    *,
    routine_owners: list[str] | None = None,
    model: str | None = None,
) -> OperationsDefinition:
    """Generate the OPERATIONS.md content from the identity and the agent list.

    Args:
        routine_owners: the agent slugs that own recurring work — the one fact this generator
            previously could not see (ADR-044). Routines are derived at render time from tasks
            carrying ``recurrence``, so without this the generator filled its routine slots from
            the agent list alone and described a rhythm nothing would ever trigger. An **empty
            list** means this bundle will carry no routine and is the load-bearing case;
            ``None`` means the caller did not say, and the prompt renders as it did before.

            Threading this does not replace validator I16 — the rule is what closes the class,
            including instances nobody has thought of. This is what makes the rule *clearable*:
            a rule a blind generator cannot satisfy is a permanent rejection, not a regeneration
            trigger, because every re-sample is drawn from the same blind distribution.
    """
    prompt = render_prompt(
        "operations_generator",
        name=company.name,
        north_star=company.north_star,
        we_are=company.we_are,
        we_are_not=company.we_are_not,
        constraints=company.constraints,
        governance_position=brief.governance_position,
        agents=agents,
        routine_owners=routine_owners,
    )

    def _check(payload: dict[str, Any]) -> None:
        """Reject a schedule claim at this call when no routine will exist.

        Only meaningful because of ``routine_owners``: the same check on a blind generator
        would re-sample from a distribution that cannot produce a passing answer. Scoped to the
        zero case, where the claim is unambiguously false — an over-claim alongside real
        routines is a judgement call and is left to the operator.
        """
        if routine_owners is None or routine_owners:
            return
        for field in ("idle_state_protocol", "routine_slots", "phase_model", "reporting_cadence"):
            value = payload.get(field)
            text = " ".join(value) if isinstance(value, list) else str(value or "")
            claims = schedule_mechanism_claims(text)
            if claims:
                raise GenerationError(
                    f"{field} claims {claims} but this company has no recurring work, so the "
                    f"bundle will carry no routine and nothing will fire on a schedule. Write "
                    f"it for agents that act when work reaches them."
                )
        if payload.get("routine_slots"):
            raise GenerationError(
                "routine_slots must be empty: this company has no recurring work, so no "
                "routine will be emitted and no agent has a scheduled slot"
            )

    payload = client.complete_json(
        model=model or CONTENT_MODEL,
        system=_SYSTEM,
        user=prompt,
        what="operations",
        thinking=True,
        schema=strict_json_schema(OperationsDefinition),
        check=_check,
    )
    try:
        return OperationsDefinition(**payload)
    except Exception as exc:  # noqa: BLE001
        raise GenerationError(f"operations failed validation: {exc}") from exc
