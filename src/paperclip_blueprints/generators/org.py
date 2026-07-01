"""org_planner — produce the OrgPlan skeleton (Sonnet, ADR-004 / R-001).

The planner fixes every agent, project, and task slug and all their cross-references
before content fan-out. ``OrgPlan`` and the stub models live in ``models/org_plan.py``
and are re-exported here for callers that import them from the generator.
"""

from __future__ import annotations

import logging

from ..config import STRUCTURAL_MODEL
from ..models.company import CompanyDefinition
from ..models.input import CompanyBrief
from ..models.org_plan import AgentStub, OrgPlan, ProjectStub, TaskStub
from ..paperclip_slug import dedupe_slug, slugify_project_name
from .client import GenerationError, LLMClient, render_prompt, strict_json_schema

_log = logging.getLogger(__name__)

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
        free_text=brief.free_text,
        use_case_notes=brief.use_case_notes,
    )
    payload = client.complete_json(
        model=model or STRUCTURAL_MODEL,
        system=_SYSTEM,
        user=prompt,
        what="org plan",
        schema=strict_json_schema(OrgPlan),
    )
    try:
        plan = OrgPlan(**payload)
    except Exception as exc:  # noqa: BLE001 - pydantic ValidationError or type errors
        raise GenerationError(f"org plan failed validation: {exc}") from exc
    if single_agent and len(plan.agents) != 1:
        raise GenerationError("single-agent org must have exactly one agent")
    return _normalize_project_slugs(plan)


def _normalize_project_slugs(plan: OrgPlan) -> OrgPlan:
    """Force every project slug to Paperclip's ``slugify(name)`` and rewrite task refs.

    Paperclip creates projects with ``urlKey = slugify(name)`` and resolves a task's
    ``project:`` reference against that key (ADR-013). The planner lets the model pick
    arbitrary slugs, so we re-key projects to the slugified name (de-duplicating
    collisions) and rewrite every ``task.project`` to match, then rebuild the plan so
    its cross-reference validator re-runs. No-op when there are no projects.
    """
    if not plan.projects:
        return plan
    used: set[str] = set()
    mapping: dict[str, str] = {}
    new_projects: list[ProjectStub] = []
    for project in plan.projects:
        base = slugify_project_name(project.name)
        if not base:
            # All-non-ASCII name: Paperclip would append an unpredictable UUID, so we
            # cannot match it offline. Keep the planner's slug and warn.
            _log.warning(
                "project %r name %r did not yield an ASCII slug; keeping %r — tasks "
                "may not associate on import",
                project.slug,
                project.name,
                project.slug,
            )
            base = project.slug
        new_slug = dedupe_slug(base, used)
        mapping[project.slug] = new_slug
        new_projects.append(project.model_copy(update={"slug": new_slug}))
    new_tasks = [
        task.model_copy(update={"project": mapping.get(task.project, task.project)})
        for task in plan.tasks
    ]
    # Rebuild via the constructor so OrgPlan's cross-reference validator re-runs.
    return OrgPlan(agents=plan.agents, projects=new_projects, tasks=new_tasks)


def generate_org(
    brief: CompanyBrief, company: CompanyDefinition, client: LLMClient, *, model: str | None = None
) -> AgentStub:
    """Plan a single-agent org and return its one owner stub (v0.1a convenience)."""
    return generate_org_plan(brief, company, client, single_agent=True, model=model).agents[0]
