"""goal_hierarchy_generator — reason the north-star → sub-goals tree (Sonnet, ADR-025).

Runs AFTER the per-agent fan-out (alongside operations) because owner reasoning needs each
``AgentDefinition.mandate`` — which only exists once agents are generated. The LLM decides
only *owner* + *level* per goal; the tree shape (single root = north star, every goal
nested under it) is built deterministically here, so a flaky or absent model can never
produce an orphan or a second root. Unknown/ambiguous owners fall back to the org root at
company level, and a single-agent company skips the LLM entirely (the lone agent owns
everything).
"""

from __future__ import annotations

from typing import Any

from ..config import STRUCTURAL_MODEL
from ..models.agent import AgentDefinition
from ..models.company import CompanyDefinition
from ..models.goal import GoalDefinition, GoalHierarchy, GoalLevel
from ..models.input import CompanyBrief
from ..paperclip_slug import dedupe_slug, slugify_project_name
from .client import GenerationError, LLMClient, render_prompt

_SYSTEM = "You assign ownership for Paperclip company goals. Follow the instructions exactly."
_ROOT_SLUG = "north-star"

# Raw structured-output schema: one {owner, level} per goal, in order.
_ASSIGN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["assignments"],
    "properties": {
        "assignments": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["owner", "level"],
                "properties": {
                    "owner": {"type": "string"},
                    "level": {"type": "string", "enum": ["company", "team", "agent"]},
                },
            },
        }
    },
}


def _org_root(agents: list[AgentDefinition]) -> AgentDefinition:
    """The single org-root agent (the CEO); ``reports_to is None``."""
    return next(a for a in agents if a.reports_to is None)


def _assignments(
    company: CompanyDefinition,
    brief: CompanyBrief,
    agents: list[AgentDefinition],
    client: LLMClient,
    *,
    model: str | None,
) -> list[dict[str, str]] | None:
    """Ask the model for one ``{owner, level}`` per goal, or ``None`` to fall back.

    Returns ``None`` — signalling the deterministic company-level/CEO default — for a
    single-agent company (no reasoning needed) or when the call fails or returns the wrong
    number of assignments. Never raises: a goal hierarchy must always be produced.
    """
    if len(agents) < 2:
        return None
    prompt = render_prompt(
        "goal_hierarchy_generator",
        north_star=company.north_star,
        goals=company.goals,
        agents=agents,
    )
    try:
        payload = client.complete_json(
            model=model or STRUCTURAL_MODEL,
            system=_SYSTEM,
            user=prompt,
            what="goal hierarchy",
            schema=_ASSIGN_SCHEMA,
        )
    except GenerationError:
        return None
    assignments = payload.get("assignments")
    if not isinstance(assignments, list) or len(assignments) != len(company.goals):
        return None
    return assignments


def _resolve_owner(
    assignment: dict[str, str] | None,
    agent_slugs: set[str],
    root_slug: str,
) -> tuple[str, GoalLevel]:
    """Resolve one goal's ``(owner, level)``, coercing anything unusable to CEO/company.

    A goal stays company-level/CEO-owned when the assignment is absent (fallback /
    single-agent), names ``"company"``, or names an owner not in the org.
    """
    if assignment is None:
        return root_slug, "company"
    owner = assignment.get("owner", "")
    level = assignment.get("level", "")
    if owner not in agent_slugs:  # "company" or a hallucinated slug
        return root_slug, "company"
    resolved_level: GoalLevel = "team" if level == "team" else "agent"
    return owner, resolved_level


def generate_goal_hierarchy(
    company: CompanyDefinition,
    brief: CompanyBrief,
    agents: list[AgentDefinition],
    client: LLMClient,
    *,
    model: str | None = None,
) -> GoalHierarchy:
    """Build the reasoned north-star → sub-goals tree for a company.

    Args:
        company: The identity content (north star + flat goals).
        brief: The operator's brief (carried for symmetry with the other generators).
        agents: The generated agents, WITH mandates — the owner-reasoning input.
        client: The LLM client (Sonnet call for multi-agent owner assignment).
        model: Optional model override.

    Returns:
        A validated ``GoalHierarchy``: one root (the north star, owned by the org root),
        each brief goal nested under it with a reasoned owner and level. Structurally valid
        by construction; the LLM never controls the tree shape, only owner/level.
    """
    root_agent = _org_root(agents)
    agent_slugs = {a.slug for a in agents}
    root = GoalDefinition(
        slug=_ROOT_SLUG,
        title="North star",
        description=company.north_star,
        level="company",
        parent=None,
        owner=root_agent.slug,
    )

    assignments = _assignments(company, brief, agents, client, model=model)
    used = {_ROOT_SLUG}
    children: list[GoalDefinition] = []
    for i, goal in enumerate(company.goals):
        assignment = assignments[i] if assignments is not None else None
        owner, level = _resolve_owner(assignment, agent_slugs, root_agent.slug)
        slug = dedupe_slug(slugify_project_name(goal) or f"goal-{i + 1}", used)
        children.append(
            GoalDefinition(
                slug=slug,
                title=goal,
                description=goal,
                level=level,
                parent=_ROOT_SLUG,
                owner=owner,
            )
        )

    return GoalHierarchy(goals=[root, *children])
