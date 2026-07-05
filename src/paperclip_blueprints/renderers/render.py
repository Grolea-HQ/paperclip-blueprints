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
from .adapter import assign_adapters, parse_model_preferences
from .budget import allocate_budgets
from .frontmatter import dump_frontmatter
from .routines import RoutineSpec, derive_routines

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
    fields: dict[str, object] = {
        "schema": "agentcompanies/v1",
        "slug": task.slug,
        "name": task.name,
        "project": task.project,
        "assignee": task.assignee,
    }
    # A scheduled task is flagged recurring (ADR-022 US3); its schedule rides `.paperclip.yaml`
    # routines.<slug>. One task set — recurring ones are flagged, never duplicated.
    if task.recurrence:
        fields["recurring"] = True
    return dump_frontmatter(fields)


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


def _routine_cadence_smells(routines: list[RoutineSpec]) -> list[str]:
    """Soft smell-detector (ADR-022 US3): two recurring tasks on the SAME cadence AND assignee
    are likely one scheduled activity split into two (the org_planner one-cadence rule).

    Advisory only — surfaced via the ``warn`` sink, NEVER a validation error: a genuinely
    doubled cadence on one owner is legitimate, so the operator judges. Grouped by
    ``(cron, assignee)`` (not cron alone — two owners can share a cadence without a smell).
    """
    groups: dict[tuple[str, str], list[str]] = {}
    for r in routines:
        groups.setdefault((r.cron, r.assignee), []).append(r.slug)
    return [
        f"routines {sorted(slugs)} share cadence {cron!r} and assignee {assignee!r} — likely one "
        "scheduled activity split into multiple recurring tasks; consider folding into one "
        "recurring task (org_planner one-cadence rule)"
        for (cron, assignee), slugs in groups.items()
        if len(slugs) > 1
    ]


# Concrete format/storage tokens that constitute restating a skill's "how" (ADR-024). Kept
# to *concrete* nouns (file formats, structural elements, path words) — NOT meta-words like
# "format"/"storage"/"protocol", so the recommended deferential phrasing ("produce its
# prescribed output, format, and storage per the <skill> skill") does NOT trip the heuristic.
_PROTOCOL_TERMS = frozenset(
    {
        "markdown",
        "json",
        "yaml",
        "csv",
        "toml",
        "frontmatter",
        "heading",
        "headings",
        "bullet",
        "table",
        "directory",
        "folder",
        "filename",
        "filepath",
    }
)


def _protocol_tokens(text: str) -> set[str]:
    low = text.lower()
    return {t for t in _PROTOCOL_TERMS if t in low}


def _routine_skill_incoherence(config: CompanyConfig) -> list[str]:
    """Soft coherence check (ADR-024): a recurring task should defer the "how" (format,
    storage, protocol) to the skill that governs its work, not restate it.

    Heuristic and advisory only — surfaced via the ``warn`` sink, NEVER a validation error.
    For each recurring task, if its objective/criteria restate concrete format/storage
    tokens that a co-attached skill (a skill the assignee holds) also defines in its
    description/procedure/outputs, emit one warning per (task, skill) overlap. A false
    positive is harmless: the operator judges, and a deferential task trips nothing.
    """
    skills_by_agent = {a.slug: set(a.skills) for a in config.agents}
    skill_by_slug = {s.slug: s for s in config.skills}
    warnings: list[str] = []
    for task in config.tasks:
        if not task.recurrence:
            continue
        task_tokens = _protocol_tokens(task.objective + " " + " ".join(task.completion_criteria))
        if not task_tokens:
            continue
        for skill_slug in sorted(skills_by_agent.get(task.assignee, set())):
            skill = skill_by_slug.get(skill_slug)
            if skill is None:  # built-in / catalog skill with no SKILL.md (ADR-023)
                continue
            skill_text = " ".join([skill.description, *skill.procedure, *skill.outputs])
            shared = task_tokens & _protocol_tokens(skill_text)
            if shared:
                warnings.append(
                    f"recurring task {task.slug!r} restates format/storage language "
                    f"{sorted(shared)} that its co-attached skill {skill.slug!r} also defines "
                    "— a recurring task should defer the how (format/storage/protocol) to the "
                    "governing skill and keep only the trigger and this-run scope (ADR-024)"
                )
    return warnings


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

    # Per-agent portable model preference (ADR-017): (adapter type, model id) derived
    # from the same role buckets, emitted under each agent's `adapter`. Never `env`.
    # Explicit per-role model preferences from the brief (section 10 adapter_preferences)
    # override the coarse role default's MODEL for the named roles; unspecified roles keep
    # the default. Adapter type is unchanged (env-free, import-safe).
    model_overrides, unmatched_prefs = parse_model_preferences(
        config.brief.adapter_preferences, config.agents
    )
    adapters = assign_adapters(role_by_slug, model_overrides)
    if warn is not None:
        for line in unmatched_prefs:
            warn(
                f"adapter preference {line!r} names a model tier but matched no agent role — "
                "that role keeps its default model"
            )

    # Tasks with a `recurrence` cadence → importable Routines (ADR-022, US3, PROVISIONAL cron):
    # a `.paperclip.yaml` routines.<task-slug> block; the recurring task itself is flagged
    # `recurring: true` (no shadow task). Empty when no task is scheduled.
    routines = derive_routines(config.tasks)
    if warn is not None:
        for message in _routine_cadence_smells(routines):
            warn(message)
        # ADR-024: a recurring task must defer format/storage/protocol to the governing skill.
        for message in _routine_skill_incoherence(config):
            warn(message)

    base = {
        "brief": config.brief,
        "company": config.company,
        "agents": config.agents,
        "projects": config.projects,
        "tasks": config.tasks,
        "skills": config.skills,
        "license_kind": config.license_kind,
        "budgets": allocation.cents,
        "adapters": adapters,
        "routines": routines,
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
    # Governance reaches agents via the instruction bundle, not OPERATIONS.md/COMPANY.md files
    # (ADR-022): every AGENTS.md carries the idle-state protocol; the CEO/root additionally
    # carries the company goals (which do not survive import), the board-gate/approval language,
    # and the company critical rules. Targeted per role — not the whole manual.
    ops = config.operations
    for agent in config.agents:
        is_root = agent.reports_to is None
        actx = {
            "brief": config.brief,
            "company": config.company,
            "agent": agent,
            "soul": agent.soul,
            "role_bucket": _role_bucket(agent, agent.slug in manager_slugs),
            "is_root": is_root,
            "idle_state_protocol": ops.idle_state_protocol if ops is not None else None,
            "company_goals": config.company.goals if is_root else [],
            "critical_rules": ops.critical_rules if (is_root and ops is not None) else [],
            "board_gate": ops.approval_merge_rules if (is_root and ops is not None) else None,
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
