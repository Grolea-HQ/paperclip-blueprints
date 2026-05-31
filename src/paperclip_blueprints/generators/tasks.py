"""task_generator — a TASK.md objective + completion criteria (Sonnet)."""

from __future__ import annotations

from ..config import STRUCTURAL_MODEL
from ..models.company import CompanyDefinition
from ..models.org_plan import TaskStub
from ..models.task import TaskDefinition
from .client import GenerationError, LLMClient, parse_json_response, render_prompt

_SYSTEM = "You write Paperclip task definitions. Follow the instructions exactly."


def generate_task(
    stub: TaskStub,
    company: CompanyDefinition,
    client: LLMClient,
    *,
    model: str | None = None,
) -> TaskDefinition:
    """Generate the TASK.md content for one planned task."""
    prompt = render_prompt(
        "task_generator",
        slug=stub.slug,
        name=stub.name,
        project=stub.project,
        assignee=stub.assignee,
        we_are=company.we_are,
        north_star=company.north_star,
    )
    raw = client.complete(model=model or STRUCTURAL_MODEL, system=_SYSTEM, user=prompt)
    payload = parse_json_response(raw, what="task")
    try:
        return TaskDefinition(
            slug=stub.slug,
            name=stub.name,
            project=stub.project,
            assignee=stub.assignee,
            **payload,
        )
    except Exception as exc:  # noqa: BLE001
        raise GenerationError(f"task failed validation: {exc}") from exc
