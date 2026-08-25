"""Runtime configuration: API credentials and model selection.

Credentials are read from the environment only and never logged (constitution,
FR-020). Model defaults follow ADR-001 / the constitution: Opus for content
synthesis, Sonnet for structural transforms.
"""

from __future__ import annotations

import os

# --- Models THIS TOOL CALLS (ADR-001 / constitution; ADR-045) -----------------
# Validity here is decided by our own API key and by whether the model accepts this
# codebase's request shape — streaming, adaptive thinking, output_config.effort,
# output_config.format. All four were verified against these ids by an instrumented
# call through the production transport on 2026-08-24 (ADR-045).
OPUS_MODEL = "claude-opus-5"
SONNET_MODEL = "claude-sonnet-5"

# Role of each generation step, used to pick a default model tier.
CONTENT_MODEL = OPUS_MODEL  # identity, soul (synthesis quality matters)
STRUCTURAL_MODEL = SONNET_MODEL  # org, agents, skills (constrained)

# --- Models a GENERATED BUNDLE prefers (ADR-017, refining ADR-015; ADR-045) ----
# Emitted as each agent's adapter.config.model in .paperclip.yaml. A DIFFERENT
# authority decides validity: the operator's Paperclip instance and its claude_local
# adapter build, which this repo cannot check — the importer does not validate these
# ids for env-free worker kinds, so a wrong one fails at agent-run time, not at import.
# They equal the generation-time ids above today. That is a coincidence of tiering,
# NOT a constraint: what this tool runs on and what a generated company runs on move
# for different reasons, and separating the names is what lets one move without the
# other. renderers/adapter.py reads only these; a test asserts it reads only these.
AGENT_TOP_TIER_MODEL = "claude-opus-5"
AGENT_BALANCED_MODEL = "claude-sonnet-5"

# Per-agent model preference shipped in .paperclip.yaml (ADR-017, refining ADR-015).
# Only env-free, import-safe registered worker kinds are emitted; provider routing,
# base URLs, and credentials (adapter.config.env) stay operator-environment and are
# NEVER emitted. Model ids are adjustable preferences (not import-validated for these
# kinds). CODEX_MODEL is the codex-local adapter's documented default at v2026.618.0.
CODEX_MODEL = "gpt-5.3-codex"
ADAPTER_CLAUDE_LOCAL = "claude_local"
ADAPTER_CODEX_LOCAL = "codex_local"
PORTABLE_ADAPTER_TYPES = frozenset({ADAPTER_CLAUDE_LOCAL, ADAPTER_CODEX_LOCAL})

# USD price per MILLION tokens (input, output), for the end-of-run cost summary
# (SC-011 of spec 002 requires that summary, so this table stays — ADR-045).
# An unknown model falls back to Sonnet, SILENTLY: a model id that changes without
# this table changing reports a wrong cost and raises nothing. A test derives the
# called-by-default ids from the constants above and asserts each is a key here.
#
# STANDARD published rates, verified against platform.claude.com 2026-08-24.
# Sonnet 5 also carries an INTRODUCTORY rate of $2/$10 through 2026-08-31, which is
# live as this is written and is deliberately NOT encoded: it would be right for a
# week and then under-report every run afterwards with nothing to signal the change.
# Over-reporting during an introductory period is the recoverable direction.
#
# Superseded ids are KEPT. This table prices what the tool may be ASKED to call, not
# only what it calls by default — `--model claude-opus-4-8` still resolves — and the
# real-billing reconciliation test anchors to a run made on those models. Dropping
# them would make that anchor arithmetic instead of evidence.
# When updating: check https://platform.claude.com/docs/en/about-claude/pricing;
# Anthropic's pricing has dropped before (Opus 4 → Opus 4.5 cut the Opus rate 3×).
TOKEN_PRICES_PER_MTOK: dict[str, tuple[float, float]] = {
    OPUS_MODEL: (5.0, 25.0),  # claude-opus-5
    SONNET_MODEL: (3.0, 15.0),  # claude-sonnet-5 (intro $2/$10 until 2026-08-31)
    "claude-opus-4-8": (5.0, 25.0),
    "claude-sonnet-4-6": (3.0, 15.0),
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate the USD cost of a call from the token price table."""
    in_price, out_price = TOKEN_PRICES_PER_MTOK.get(model, TOKEN_PRICES_PER_MTOK[SONNET_MODEL])
    return (input_tokens * in_price + output_tokens * out_price) / 1_000_000


# CLI ``--model`` aliases → full IDs. Version-suffixed aliases for superseded models
# are REMOVED rather than repointed (ADR-045): repointing ``opus-4.8`` at Opus 5 would
# make the flag say one model and select another. Removed, it falls through
# ``resolve_model`` unchanged as a literal id and the API reports it, and a deliberate
# older-model run stays expressible by full id (``--model claude-opus-4-8``).
_MODEL_ALIASES = {
    "opus-5": OPUS_MODEL,
    "opus": OPUS_MODEL,
    "sonnet-5": SONNET_MODEL,
    "sonnet": SONNET_MODEL,
}

API_KEY_ENV = "ANTHROPIC_API_KEY"


class MissingAPIKeyError(RuntimeError):
    """Raised when the Anthropic API key is not present in the environment."""

    def __init__(self) -> None:
        super().__init__(
            f"{API_KEY_ENV} is not set. Export it in your environment; "
            "the tool never reads keys from files or flags."
        )


def get_api_key() -> str:
    """Return the Anthropic API key from the environment, or raise.

    The key value is never logged or echoed.
    """
    key = os.environ.get(API_KEY_ENV)
    if not key:
        raise MissingAPIKeyError()
    return key


def resolve_model(override: str | None, *, default: str) -> str:
    """Resolve a model id from an optional CLI override alias.

    Args:
        override: A ``--model`` value (alias or full id), or None.
        default: The default full model id to use when no override is given.

    Returns:
        A full Anthropic model id.
    """
    if not override:
        return default
    return _MODEL_ALIASES.get(override, override)
