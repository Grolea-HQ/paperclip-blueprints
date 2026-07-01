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

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from ..config import (
    ADAPTER_CLAUDE_LOCAL,
    ADAPTER_CODEX_LOCAL,
    CODEX_MODEL,
    OPUS_MODEL,
    SONNET_MODEL,
)
from ..paperclip_slug import slugify_project_name


class _AgentRef(Protocol):
    """The only agent attributes the preference matcher reads — ``AgentDefinition`` satisfies it."""

    slug: str
    title: str
    name: str


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


def assign_adapters(
    role_by_slug: dict[str, str], model_overrides: dict[str, str] | None = None
) -> dict[str, AdapterChoice]:
    """Map each agent's role bucket to its portable ``(type, model)`` preference.

    Args:
        role_by_slug: agent slug -> role bucket
            ("owner" | "manager" | "engineering" | "generic").
        model_overrides: slug -> model id, from the brief's explicit per-role model
            preferences (see :func:`parse_model_preferences`). Overrides the coarse
            role default's **model** for the named roles; the adapter **type** stays
            the env-free, import-safe default (ADR-017 unchanged).

    Returns:
        slug -> :class:`AdapterChoice`, covering exactly the input agents. Every
        ``type`` is an env-free, import-safe worker kind; no ``env`` is produced.
    """
    overrides = model_overrides or {}
    result: dict[str, AdapterChoice] = {}
    for slug, bucket in role_by_slug.items():
        default = _BY_ROLE[bucket]
        result[slug] = AdapterChoice(default.type, overrides.get(slug, default.model))
    return result


# Claude model tier keyword (in a preference line) -> full model id. Only the Claude
# *tier* is honored here; adapter-*type* overrides (codex/hermes/opencode/Manifest) need
# instance/env knowledge and stay v0.2-deployer territory (ADR-017).
_TIER_MODELS = ((("opus",), OPUS_MODEL), (("sonnet",), SONNET_MODEL))


def _tier_model(line_lower: str) -> str | None:
    for keywords, model in _TIER_MODELS:
        if any(k in line_lower for k in keywords):
            return model
    return None


def _boundary_contains(haystack_slug: str, needle_slug: str) -> bool:
    """True if ``needle_slug`` appears as a whole hyphen-delimited run in ``haystack_slug``.

    Boundary match so agent ``analyst`` is not matched by a line about ``senior-analyst``.
    """
    return bool(needle_slug) and f"-{needle_slug}-" in f"-{haystack_slug}-"


def _matched_ref(agent: _AgentRef, line_slug: str) -> str | None:
    """The longest of the agent's slug / title-slug / name-slug that boundary-matches the line."""
    refs = [agent.slug, slugify_project_name(agent.title), slugify_project_name(agent.name)]
    matched = [r for r in refs if _boundary_contains(line_slug, r)]
    return max(matched, key=len) if matched else None


def parse_model_preferences(
    preferences: Sequence[str] | None, agents: Sequence[_AgentRef]
) -> tuple[dict[str, str], list[str]]:
    """Resolve the brief's per-role model preferences to per-slug model overrides.

    For each ``adapter_preferences`` line that names a Claude tier (``opus``/``sonnet``),
    match it to the agent(s) it references by boundary-safe slug / title-slug / name-slug, and
    record a model override. Lines with no Claude tier are skipped (adapter-type/provider notes
    stay v0.2). A line can legitimately name several distinct roles for one tier; a role whose
    matched ref is *nested* inside another matched role's ref (e.g. ``analyst`` inside
    ``senior-analyst``) is dropped so only the most-specific role is taken.

    Returns ``(overrides, unmatched)`` — ``overrides`` maps slug -> model id; ``unmatched``
    lists tier-naming lines that matched no agent (a likely typo the caller can warn about).
    """
    if not preferences:
        return {}, []
    overrides: dict[str, str] = {}
    unmatched: list[str] = []
    for line in preferences:
        model = _tier_model(line.lower())
        if model is None:
            continue
        line_slug = slugify_project_name(line)
        matched = [(a.slug, ref) for a in agents if (ref := _matched_ref(a, line_slug))]
        kept = [
            slug
            for slug, ref in matched
            if not any(other != ref and _boundary_contains(other, ref) for _, other in matched)
        ]
        if kept:
            for slug in kept:
                overrides[slug] = model
        else:
            unmatched.append(line)
    return overrides, unmatched
