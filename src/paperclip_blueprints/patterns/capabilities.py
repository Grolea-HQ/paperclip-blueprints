"""Per-agent capability derivation (ADR-026).

A Paperclip agent may need a platform capability its role genuinely requires — e.g. a
scanner/research role needs read-only web access to fetch external pages. The bundle
carries no structured capability signal today, so the deployer's per-agent capability step
(D7) has nothing to act on. This module derives a conservative, structured capability set
per agent from its role/title/mandate, which D7 consumes.

Capability grants are a permission decision, so the derivation is **deterministic and
auditable** — a keyword-reasoned mapping over role/title/mandate — NOT an LLM call that
could over-grant (the "LLM creativity can't overrule structural rules" principle applied to
access). It is conservative by default: grant only what the role genuinely needs, and when
in doubt grant nothing (D7 stays a no-op for that agent).

This is a leaf module (no runtime imports from the package) so ``models`` may import
``KNOWN_CAPABILITIES`` without a cycle.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # type-only; never executed, so no import cycle with models.agent
    from ..models.agent import AgentDefinition

# The read-only web-fetch capability: fetch external web pages (reading only). The single
# capability the generator derives today; the set is open for future additions.
WEB_FETCH = "web-fetch"

# Every capability slug the generator recognizes. A per-agent ``capabilities`` entry must be
# one of these; the deployer resolves them against its per-agent capability API.
KNOWN_CAPABILITIES: frozenset[str] = frozenset({WEB_FETCH})

# Whole-word signals in an agent's role/title/mandate that a role genuinely gathers external
# web information (→ read-only web-fetch). Word-boundary matched, so "resource"/"outsource"
# do not trip "source". Kept tight to avoid over-granting.
_WEB_FETCH_RE = re.compile(
    r"\b("
    r"web|internet|online|urls?|scrape|scraping|crawl|crawling|"
    r"scan|scanner|scanning|research|researching|prospect|prospecting|"
    r"discover|discovery|sources?|sourcing"
    r")\b",
    re.IGNORECASE,
)


def derive_capabilities(*, role: str | None, title: str, mandate: str) -> list[str]:
    """Return the capability slugs an agent's role genuinely needs, sorted and de-duped.

    Conservative: only a role/title/mandate that signals external web-information gathering
    is granted ``web-fetch``; everything else gets nothing (an empty list → D7 no-op).

    Args:
        role: The agent's importer role (may be ``None``).
        title: The agent's title.
        mandate: The agent's mandate prose (AGENTS.md).

    Returns:
        A sorted list of granted capability slugs (all in ``KNOWN_CAPABILITIES``), possibly
        empty.
    """
    text = " ".join(filter(None, (role, title, mandate)))
    granted: set[str] = set()
    if _WEB_FETCH_RE.search(text):
        granted.add(WEB_FETCH)
    return sorted(granted)


def attach_capabilities(agents: list[AgentDefinition]) -> list[AgentDefinition]:
    """Set each agent's ``capabilities`` from its role/title/mandate (ADR-026).

    Mutates each agent in place and returns the same list for chaining. Runs after the
    per-agent fan-out, where the mandate exists.
    """
    for agent in agents:
        agent.capabilities = derive_capabilities(
            role=agent.role, title=agent.title, mandate=agent.mandate
        )
    return agents
