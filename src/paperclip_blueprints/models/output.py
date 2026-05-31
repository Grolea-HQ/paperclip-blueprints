"""CompanyConfig — the composite the renderer consumes.

Mode-aware (R-007): ``single`` holds the v0.1a 9-file subset (one agent, one
skill, no projects/tasks/operations); ``full`` holds the complete multi-agent
bundle. The mode discriminator lets the type itself enforce each mode's
cardinality invariants. Graph-level checks (acyclic, span-of-control) live on
``OrgPlan`` and the bundle validator (US3); here we enforce only mode cardinality,
the single-root rule, and skill cross-reference closure.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .agent import AgentDefinition
from .company import CompanyDefinition
from .input import CompanyBrief
from .operations import OperationsDefinition
from .project import ProjectDefinition
from .skill import SkillDefinition
from .task import TaskDefinition


class CompanyConfig(BaseModel):
    """All generated artifacts for a bundle, single-agent or full multi-agent."""

    mode: Literal["single", "full"] = "full"
    brief: CompanyBrief
    company: CompanyDefinition
    agents: list[AgentDefinition]
    skills: list[SkillDefinition]
    projects: list[ProjectDefinition] = Field(default_factory=list)
    tasks: list[TaskDefinition] = Field(default_factory=list)
    operations: OperationsDefinition | None = None
    license_kind: str = "Proprietary"

    @model_validator(mode="after")
    def _check_mode(self) -> CompanyConfig:
        roots = [a for a in self.agents if a.reports_to is None]
        if self.mode == "single":
            if len(self.agents) != 1:
                raise ValueError("single-agent bundle must have exactly one agent")
            if len(self.skills) != 1:
                raise ValueError("single-agent bundle must have exactly one skill")
            if self.projects or self.tasks:
                raise ValueError("single-agent bundle must have no projects or tasks")
            if self.operations is not None:
                raise ValueError("single-agent bundle must not have operations")
        else:  # full
            if len(roots) != 1:
                raise ValueError(
                    f"full bundle must have exactly one root agent (reports_to=null); "
                    f"found {[a.slug for a in roots]}"
                )
            if not self.projects:
                raise ValueError("full bundle must have at least one project")
            if not self.tasks:
                raise ValueError("full bundle must have at least one task")
            if self.operations is None:
                raise ValueError("full bundle must have operations")
            skill_slugs = {s.slug for s in self.skills}
            for a in self.agents:
                missing = set(a.skills) - skill_slugs
                if missing:
                    raise ValueError(
                        f"agent {a.slug!r} references skill(s) with no SKILL.md: {sorted(missing)}"
                    )
        return self
