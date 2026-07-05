"""Per-agent run-policy caps (ADR-027).

The deployer previously set run-policy caps as hard-coded defaults
(``adapterConfig.maxTurnsPerRun = 30``; ``runtimeConfig.heartbeat.maxConcurrentRuns`` = 1
for the CEO / 2 for others). This module makes them **bundle-driven**: it reasons a
``RunPolicy`` per agent from role, so a company can tune caps per role instead of accepting
one global default. The values are emitted into ``.paperclip.yaml`` under each agent's
``runPolicy`` block; the deployer maps ``runPolicy.maxTurnsPerRun`` →
``adapterConfig.maxTurnsPerRun`` and ``runPolicy.maxConcurrentRuns`` →
``runtimeConfig.heartbeat.maxConcurrentRuns``.

Pure and deterministic (no LLM). The defaults match the deployer's current hard-coded
defaults, so behavior is unchanged for a role the reasoning does not tighten; the reasoning
only tightens where a role justifies it (a decision-maker/CEO gets tighter concurrency; a
bounded poller gets low turns).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.agent import AgentDefinition

# Deployer-matching defaults: unchanged behavior unless a role tightens them.
DEFAULT_MAX_TURNS_PER_RUN = 30
CEO_MAX_CONCURRENT_RUNS = 1
DEFAULT_MAX_CONCURRENT_RUNS = 2

# A bounded poller does a quick, repeated, bounded check — it does not need the full turn
# budget, so cap it low to stop a runaway loop.
POLLER_MAX_TURNS_PER_RUN = 10

# Whole-word signals that a role is a bounded poller (→ low turns). Word-boundary matched to
# avoid tripping on unrelated substrings. Kept tight so an ordinary role keeps the default.
_POLLER_RE = re.compile(
    r"\b(poll|polls|polling|monitor|monitors|monitoring|watch|watches|watching|"
    r"sweep|sweeps|sweeping)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RunPolicy:
    """One agent's run-policy caps, emitted under ``.paperclip.yaml`` ``runPolicy``."""

    max_turns_per_run: int
    max_concurrent_runs: int


def derive_run_policy(*, is_root: bool, title: str, mandate: str) -> RunPolicy:
    """Reason an agent's run-policy caps from its role.

    Args:
        is_root: The agent is the org root / CEO (``reports_to is None``).
        title: The agent's title.
        mandate: The agent's mandate prose.

    Returns:
        A ``RunPolicy``: the CEO/root gets tighter concurrency (1 vs 2); a bounded poller
        gets low turns (``POLLER_MAX_TURNS_PER_RUN``); otherwise the deployer-matching
        defaults (30 turns) apply.
    """
    max_concurrent = CEO_MAX_CONCURRENT_RUNS if is_root else DEFAULT_MAX_CONCURRENT_RUNS
    is_poller = bool(_POLLER_RE.search(f"{title} {mandate}"))
    max_turns = POLLER_MAX_TURNS_PER_RUN if is_poller else DEFAULT_MAX_TURNS_PER_RUN
    return RunPolicy(max_turns_per_run=max_turns, max_concurrent_runs=max_concurrent)


def assign_run_policies(agents: list[AgentDefinition]) -> dict[str, RunPolicy]:
    """Return each agent's reasoned ``RunPolicy``, keyed by slug (ADR-027)."""
    return {
        a.slug: derive_run_policy(is_root=a.reports_to is None, title=a.title, mandate=a.mandate)
        for a in agents
    }
