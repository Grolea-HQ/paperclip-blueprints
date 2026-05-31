"""project_generator — a PROJECT.md description + success condition (Sonnet)."""

from __future__ import annotations

from ..config import STRUCTURAL_MODEL
from ..models.company import CompanyDefinition
from ..models.org_plan import ProjectStub
from ..models.project import ProjectDefinition
from .client import GenerationError, LLMClient, parse_json_response, render_prompt

_SYSTEM = "You write Paperclip project briefs. Follow the instructions exactly."


def generate_project(
    stub: ProjectStub,
    company: CompanyDefinition,
    client: LLMClient,
    *,
    model: str | None = None,
) -> ProjectDefinition:
    """Generate the PROJECT.md content for one planned project."""
    prompt = render_prompt(
        "project_generator",
        slug=stub.slug,
        name=stub.name,
        owner=stub.owner,
        we_are=company.we_are,
        north_star=company.north_star,
        constraints=company.constraints,
    )
    raw = client.complete(model=model or STRUCTURAL_MODEL, system=_SYSTEM, user=prompt)
    payload = parse_json_response(raw, what="project")
    try:
        return ProjectDefinition(slug=stub.slug, name=stub.name, owner=stub.owner, **payload)
    except Exception as exc:  # noqa: BLE001
        raise GenerationError(f"project failed validation: {exc}") from exc
