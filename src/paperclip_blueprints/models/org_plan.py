"""OrgPlan — the org_planner skeleton that fixes every slug and cross-reference
before content fan-out (v0.1b, R-001).

OrgPlan is a transient planning object, not a bundle artifact, but it carries the
structural invariants (single root, acyclic reporting, span-of-control ≤7,
resolvable owner/project/assignee, unique slugs) that gate the fan-out — so they
are enforced here, at the model level, before any expensive content call
(contracts/org-plan.md).
"""

from __future__ import annotations

import re

from pydantic import BaseModel, field_validator, model_validator

_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# P-PAT-3: no manager (CEO included) owns more than this many direct reports.
SPAN_OF_CONTROL = 7


def _check_slug(v: str) -> str:
    if not _SLUG_RE.match(v):
        raise ValueError(f"slug must be lowercase-hyphenated: {v!r}")
    return v


class AgentStub(BaseModel):
    """One planned agent: enough to drive per-agent content generation."""

    slug: str
    name: str
    title: str
    reports_to: str | None
    skills: list[str]

    @field_validator("slug")
    @classmethod
    def _slug_shape(cls, v: str) -> str:
        return _check_slug(v)

    @field_validator("skills")
    @classmethod
    def _at_least_one_skill(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("an agent must reference at least one skill")
        return v


class ProjectStub(BaseModel):
    """One planned starter project."""

    slug: str
    name: str
    owner: str

    @field_validator("slug")
    @classmethod
    def _slug_shape(cls, v: str) -> str:
        return _check_slug(v)


class TaskStub(BaseModel):
    """One planned starter task, linked to a project and an assignee."""

    slug: str
    name: str
    project: str
    assignee: str
    recurrence: str | None = None
    """Cadence for genuinely schedule-driven standing work, else None (ADR-022, US3). The
    org_planner sets this — a whole-org structural decision so only the truly scheduled tasks
    are flagged recurring; threaded into TaskDefinition and keyed off by routine emission."""

    @field_validator("slug")
    @classmethod
    def _slug_shape(cls, v: str) -> str:
        return _check_slug(v)


class OrgPlan(BaseModel):
    """The planned org skeleton: agents + projects + tasks, fully cross-referenced."""

    agents: list[AgentStub]
    projects: list[ProjectStub] = []
    tasks: list[TaskStub] = []

    @model_validator(mode="after")
    def _check_structure(self) -> OrgPlan:
        if not self.agents:
            raise ValueError("org plan must contain at least one agent")

        agent_slugs = [a.slug for a in self.agents]
        _require_unique(agent_slugs, "agent")
        _require_unique([p.slug for p in self.projects], "project")
        _require_unique([t.slug for t in self.tasks], "task")
        agent_set = set(agent_slugs)
        project_set = {p.slug for p in self.projects}

        # Single root.
        roots = [a.slug for a in self.agents if a.reports_to is None]
        if len(roots) != 1:
            raise ValueError(
                f"org plan must have exactly one root (reports_to=null); found {roots}"
            )

        # Managers resolve.
        for a in self.agents:
            if a.reports_to is not None and a.reports_to not in agent_set:
                raise ValueError(f"agent {a.slug!r} reports to unknown manager {a.reports_to!r}")

        _check_acyclic(self.agents)

        # Span-of-control (P-PAT-3).
        direct_reports: dict[str, int] = {}
        for a in self.agents:
            if a.reports_to is not None:
                direct_reports[a.reports_to] = direct_reports.get(a.reports_to, 0) + 1
        over = {m: n for m, n in direct_reports.items() if n > SPAN_OF_CONTROL}
        if over:
            raise ValueError(
                f"span-of-control exceeded (limit {SPAN_OF_CONTROL}): "
                + ", ".join(f"{m} has {n} reports" for m, n in sorted(over.items()))
            )

        # Ownership / assignment resolve.
        for p in self.projects:
            if p.owner not in agent_set:
                raise ValueError(f"project {p.slug!r} owned by unknown agent {p.owner!r}")
        for t in self.tasks:
            if t.project not in project_set:
                raise ValueError(f"task {t.slug!r} references unknown project {t.project!r}")
            if t.assignee not in agent_set:
                raise ValueError(f"task {t.slug!r} assigned to unknown agent {t.assignee!r}")

        return self

    @property
    def skill_slugs(self) -> list[str]:
        """The de-duplicated union of every agent's skills, in first-seen order."""
        seen: list[str] = []
        for a in self.agents:
            for s in a.skills:
                if s not in seen:
                    seen.append(s)
        return seen


def _require_unique(slugs: list[str], kind: str) -> None:
    dupes = {s for s in slugs if slugs.count(s) > 1}
    if dupes:
        raise ValueError(f"duplicate {kind} slug(s): {sorted(dupes)}")


def _check_acyclic(agents: list[AgentStub]) -> None:
    parent = {a.slug: a.reports_to for a in agents}
    for start in parent:
        seen = {start}
        cur = parent[start]
        while cur is not None:
            if cur in seen:
                raise ValueError(f"reporting graph has a cycle through {cur!r}")
            seen.add(cur)
            cur = parent.get(cur)
