"""Render a CompanyConfig into the in-memory bundle file map.

Bodies come from Jinja templates in ``templates/``; YAML frontmatter is produced by
:func:`dump_frontmatter` so quoting/order match the reference companies. Returns a
``{relative_path: content}`` map — nothing touches disk here (the atomic write lives
in ``bundle.py``).
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from ..models.agent import AgentDefinition
from ..models.company import CompanyDefinition
from ..models.goal import GoalHierarchy
from ..models.output import CompanyConfig
from ..models.project import ProjectDefinition
from ..models.skill import SkillDefinition
from ..models.task import TaskDefinition
from .adapter import assign_adapters, parse_model_preferences
from .budget import allocate_budgets
from .canon import (
    canon_coverage,
    canon_warnings,
    extract_canon_terms,
    extraction_warnings,
)
from .frontmatter import dump_frontmatter
from .routines import RoutineSpec, derive_routines, wakes_per_active_month
from .run_policy import (
    assign_run_policies,
    parse_run_policy_preferences,
    peer_turn_asymmetry,
)

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


def render_company_md(
    company: CompanyDefinition, goal_hierarchy: GoalHierarchy | None = None
) -> str:
    """Render COMPANY.md (frontmatter + body) from identity content.

    Shared by the full bundle and ``blueprints preview`` (US3), which emits only this file.

    Args:
        company: The identity content (carries the flat ``goals`` list).
        goal_hierarchy: The reasoned north-star → sub-goals tree (ADR-025). When given, it
            is emitted additively under ``metadata.paperclip.goalHierarchy`` for the
            deployer; the flat ``goals`` list is always preserved for backward-compat.
            ``None`` (e.g. ``preview``, which runs before the org exists) omits the block.
    """
    paperclip_meta: dict[str, Any] = {
        # `mono` is the company monogram letter, derived from the name
        # (matches the reference companies: Newsletter→N, Agency→A, …).
        "tone": company.tone,
        "mono": company.name[0].upper(),
    }
    if goal_hierarchy is not None:
        paperclip_meta["goalHierarchy"] = [
            {
                "slug": g.slug,
                "title": g.title,
                "description": g.description,
                "level": g.level,
                "parent": g.parent,
                "owner": g.owner,
            }
            for g in goal_hierarchy.goals
        ]
    frontmatter = dump_frontmatter(
        {
            "schema": "agentcompanies/v1",
            "name": company.name,
            "description": company.description,
            "version": company.version,
            "tags": company.tags,
            "goals": company.goals,
            "metadata": {
                "paperclip": paperclip_meta,
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
            "capabilities": agent.capabilities,
        },
        flow_seq_keys={"skills", "capabilities"},
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


def _day_pattern(cron: str) -> str:
    """The cron fields encoding WHICH days a routine runs — everything after minute and hour."""
    return " ".join(cron.split()[2:])


def _routine_cadence_smells(routines: list[RoutineSpec]) -> list[str]:
    """Soft smell-detector (ADR-022 US3): two recurring tasks on the SAME cadence AND assignee
    are likely one scheduled activity split into two (the org_planner one-cadence rule).

    Advisory only — surfaced via the ``warn`` sink, NEVER a validation error: a genuinely
    doubled cadence on one owner is legitimate, so the operator judges. Grouped by
    ``(day pattern, assignee)`` — NOT by the full cron, and not by the day pattern alone (two
    owners can share a cadence without a smell).

    The key is the **day pattern**, not the whole expression, because since feature 015 the
    expression also carries a per-task time-of-day: two tasks on one cadence now differ in the
    minute/hour fields, so keying on the full cron would have silently stopped this check ever
    firing. The question it asks is "was one activity split into two tasks?", and that is about
    the cadence, which is exactly the day pattern.
    """
    groups: dict[tuple[str, str], list[str]] = {}
    for r in routines:
        groups.setdefault((_day_pattern(r.cron), r.assignee), []).append(r.slug)
    return [
        f"routines {sorted(slugs)} share cadence {pattern!r} and assignee {assignee!r} — likely "
        "one scheduled activity split into multiple recurring tasks; consider folding into one "
        "recurring task (org_planner one-cadence rule)"
        for (pattern, assignee), slugs in groups.items()
        if len(slugs) > 1
    ]


def _routine_trigger_collisions(routines: list[RoutineSpec]) -> list[str]:
    """Soft collision detector (feature 015, US2): recurring tasks that fire at the same moment.

    Keyed on the trigger expression ALONE — deliberately a different key from
    :func:`_routine_cadence_smells`, which groups by ``(day pattern, assignee)``. The two answer
    different questions and neither replaces the other:

    - the cadence smell asks *"was one activity split into two tasks?"*, for which two different
      owners sharing a cadence is no evidence, so it rightly includes the assignee in its key;
    - this asks *"will these fire simultaneously and contend?"*, for which the owner is
      irrelevant — two agents on one subscription contend precisely because they are different
      agents.

    Widening the cadence smell to cover this would have destroyed the detection it was built
    for. A pair matching both conditions correctly produces both findings.

    Advisory only — via the ``warn`` sink, NEVER a validation error. Ordered by expression so
    repeated runs emit identical output.
    """
    groups: dict[str, list[str]] = {}
    for r in routines:
        groups.setdefault(r.cron, []).append(r.slug)
    return [
        f"routines {sorted(slugs)} share the same trigger {cron!r} and will fire simultaneously "
        "— on a shared subscription this is self-inflicted contention; consider moving one "
        "(the generated time of day is a default, not something the brief stated)"
        for cron, slugs in sorted(groups.items())
        if len(slugs) > 1
    ]


def _routine_dependency_order(
    tasks: Sequence[TaskDefinition], routines: list[RoutineSpec]
) -> list[str]:
    """Soft ordering check (feature 015, US3, FR-008): a consumer that does not follow its producer.

    Fires when task A's objective references task B by slug or name, A and B recur on the same
    day pattern, and A is scheduled **at or before** B — so A reports on work B has not done yet.

    **Why "at or before" and not "same trigger".** The narrower rule (warn only on an identical
    trigger) was the original design, and it would have been dead on arrival: the whole point of
    the time-of-day spread is to stop routines sharing a trigger, so the pair would separate and
    this check would fall silent — while the defect got *worse*, the recap landing hours before
    the scan instead of alongside it. Equality is just the special case where the gap is zero.

    **Why day patterns must match.** Across differing patterns (a daily consumer of a weekly
    producer) there is no single well-defined "before" without expanding both schedules. Recall
    is deliberately sacrificed to keep the finding trustworthy when it does fire.

    Advisory only — via the ``warn`` sink, NEVER a validation error.
    """
    by_slug = {r.slug: r for r in routines}
    recurring = [t for t in tasks if t.slug in by_slug]
    warnings: list[str] = []
    for consumer in recurring:
        c_routine = by_slug[consumer.slug]
        for producer in recurring:
            if producer.slug == consumer.slug:
                continue
            p_routine = by_slug[producer.slug]
            if _day_pattern(c_routine.cron) != _day_pattern(p_routine.cron):
                continue
            if not _references_task(consumer.objective, producer):
                continue
            if _time_of_day(c_routine.cron) > _time_of_day(p_routine.cron):
                continue  # the consumer correctly follows its producer
            warnings.append(
                f"recurring task {consumer.slug!r} references {producer.slug!r} but is scheduled "
                f"at or before the task it depends on ({c_routine.cron!r} vs {p_routine.cron!r}) "
                "— it will report on work that has not run yet, every time it fires, without "
                "erroring; schedule it later in the day or fold the two together"
            )
    return warnings


def _references_task(objective: str, producer: TaskDefinition) -> bool:
    """Whether ``objective`` names ``producer`` by slug or name, word-boundary matched.

    Word boundaries matter: a task slugged ``scan`` must not be considered referenced by prose
    about a "scandal". Precision over recall — the finding is only worth having if it is right
    when it fires.
    """
    haystack = objective.lower()
    for token in (producer.slug, producer.name):
        if not token:
            continue
        if re.search(rf"\b{re.escape(token.lower())}\b", haystack):
            return True
    return False


def _time_of_day(cron: str) -> tuple[int, int]:
    """``(hour, minute)`` from a cron expression, for ordering comparisons."""
    fields = cron.split()
    return int(fields[1]), int(fields[0])


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
    # Cadence weighting (ADR-012 amendment): an agent's cap is also weighted by how often its
    # recurring tasks wake it. An agent driven by several routines is funded for its BUSIEST
    # one — the cap has to cover the heaviest month, not an average of them. An agent with no
    # recurring task maps to None (on-demand; see budget.UNSCHEDULED_WAKE_WEIGHT).
    wakes_by_slug: dict[str, int | None] = {a.slug: None for a in config.agents}
    for task in config.tasks:
        wakes = wakes_per_active_month(task.recurrence)
        if wakes is None or task.assignee not in wakes_by_slug:
            continue
        current = wakes_by_slug[task.assignee]
        wakes_by_slug[task.assignee] = wakes if current is None else max(current, wakes)

    role_by_slug = {a.slug: _role_bucket(a, a.slug in manager_slugs) for a in config.agents}
    allocation = allocate_budgets(
        role_by_slug,
        config.brief.governance_position,
        config.brief.capital_monthly_eur,
        wakes_by_slug,
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

    # Per-agent run-policy overrides from the brief (feature 014 / ADR-034): a pure carrier
    # layering brief-stated caps / heartbeat toggle over the ADR-027 role base. Empty ⇒ the
    # role base alone (byte-identical to today). Values are brief-validated; a reference that
    # matches no agent is advisory only.
    run_overrides, run_unmatched = parse_run_policy_preferences(
        config.brief.run_policy_preferences, config.agents
    )
    if warn is not None:
        for line in run_unmatched:
            warn(f"run-policy override {line!r} names no agent — no run policy is set for it")

    # Per-agent run-policy caps (ADR-027) + brief overrides (ADR-034). Peers under one manager
    # that end up with different turn caps are reported for the operator to judge — never
    # normalized, since normalizing propagates the majority value and the tightening direction
    # fails silently.
    run_policies = assign_run_policies(config.agents, run_overrides)
    if warn is not None:
        for message in peer_turn_asymmetry(config.agents, run_policies, run_overrides):
            warn(message)

    # Tasks with a `recurrence` cadence → importable Routines (ADR-022, US3, PROVISIONAL cron):
    # a `.paperclip.yaml` routines.<task-slug> block; the recurring task itself is flagged
    # `recurring: true` (no shadow task). Empty when no task is scheduled.
    routines = derive_routines(config.tasks)
    if warn is not None:
        for message in _routine_cadence_smells(routines):
            warn(message)
        # Feature 015 US2: a differently-keyed check — same trigger, any owner. The spread in
        # routines.py is probabilistic, so this is what turns "usually distinct" into "always
        # reported".
        for message in _routine_trigger_collisions(routines):
            warn(message)
        # Feature 015 US3: a consumer that does not follow the producer it names.
        for message in _routine_dependency_order(config.tasks, routines):
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
        # Per-agent run-policy caps (ADR-027): role-derived maxTurnsPerRun /
        # maxConcurrentRuns, with brief overrides overlaid per field (feature 014 / ADR-034).
        "run_policies": run_policies,
        "routines": routines,
    }

    files: dict[str, str] = {
        ".paperclip.yaml": _render("paperclip_yaml.j2", **base),
        "COMPANY.md": render_company_md(config.company, config.goal_hierarchy),
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

    # Canon coverage (ADR-037): the brief's section-11 operating canon has no carrier but
    # the threading, so a term that reaches no file is lost silently. Report by name, and
    # report where thinly-carried terms landed. ADVISORY ONLY — this never blocks a write
    # and is deliberately not part of validate_bundle, which raises. Scoped to
    # canon-UNIQUE material: a phrase also present in another brief field reaches the
    # generators by an existing path, so its coverage says nothing about this defect.
    if warn is not None and config.brief.free_text:
        brief = config.brief
        exclude_texts = [
            brief.description,
            brief.north_star,
            brief.we_are,
            *brief.goals,
            *brief.we_are_not,
            *brief.constraints,
        ]
        terms = extract_canon_terms(brief.free_text, exclude_texts=exclude_texts)
        # Extraction failures first: canon present but nothing recognised means the
        # coverage result below is empty for a reason that has nothing to do with the
        # bundle, and a silent zero-term run would read as "all clear".
        for message in extraction_warnings(brief.free_text, terms):
            warn(message)
        for message in canon_warnings(canon_coverage(terms, files)):
            warn(message)

    return files
