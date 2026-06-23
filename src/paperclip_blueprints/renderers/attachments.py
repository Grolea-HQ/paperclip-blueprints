"""Skill→agent attachment instructions (ADR-020).

Importing a bundle places its skills in the company library but does NOT attach them
to agents — confirmed firsthand (library skills show "0 agents attached"). The tool
therefore emits explicit, per-agent attach instructions derived deterministically from
each agent's declared ``skills`` list. This module is the single source of those
instructions; ``renderers/render.py`` renders them into OPERATIONS.md (full bundle) or
README.md (single-agent), and ``renderers/bundle.py`` parses them back to enforce that
the rendered set equals the declared set (attachment closure).

Pure: no I/O, no model call. Mirrors the ``renderers/budget.py`` / ``renderers/adapter.py``
pattern.

Reuse boundary (FR-008): :func:`attach_step` is the one per-pair attach unit. ADR-019's
commodity-skill reuse prepends a library-install step to this step ("install skill X
from source S, then attach to agent Y") and MUST call it rather than duplicate it.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from ..models.agent import AgentDefinition


@dataclass(frozen=True)
class AttachmentPair:
    """A declared (agent, skill) attachment — one skill an agent should load."""

    agent_slug: str
    skill_slug: str


def attachment_pairs(agents: Sequence[AgentDefinition]) -> list[AttachmentPair]:
    """Declared ``(agent, skill)`` attachment pairs, deterministically ordered.

    Order is by agent position in ``agents``, then by skill position within that
    agent's ``skills`` list. A skill declared by two agents yields one pair per
    declaring agent (no cross-agent dedupe). An agent with no skills contributes
    nothing; empty input yields ``[]``.

    Args:
        agents: the bundle's agent definitions.

    Returns:
        The flat, ordered list of declared attachment pairs.
    """
    return [AttachmentPair(agent.slug, skill) for agent in agents for skill in agent.skills]


def attach_step(pair: AttachmentPair) -> str:
    """Render the single, reusable per-pair attach instruction.

    This is the one attach unit (FR-008). ADR-019's referenced-skill flow prepends a
    library-install step to this step and MUST NOT reimplement it.
    """
    return f"Attach skill `{pair.skill_slug}` to agent `{pair.agent_slug}`"


def attachments_by_agent(agents: Sequence[AgentDefinition]) -> list[tuple[str, list[str]]]:
    """Group attach steps per agent for rendering.

    Returns ``[(agent_slug, [attach_step, ...]), ...]`` for agents that declare at
    least one skill, in deterministic order. Steps come from :func:`attach_step`, so
    the rendered wording has a single source.
    """
    grouped: list[tuple[str, list[str]]] = []
    for agent in agents:
        steps = [attach_step(AttachmentPair(agent.slug, s)) for s in agent.skills]
        if steps:
            grouped.append((agent.slug, steps))
    return grouped


_ATTACH_STEP_RE = re.compile(r"Attach skill `([^`]+)` to agent `([^`]+)`")


def parse_attach_steps(text: str) -> set[tuple[str, str]]:
    """Parse rendered attach steps back into a ``{(agent_slug, skill_slug)}`` set.

    The inverse of :func:`attach_step`, used by the attachment-closure check to compare
    the rendered instructions against the declared pairs.
    """
    return {(agent, skill) for skill, agent in _ATTACH_STEP_RE.findall(text)}
