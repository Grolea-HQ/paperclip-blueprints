"""task_generator — a TASK.md objective + completion criteria (Sonnet)."""

from __future__ import annotations

from ..config import STRUCTURAL_MODEL
from ..models.company import CompanyDefinition
from ..models.org_plan import TaskStub
from ..models.task import TaskDefinition
from .client import GenerationError, LLMClient, render_prompt, strict_json_schema

_SYSTEM = "You write Paperclip task definitions. Follow the instructions exactly."


def generate_task(
    stub: TaskStub,
    company: CompanyDefinition,
    client: LLMClient,
    *,
    assignee_skills: list[str] | None = None,
    canon: str | None = None,
    model: str | None = None,
) -> TaskDefinition:
    """Generate the TASK.md content for one planned task.

    Args:
        canon: The brief's section-11 operating canon (ADR-037), passed through wholesale
            and unmodified. Load-bearing for a recurring task, whose text is the wake
            instruction that wins over the skill. ``None`` ⇒ the prompt renders exactly
            as it did before.
        assignee_skills: The skill slugs the assignee agent holds. Threaded into the
            prompt (ADR-024) so a task that maps to a skill-governed process references
            the governing skill and defers the how (format/storage/protocol) to it, rather
            than restating — and drifting from — the skill. Especially load-bearing for a
            recurring task, whose text is the wake instruction that wins over the skill.
    """
    prompt = render_prompt(
        "task_generator",
        slug=stub.slug,
        name=stub.name,
        project=stub.project,
        assignee=stub.assignee,
        assignee_skills=assignee_skills or [],
        is_recurring=stub.recurrence is not None,
        we_are=company.we_are,
        north_star=company.north_star,
        operating_canon=canon,
    )
    payload = client.complete_json(
        model=model or STRUCTURAL_MODEL,
        system=_SYSTEM,
        user=prompt,
        what="task",
        schema=strict_json_schema(TaskDefinition, include={"objective", "completion_criteria"}),
    )
    try:
        return TaskDefinition(
            slug=stub.slug,
            name=stub.name,
            project=stub.project,
            assignee=stub.assignee,
            recurrence=stub.recurrence,
            **payload,
        )
    except Exception as exc:  # noqa: BLE001
        raise GenerationError(f"task failed validation: {exc}") from exc
