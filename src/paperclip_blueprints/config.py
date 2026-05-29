"""Runtime configuration: API credentials and model selection.

Credentials are read from the environment only and never logged (constitution,
FR-020). Model defaults follow ADR-001 / the constitution: Opus for content
synthesis, Sonnet for structural transforms.
"""

from __future__ import annotations

import os

# Full model IDs (ADR-001 / constitution).
OPUS_MODEL = "claude-opus-4-7"
SONNET_MODEL = "claude-sonnet-4-6"

# Role of each generation step, used to pick a default model tier.
CONTENT_MODEL = OPUS_MODEL  # identity, soul (synthesis quality matters)
STRUCTURAL_MODEL = SONNET_MODEL  # org, agents, skills (constrained)

# CLI ``--model`` aliases → full IDs.
_MODEL_ALIASES = {
    "opus-4.7": OPUS_MODEL,
    "opus": OPUS_MODEL,
    "sonnet-4.6": SONNET_MODEL,
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
