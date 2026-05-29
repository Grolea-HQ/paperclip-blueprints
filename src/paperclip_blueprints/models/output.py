"""CompanyConfig — the composite the renderer consumes for a single-agent bundle.

The single-agent invariant is enforced structurally: this type holds exactly one
agent and one skill (no lists), and no operations/projects/tasks fields. Those are
added in v0.1b.
"""

from __future__ import annotations

from pydantic import BaseModel

from .agent import AgentDefinition
from .company import CompanyDefinition
from .input import CompanyBrief
from .skill import SkillDefinition


class CompanyConfig(BaseModel):
    """All generated artifacts for a v0.1a single-agent bundle."""

    brief: CompanyBrief
    company: CompanyDefinition
    agent: AgentDefinition
    skill: SkillDefinition
    license_kind: str = "Proprietary"
