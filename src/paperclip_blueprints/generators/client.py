"""The single seam to the Anthropic API.

All LLM access goes through :class:`LLMClient`. Tests inject a fake ``_invoke``
transport so the suite never makes a live call (Constitution III); the real
transport streams with extended thinking on Opus calls. Prompt files are loaded
from the versioned ``prompts/`` package; generator responses carry their payload
in a fenced block that :func:`extract_fenced_block` pulls out.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

# Streaming/thinking budgets for the real transport.
_MAX_TOKENS = 8000
_THINKING_BUDGET = 4000


class GenerationError(Exception):
    """Raised on a missing prompt, a malformed model response, or an API failure."""


def load_prompt(name: str) -> str:
    """Load a versioned prompt by stem name from ``prompts/<name>.md``."""
    path = _PROMPTS_DIR / f"{name}.md"
    if not path.is_file():
        raise GenerationError(f"prompt not found: {path}")
    return path.read_text(encoding="utf-8")


def render_prompt(name: str, /, **context: object) -> str:
    """Load a prompt template and render its ``{{ ... }}`` variables."""
    from jinja2 import Template

    return Template(load_prompt(name)).render(**context)


_FENCE_RE = re.compile(r"```([\w-]*)\n(.*?)```", re.DOTALL)


def extract_fenced_block(text: str, *, lang: str | None = None) -> str:
    """Return the contents of a fenced code block.

    Args:
        text: The raw model response.
        lang: If given, prefer a fence tagged with this language; otherwise the
            first fenced block is used.

    Raises:
        GenerationError: if no suitable fenced block is present.
    """
    blocks = _FENCE_RE.findall(text)
    if not blocks:
        raise GenerationError("model response contained no fenced code block")
    if lang is not None:
        for tag, body in blocks:
            if tag.lower() == lang.lower():
                return body.strip()
    return blocks[0][1].strip()


def parse_json_response(raw: str, *, what: str) -> dict[str, Any]:
    """Extract and parse the JSON object a generator response carries.

    Args:
        raw: The full model response.
        what: A short label used in error messages (e.g. "org plan").

    Raises:
        GenerationError: if no JSON block is present or it is not valid JSON.
    """
    block = extract_fenced_block(raw, lang="json")
    try:
        payload = json.loads(block)
    except json.JSONDecodeError as exc:
        raise GenerationError(f"{what} response was not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise GenerationError(f"{what} response was not a JSON object")
    return payload


# Transport signature: (model, system, user, thinking) -> response text.
Transport = Callable[..., str]


class LLMClient:
    """Wraps the Anthropic SDK behind a single, injectable ``complete`` call."""

    def __init__(
        self, api_key: str | None = None, *, _invoke: Transport | None = None
    ) -> None:
        self._invoke: Transport = _invoke or self._invoke_anthropic
        self._api_key = api_key
        self._sdk = None  # constructed lazily by the real transport

    def complete(
        self,
        *,
        model: str,
        system: str,
        user: str,
        thinking: bool = False,
    ) -> str:
        """Return the model's text response for a single-turn completion."""
        return self._invoke(model=model, system=system, user=user, thinking=thinking)

    def _invoke_anthropic(
        self, *, model: str, system: str, user: str, thinking: bool
    ) -> str:
        import anthropic

        from ..config import get_api_key

        if self._sdk is None:
            self._sdk = anthropic.Anthropic(api_key=self._api_key or get_api_key())

        kwargs: dict[str, object] = {
            "model": model,
            "max_tokens": _MAX_TOKENS,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        if thinking:
            kwargs["thinking"] = {"type": "enabled", "budget_tokens": _THINKING_BUDGET}

        parts: list[str] = []
        try:
            with self._sdk.messages.stream(**kwargs) as stream:  # type: ignore[attr-defined]
                for chunk in stream.text_stream:
                    parts.append(chunk)
        except Exception as exc:  # noqa: BLE001 - surface any SDK failure clearly
            raise GenerationError(f"Anthropic API call failed: {exc}") from exc
        return "".join(parts)
