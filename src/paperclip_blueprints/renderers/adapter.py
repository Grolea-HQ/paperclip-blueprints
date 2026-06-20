"""Per-agent model preference assignment (ADR-017, refining ADR-015).

Derives a portable ``(adapter type, model id)`` preference for each agent from its
role bucket — the same classifier the budget allocator uses. Pure and deterministic.

Only env-free, import-safe registered worker kinds are produced
(``claude_local``/``codex_local``); ``adapter.config.env`` (provider routing, base
URLs, credentials) and the instance's actual model availability are
operator-environment and are never produced here. Model ids are adjustable
preferences and are not validated by the importer for these worker kinds.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config import (
    ADAPTER_CLAUDE_LOCAL,
    ADAPTER_CODEX_LOCAL,
    CODEX_MODEL,
    OPUS_MODEL,
    SONNET_MODEL,
)


@dataclass(frozen=True)
class AdapterChoice:
    """The portable per-agent preference: a worker-kind type and a model id."""

    type: str
    model: str


# Role bucket (from ``render._role_bucket``) -> portable (adapter type, model id).
# Default to a single provider for out-of-the-box coherence: every role runs on
# ``claude_local`` — the owner/CEO on the top tier (it reasons over the whole
# company), every other role on the balanced tier (Sonnet, which is also strong at
# code). ``codex_local`` is a fully supported alternative worker, not the default
# (see ``CODEX_ALTERNATIVE``); flipping a role to it is a one-line change here.
_BY_ROLE: dict[str, AdapterChoice] = {
    "owner": AdapterChoice(ADAPTER_CLAUDE_LOCAL, OPUS_MODEL),
    "manager": AdapterChoice(ADAPTER_CLAUDE_LOCAL, SONNET_MODEL),
    "engineering": AdapterChoice(ADAPTER_CLAUDE_LOCAL, SONNET_MODEL),
    "generic": AdapterChoice(ADAPTER_CLAUDE_LOCAL, SONNET_MODEL),
}

# Supported opt-in alternative worker kind (env-free, import-validated by S12).
# Not a default; assign it to a role by using it in ``_BY_ROLE`` above.
CODEX_ALTERNATIVE = AdapterChoice(ADAPTER_CODEX_LOCAL, CODEX_MODEL)


def assign_adapters(role_by_slug: dict[str, str]) -> dict[str, AdapterChoice]:
    """Map each agent's role bucket to its portable ``(type, model)`` preference.

    Args:
        role_by_slug: agent slug -> role bucket
            ("owner" | "manager" | "engineering" | "generic").

    Returns:
        slug -> :class:`AdapterChoice`, covering exactly the input agents. Every
        ``type`` is an env-free, import-safe worker kind; no ``env`` is produced.
    """
    return {slug: _BY_ROLE[bucket] for slug, bucket in role_by_slug.items()}
