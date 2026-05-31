"""Referential-integrity checks (I1–I10) — contracts/bundle-validation.md.

Operates on the assembled ``CompanyConfig`` (structured, robust) plus the rendered
file map (for the file-set and ``.paperclip.yaml`` cross-checks). Each function
returns a list of violation strings rather than raising, so the caller can
aggregate every problem into one report.
"""

from __future__ import annotations

from ruamel.yaml import YAML

from ..models.org_plan import SPAN_OF_CONTROL
from ..models.output import CompanyConfig

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
            if s not in skill_set:
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

    # I8: handoffs name existing agents.
    for a in agents:
        for entry in (*a.receives_from, *a.hands_to):
            head = _handoff_head(entry)
            if head and head not in agent_slugs:
                v.append(f"I8: agent {a.slug!r} handoff names unknown agent {head!r}")

    # I9: .paperclip.yaml maps + sidebar match the actual dirs.
    v += _check_paperclip_yaml(files.get(".paperclip.yaml", ""), agent_slugs, project_slugs)

    # I10: file set matches the mode contract exactly.
    expected = _expected_files(config)
    actual = set(files)
    if missing := expected - actual:
        v.append(f"I10: missing files: {sorted(missing)}")
    if extra := actual - expected:
        v.append(f"I10: unexpected files: {sorted(extra)}")

    return v


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
