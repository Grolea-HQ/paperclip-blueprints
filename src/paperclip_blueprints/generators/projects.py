"""project_generator — a PROJECT.md description + success condition (Sonnet)."""

from __future__ import annotations

from ..config import STRUCTURAL_MODEL
from ..models.company import CompanyDefinition
from ..models.org_plan import ProjectStub
from ..models.project import ProjectDefinition
from .client import GenerationError, LLMClient, render_prompt, strict_json_schema

_SYSTEM = "You write Paperclip project briefs. Follow the instructions exactly."


def generate_project(
    stub: ProjectStub,
    company: CompanyDefinition,
    client: LLMClient,
    *,
    canon: str | None = None,
    model: str | None = None,
) -> ProjectDefinition:
    """Generate the PROJECT.md content for one planned project.

    Args:
        canon: The brief's section-11 operating canon (ADR-037), passed through
            wholesale and unmodified. ``None`` ⇒ the prompt renders exactly as it did
            before.
    """
    prompt = render_prompt(
        "project_generator",
        slug=stub.slug,
        name=stub.name,
        owner=stub.owner,
        we_are=company.we_are,
        north_star=company.north_star,
        constraints=company.constraints,
        operating_canon=canon,
    )
    payload = client.complete_json(
        model=model or STRUCTURAL_MODEL,
        system=_SYSTEM,
        user=prompt,
        what="project",
        schema=strict_json_schema(ProjectDefinition, include={"summary", "success_condition"}),
    )
    try:
        return ProjectDefinition(slug=stub.slug, name=stub.name, owner=stub.owner, **payload)
    except Exception as exc:  # noqa: BLE001
        raise GenerationError(f"project failed validation: {exc}") from exc
