"""Referential-integrity checks (I1–I10) — contracts/bundle-validation.md.

Operates on the assembled ``CompanyConfig`` (structured, robust) plus the rendered
file map (for the file-set and ``.paperclip.yaml`` cross-checks). Each function
returns a list of violation strings rather than raising, so the caller can
aggregate every problem into one report.
"""

from __future__ import annotations

import re

from ruamel.yaml import YAML

from ..models.org_plan import SPAN_OF_CONTROL
from ..models.output import CompanyConfig
from ..paperclip_slug import slugify_agent_name, slugify_project_name
from ..patterns.builtins import BUILTIN_AGENT_SLUGS, BUILTIN_SKILLS

# Reserved human-principal role-words (ADR-016): an agent name/title must not collide
# with the human founder/board, who sit above the company as its approver and are
# never agents. Matched on standalone tokens (word boundaries) so substrings like
# "onboarding", "billboard", or "Product Owner" do not trip it. ``owner`` is
# intentionally not reserved.
_RESERVED_ROLE_RE = re.compile(r"\b(co-?founder|founder|board)\b", re.IGNORECASE)

_AGENT_FILES = ("AGENTS.md", "SOUL.md", "HEARTBEAT.md", "TOOLS.md")


def _expected_files(config: CompanyConfig) -> set[str]:
    """The exact file set a bundle of this shape must contain (I10)."""
    files = {".paperclip.yaml", "COMPANY.md", "README.md", "LICENSE.txt"}
    if config.operations is not None:
        files |= {"OPERATIONS.md", "PROJECT-INVENTORY.md"}
    for a in config.agents:
        files |= {f"agents/{a.slug}/{name}" for name in _AGENT_FILES}
    for s in config.skills:
        files.add(f"skills/{s.slug}/SKILL.md")
    for p in config.projects:
        files.add(f"projects/{p.slug}/PROJECT.md")
    for t in config.tasks:
        files.add(f"tasks/{t.slug}/TASK.md")
    # Routines (ADR-022 US3) add NO files: a recurring task is the existing task flagged
    # `recurring: true`, not a separate shadow task — so the expected set is unchanged.
    return files


def _handoff_head(entry: str) -> str:
    """The leading agent slug of a handoff string like ``ceo — sets strategy``."""
    token = entry.strip().strip("`")
    return token.split()[0].strip("`,") if token else ""


def check_integrity(config: CompanyConfig, files: dict[str, str]) -> list[str]:
    """Return every referential-integrity violation (I1–I10)."""
    v: list[str] = []
    agents = config.agents
    agent_slugs = {a.slug for a in agents}
    project_slugs = {p.slug for p in config.projects}
    skill_slugs = [s.slug for s in config.skills]

    # I1: exactly one root.
    roots = [a.slug for a in agents if a.reports_to is None]
    if len(roots) != 1:
        v.append(f"I1: expected exactly one root agent (reportsTo null), found {sorted(roots)}")

    # I2 + I3: managers resolve, graph acyclic.
    parent = {a.slug: a.reports_to for a in agents}
    for a in agents:
        if a.reports_to is not None and a.reports_to not in agent_slugs:
            v.append(f"I2: agent {a.slug!r} reports to unknown manager {a.reports_to!r}")
    for start in parent:
        seen = {start}
        cur = parent[start]
        while cur is not None:
            if cur in seen:
                v.append(f"I3: reporting graph has a cycle through {cur!r}")
                break
            seen.add(cur)
            cur = parent.get(cur)

    # I4: span-of-control.
    counts: dict[str, int] = {}
    for a in agents:
        if a.reports_to is not None:
            counts[a.reports_to] = counts.get(a.reports_to, 0) + 1
    for manager, n in sorted(counts.items()):
        if n > SPAN_OF_CONTROL:
            v.append(f"I4: manager {manager!r} has {n} direct reports (limit {SPAN_OF_CONTROL})")

    # I5: skill closure.
    dup = {s for s in skill_slugs if skill_slugs.count(s) > 1}
    if dup:
        v.append(f"I5: duplicate skill slug(s): {sorted(dup)}")
    skill_set = set(skill_slugs)
    referenced: set[str] = set()
    for a in agents:
        for s in a.skills:
            referenced.add(s)
            # Built-in skills (ADR-023) resolve against the instance catalog, not the
            # bundle, so a reference to one is valid without a SKILL.md.
            if s not in skill_set and s not in BUILTIN_SKILLS:
                v.append(f"I5: agent {a.slug!r} references skill {s!r} with no SKILL.md")
    for s in sorted(skill_set - referenced):
        v.append(f"I5: skill {s!r} is referenced by no agent")

    # I6: task references.
    for t in config.tasks:
        if t.project not in project_slugs:
            v.append(f"I6: task {t.slug!r} references unknown project {t.project!r}")
        if t.assignee not in agent_slugs:
            v.append(f"I6: task {t.slug!r} assigned to unknown agent {t.assignee!r}")

    # I7: project ownership.
    for p in config.projects:
        if p.owner not in agent_slugs:
            v.append(f"I7: project {p.slug!r} owned by unknown agent {p.owner!r}")

    # I12: project slug must equal Paperclip's slugify(name) so a task's `project:`
    # reference resolves against the urlKey Paperclip derives on import (ADR-013).
    # A `-N` collision suffix on that base is allowed (matches `uniqueSlug`).
    for p in config.projects:
        base = slugify_project_name(p.name)
        if base and p.slug != base and not re.fullmatch(rf"{re.escape(base)}-\d+", p.slug):
            v.append(
                f"I12: project {p.slug!r} slug must equal slugify(name) {base!r} "
                f"(or {base!r}-N on collision) so tasks associate on import"
            )

    # I8: handoffs name existing agents.
    for a in agents:
        for entry in (*a.receives_from, *a.hands_to):
            head = _handoff_head(entry)
            if head and head not in agent_slugs:
                v.append(f"I8: agent {a.slug!r} handoff names unknown agent {head!r}")

    # I9: .paperclip.yaml maps + sidebar match the actual dirs.
    v += _check_paperclip_yaml(files.get(".paperclip.yaml", ""), agent_slugs, project_slugs)

    # I11: per-agent budgets sum within the stated capital cap (ADR-012, INV-1).
    v += _check_budget_sum(files.get(".paperclip.yaml", ""), config.brief.capital_monthly_eur)

    # I13: no agent name/title collides with the human founder/board role (ADR-016).
    for a in agents:
        for field, value in (("name", a.name), ("title", a.title)):
            if _RESERVED_ROLE_RE.search(value):
                v.append(
                    f"I13: agent {a.slug!r} {field} {value!r} collides with the human "
                    f"founder/board role; name agents for working roles (e.g. CEO), not "
                    f"Founder/Board"
                )

    # I15: no agent name/title collides with a built-in Paperclip agent. Paperclip
    # derives an agent's key from its DISPLAY NAME, so the check normalizes name and
    # title the same way (`normalizeAgentUrlKey`) rather than matching literal tokens.
    # See `patterns.builtins.BUILTIN_AGENT_SLUGS` for the source and the version it was
    # read at — the reserved set is a platform fact that needs re-reading each release.
    for a in agents:
        for field, value in (("name", a.name), ("title", a.title)):
            if slugify_agent_name(value) in BUILTIN_AGENT_SLUGS:
                v.append(
                    f"I15: agent {a.slug!r} {field} {value!r} collides with the built-in "
                    f"Paperclip agent {slugify_agent_name(value)!r}, which is "
                    f"auto-provisioned into every company; rename the agent"
                )

    # I14: goal-hierarchy closure (ADR-025). Structural invariants (one root, resolvable/
    # acyclic parents, unique slugs) are guaranteed by the GoalHierarchy model; here we
    # re-assert them plus owner-resolves-to-a-real-agent on the assembled bundle, so a
    # malformed hierarchy is a hard failure in the aggregated report, not a silent pass.
    if config.goal_hierarchy is not None:
        goals = config.goal_hierarchy.goals
        goal_slugs = {g.slug for g in goals}
        roots = [g.slug for g in goals if g.parent is None]
        if len(roots) != 1:
            v.append(f"I14: goal hierarchy must have exactly one root, found {sorted(roots)}")
        for g in goals:
            if g.parent is not None and g.parent not in goal_slugs:
                v.append(f"I14: goal {g.slug!r} has unknown parent {g.parent!r}")
            if g.owner not in agent_slugs:
                v.append(f"I14: goal {g.slug!r} owner {g.owner!r} is not an agent in the org")

    # I10: file set matches the mode contract exactly.
    expected = _expected_files(config)
    actual = set(files)
    if missing := expected - actual:
        v.append(f"I10: missing files: {sorted(missing)}")
    if extra := actual - expected:
        v.append(f"I10: unexpected files: {sorted(extra)}")

    return v


def _check_budget_sum(yaml_text: str, capital_monthly_eur: int | None) -> list[str]:
    """I11: the per-agent budgets sum to no more than the capital cap (INV-1).

    Skipped when no cap was stated (budgets are then absent by design).
    """
    if capital_monthly_eur is None or not yaml_text:
        return []
    try:
        data = YAML(typ="safe").load(yaml_text)
    except Exception:  # noqa: BLE001 - I9 already reports unparseable YAML
        return []
    total = 0
    for agent in (data.get("agents") or {}).values():
        if isinstance(agent, dict) and isinstance(agent.get("budgetMonthlyCents"), int):
            total += agent["budgetMonthlyCents"]
    cap_cents = capital_monthly_eur * 100
    if total > cap_cents:
        return [
            f"I11: per-agent budgets sum to {total} cents, exceeding the capital cap "
            f"of {cap_cents} cents"
        ]
    return []


def _check_paperclip_yaml(
    yaml_text: str, agent_slugs: set[str], project_slugs: set[str]
) -> list[str]:
    v: list[str] = []
    if not yaml_text:
        return ["I9: .paperclip.yaml is missing"]
    try:
        data = YAML(typ="safe").load(yaml_text)
    except Exception as exc:  # noqa: BLE001
        return [f"I9: .paperclip.yaml is not valid YAML: {exc}"]
    yaml_agents = set((data.get("agents") or {}).keys())
    if yaml_agents != agent_slugs:
        v.append(f"I9: .paperclip.yaml agents map {sorted(yaml_agents)} != {sorted(agent_slugs)}")
    yaml_projects = set((data.get("projects") or {}).keys())
    if yaml_projects != project_slugs:
        v.append(
            f"I9: .paperclip.yaml projects map {sorted(yaml_projects)} != {sorted(project_slugs)}"
        )
    sidebar = data.get("sidebar") or {}
    if set(sidebar.get("agents") or []) != agent_slugs:
        v.append("I9: .paperclip.yaml sidebar.agents does not match the agent set")
    if set(sidebar.get("projects") or []) != project_slugs:
        v.append("I9: .paperclip.yaml sidebar.projects does not match the project set")
    return v
