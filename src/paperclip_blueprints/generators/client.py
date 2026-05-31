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
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

# Streaming cap for the real transport. Thinking is adaptive (ADR-008): the
# model sizes its own reasoning, so there is no fixed budget to set.
_MAX_TOKENS = 8000

# Project default effort for content-synthesis Opus calls (ADR-008).
_DEFAULT_EFFORT = "high"


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


# Transport signature: (model, system, user, thinking, effort) -> response text,
# or (text, (input_tokens, output_tokens)) when the transport reports usage. The
# real transport reports usage; plain-text mocks simply return a string.
Transport = Callable[..., Any]


@dataclass(frozen=True)
class CallUsage:
    """Token usage for one completed call."""

    model: str
    input_tokens: int
    output_tokens: int


class LLMClient:
    """Wraps the Anthropic SDK behind a single, injectable ``complete`` call.

    Token usage is accumulated on the instance as a side effect of ``complete`` so
    a whole run's cost can be summarized at the end (US4 / R-005), without changing
    ``complete``'s ``str`` return type.
    """

    def __init__(self, api_key: str | None = None, *, _invoke: Transport | None = None) -> None:
        self._invoke: Transport = _invoke or self._invoke_anthropic
        self._api_key = api_key
        self._sdk = None  # constructed lazily by the real transport
        self._usage: list[CallUsage] = []

    def complete(
        self,
        *,
        model: str,
        system: str,
        user: str,
        thinking: bool = False,
        effort: str | None = None,
    ) -> str:
        """Return the model's text response for a single-turn completion.

        Args:
            thinking: enable adaptive extended thinking (ADR-008).
            effort: ``output_config`` effort when thinking is on; defaults to the
                project content-synthesis default (``high``). Ignored when
                ``thinking`` is False.
        """
        if thinking and effort is None:
            effort = _DEFAULT_EFFORT
        result = self._invoke(
            model=model, system=system, user=user, thinking=thinking, effort=effort
        )
        if isinstance(result, tuple):
            text, usage = result
            self._usage.append(CallUsage(model, int(usage[0]), int(usage[1])))
            return text
        return result

    def usage_summary(self) -> dict[str, Any]:
        """Aggregate per-model token usage and estimated cost for the run."""
        from ..config import estimate_cost

        by_model: dict[str, dict[str, Any]] = {}
        for u in self._usage:
            m = by_model.setdefault(
                u.model, {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
            )
            m["calls"] += 1
            m["input_tokens"] += u.input_tokens
            m["output_tokens"] += u.output_tokens
        total = {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
        for model, m in by_model.items():
            m["cost_usd"] = estimate_cost(model, m["input_tokens"], m["output_tokens"])
            total["calls"] += m["calls"]
            total["input_tokens"] += m["input_tokens"]
            total["output_tokens"] += m["output_tokens"]
            total["cost_usd"] += m["cost_usd"]
        return {"total": total, "by_model": by_model}

    def _invoke_anthropic(
        self, *, model: str, system: str, user: str, thinking: bool, effort: str | None
    ) -> tuple[str, tuple[int, int]]:
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
            kwargs["thinking"] = {"type": "adaptive"}
            kwargs["output_config"] = {"effort": effort or _DEFAULT_EFFORT}

        parts: list[str] = []
        try:
            with self._sdk.messages.stream(**kwargs) as stream:  # type: ignore[attr-defined]
                for chunk in stream.text_stream:
                    parts.append(chunk)
            usage = stream.get_final_message().usage
        except Exception as exc:  # noqa: BLE001 - surface any SDK failure clearly
            raise GenerationError(f"Anthropic API call failed: {exc}") from exc
        return "".join(parts), (usage.input_tokens, usage.output_tokens)
