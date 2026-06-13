"""Render a CompanyConfig into the in-memory bundle file map.

Bodies come from Jinja templates in ``templates/``; YAML frontmatter is produced by
:func:`dump_frontmatter` so quoting/order match the reference companies. Returns a
``{relative_path: content}`` map — nothing touches disk here (the atomic write lives
in ``bundle.py``).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from ..models.agent import AgentDefinition
from ..models.company import CompanyDefinition
from ..models.output import CompanyConfig
from ..models.project import ProjectDefinition
from ..models.skill import SkillDefinition
from ..models.task import TaskDefinition
from .budget import allocate_budgets
from .frontmatter import dump_frontmatter

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
    undefined=StrictUndefined,
    autoescape=False,
)


def _render(template: str, **ctx: object) -> str:
    return _env.get_template(template).render(**ctx)


def render_company_md(company: CompanyDefinition) -> str:
    """Render COMPANY.md (frontmatter + body) from identity content alone.

    Shared by the full bundle and ``blueprints preview`` (US3), which emits only
    this file.
    """
    frontmatter = dump_frontmatter(
        {
            "schema": "agentcompanies/v1",
            "name": company.name,
            "description": company.description,
            "version": company.version,
            "tags": company.tags,
            "goals": company.goals,
            "metadata": {
                # `mono` is the company monogram letter, derived from the name
                # (matches the reference companies: Newsletter→N, Agency→A, …).
                "paperclip": {"tone": company.tone, "mono": company.name[0].upper()},
                "sources": [{"kind": "url"}],
            },
        },
        flow_seq_keys={"tags"},
    )
    return frontmatter + "\n" + _render("company_md.j2", company=company)


def _agent_frontmatter(agent: AgentDefinition) -> str:
    return dump_frontmatter(
        {
            "schema": "agentcompanies/v1",
            "slug": agent.slug,
            "name": agent.name,
            "title": agent.title,
            "reportsTo": agent.reports_to,
            "skills": agent.skills,
        },
        flow_seq_keys={"skills"},
    )


def _skill_frontmatter(skill: SkillDefinition) -> str:
    return dump_frontmatter(
        {
            "schema": "agentcompanies/v1",
            "slug": skill.slug,
            "name": skill.name,
            "description": skill.description,
        }
    )


def _project_frontmatter(project: ProjectDefinition) -> str:
    # `description` is the entity description Paperclip imports (it reads the
    # frontmatter field, never the body — ADR-013); the rich body stays authoring
    # content. Field order follows companies-spec §9 (name, description, owner).
    return dump_frontmatter(
        {
            "schema": "agentcompanies/v1",
            "slug": project.slug,
            "name": project.name,
            "description": project.summary,
            "owner": project.owner,
        }
    )


def _task_frontmatter(task: TaskDefinition) -> str:
    return dump_frontmatter(
        {
            "schema": "agentcompanies/v1",
            "slug": task.slug,
            "name": task.name,
            "project": task.project,
            "assignee": task.assignee,
        }
    )


def _role_bucket(agent: AgentDefinition, is_manager: bool) -> str:
    """Classify an agent's role for TOOLS.md customization (R-008)."""
    if agent.reports_to is None:
        return "owner"
    if is_manager:
        return "manager"
    text = (agent.title + " " + " ".join(agent.skills)).lower()
    if any(
        k in text for k in ("engineer", "developer", " dev", "qa", "coding", "platform", "tool")
    ):
        return "engineering"
    return "generic"


def render_files(
    config: CompanyConfig, *, warn: Callable[[str], None] | None = None
) -> dict[str, str]:
    """Render every file of a bundle (single or full) to a path→content map.

    Args:
        config: The assembled bundle to render.
        warn: Optional sink for advisory warnings (e.g. a budget pool too small
            for the org size). Defaults to discarding them.
    """
    manager_slugs = {a.reports_to for a in config.agents if a.reports_to is not None}

    # Per-agent budgets (ADR-012): derive a budgetMonthlyCents from the company
    # cap, scaled by governance and weighted by the same role buckets TOOLS.md
    # uses. Empty when no cap is stated. ``role_by_slug`` is built in agent order
    # so the allocation is deterministic.
    role_by_slug = {a.slug: _role_bucket(a, a.slug in manager_slugs) for a in config.agents}
    allocation = allocate_budgets(
        role_by_slug, config.brief.governance_position, config.brief.capital_monthly_eur
    )
    if allocation.warning is not None and warn is not None:
        warn(allocation.warning)
    capital_set = config.brief.capital_monthly_eur is not None

    base = {
        "brief": config.brief,
        "company": config.company,
        "agents": config.agents,
        "projects": config.projects,
        "tasks": config.tasks,
        "skills": config.skills,
        "license_kind": config.license_kind,
        "budgets": allocation.cents,
    }

    files: dict[str, str] = {
        ".paperclip.yaml": _render("paperclip_yaml.j2", **base),
        "COMPANY.md": render_company_md(config.company),
        "README.md": _render("readme_md.j2", **base),
        "LICENSE.txt": _render("license_txt.j2", **base),
    }

    if config.operations is not None:
        files["OPERATIONS.md"] = _render(
            "operations_md.j2",
            company=config.company,
            operations=config.operations,
            capital_set=capital_set,
        )
        files["PROJECT-INVENTORY.md"] = _render(
            "project_inventory_md.j2", company=config.company, projects=config.projects
        )
    for agent in config.agents:
        actx = {
            "brief": config.brief,
            "company": config.company,
            "agent": agent,
            "soul": agent.soul,
            "role_bucket": _role_bucket(agent, agent.slug in manager_slugs),
        }
        adir = f"agents/{agent.slug}"
        files[f"{adir}/AGENTS.md"] = (
            _agent_frontmatter(agent) + "\n" + _render("agents_md.j2", **actx)
        )
        files[f"{adir}/SOUL.md"] = _render("soul_md.j2", **actx)
        files[f"{adir}/HEARTBEAT.md"] = _render("heartbeat_md.j2", **actx)
        files[f"{adir}/TOOLS.md"] = _render("tools_md.j2", **actx)

    for skill in config.skills:
        files[f"skills/{skill.slug}/SKILL.md"] = (
            _skill_frontmatter(skill) + "\n" + _render("skill_md.j2", skill=skill)
        )

    for project in config.projects:
        files[f"projects/{project.slug}/PROJECT.md"] = (
            _project_frontmatter(project) + "\n" + _render("project_md.j2", project=project)
        )

    for task in config.tasks:
        files[f"tasks/{task.slug}/TASK.md"] = (
            _task_frontmatter(task) + "\n" + _render("task_md.j2", task=task)
        )

    return files
