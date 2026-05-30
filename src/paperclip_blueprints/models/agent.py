"""AgentDefinition and the nested AgentSoul — an agent's AGENTS.md + SOUL.md content.

TOOLS.md is rendered deterministically from the agent's slug, the company slug, and
``tools_role_specific`` (ADR-004), so there is no separately LLM-populated tools model.
"""

from __future__ import annotations

from pydantic import BaseModel, field_validator


class AgentSoul(BaseModel):
    """The 7-section SOUL.md persona."""

    identity: str
    what_we_are: str
    product_reality: str
    beliefs: list[str]
    how_i_act: list[str]
    what_i_dont_do: list[str]
    my_north_star: str

    @field_validator("beliefs")
    @classmethod
    def _includes_idle_state(cls, v: list[str]) -> list[str]:
        # P-PAT-6 / FR-009: every persona must hold the idle-state belief.
        if not any("idle" in belief.lower() for belief in v):
            raise ValueError(
                "SOUL.md beliefs must include an idle-state belief "
                "(agents wait between heartbeats rather than inventing work)"
            )
        return v


class AgentDefinition(BaseModel):
    """An agent's mandate (AGENTS.md) plus its persona (SOUL.md)."""

    slug: str
    name: str
    title: str
    reports_to: str | None
    role: str | None = None
    """Paperclip importer role (company-portability.ts:2600 reads
    agents.<slug>.role, falling back to "agent" — which strips CEO
    permissions). Free-form non-empty string in Paperclip; "ceo" and "agent"
    verified. The v0.1a generator sets "ceo" for the single agent; v0.1b will
    derive from reports_to and verify additional role values against the
    importer enum before emitting them."""
    skills: list[str]
    mandate: str
    triggers: list[str]
    receives_from: list[str]
    hands_to: list[str]
    deliverables: list[str]
    can_approve: list[str]
    must_escalate: list[str]
    escalation_text: str
    tools_role_specific: str
    soul: AgentSoul

    @field_validator("skills")
    @classmethod
    def _at_least_one_skill(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("an agent must reference at least one skill")
        return v
