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
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic import BaseModel

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

# Streaming cap for the real transport. Thinking is adaptive (ADR-008): the
# model sizes its own reasoning, so there is no fixed budget to set.
_MAX_TOKENS = 8000

# Project default effort for content-synthesis Opus calls (ADR-008).
_DEFAULT_EFFORT = "high"


class GenerationError(Exception):
    """Raised on a missing prompt, a malformed model response, or an API failure."""


class APIRequestError(GenerationError):
    """Raised when the Anthropic SDK rejects the request (``BadRequestError``).

    Distinct from a transient API failure so callers can tell "the model rejected
    this request shape" (e.g. ``output_config.format`` on a model that does not
    support structured output — ADR-014) apart from errors worth retrying. The SDK
    already retries 429/5xx internally before raising.
    """


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


def extract_json_text(raw: str) -> str:
    """Return the JSON span of a model response, tolerant of fences and prose.

    Prefers a fenced ```` ```json ````/```` ``` ```` block; otherwise takes the
    outermost ``{...}`` or ``[...]`` span by bracket matching, ignoring any prose
    around it. Structured-output responses are raw JSON (no fence), while the
    prompts ask for a fenced block — this handles both, plus arrays (ADR-014, R5).

    Raises:
        GenerationError: if no JSON-like span is present at all.
    """
    blocks = _FENCE_RE.findall(raw)
    if blocks:
        for tag, body in blocks:
            if tag.lower() == "json":
                return body.strip()
        return blocks[0][1].strip()

    # No fence: find the outermost {...} or [...] span by matching brackets.
    starts = [i for i in (raw.find("{"), raw.find("[")) if i != -1]
    if not starts:
        raise GenerationError("model response contained no JSON object or array")
    start = min(starts)
    open_ch = raw[start]
    close_ch = "}" if open_ch == "{" else "]"
    depth = 0
    for i in range(start, len(raw)):
        if raw[i] == open_ch:
            depth += 1
        elif raw[i] == close_ch:
            depth -= 1
            if depth == 0:
                return raw[start : i + 1].strip()
    # Unbalanced (e.g. truncated object) — return from the start; json.loads reports it.
    return raw[start:].strip()


def loads_json(raw: str, *, what: str) -> dict[str, Any] | list[Any]:
    """Extract and parse the JSON a generator response carries (object or array).

    Args:
        raw: The full model response.
        what: A short label used in error messages (e.g. "org plan").

    Raises:
        GenerationError: if no JSON is present or it is not valid JSON.
    """
    text = extract_json_text(raw)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise GenerationError(f"{what} response was not valid JSON: {exc}") from exc


def parse_json_response(raw: str, *, what: str) -> dict[str, Any]:
    """Extract and parse the JSON object a generator response carries.

    Thin wrapper over :func:`loads_json` kept for callers that require an object.
    """
    payload = loads_json(raw, what=what)
    if not isinstance(payload, dict):
        raise GenerationError(f"{what} response was not a JSON object")
    return payload


# Constraint keywords that the structured-output JSON-schema dialect does not
# support (ADR-014); stripped from a model's schema before it is sent.
_UNSUPPORTED_SCHEMA_KEYS = frozenset(
    {
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "multipleOf",
        "minLength",
        "maxLength",
        "pattern",
        "minItems",
        "maxItems",
        "uniqueItems",
    }
)


def _strict_node(node: Any) -> Any:
    """Recursively close objects to extra properties and strip unsupported keys."""
    if isinstance(node, dict):
        cleaned = {k: _strict_node(v) for k, v in node.items() if k not in _UNSUPPORTED_SCHEMA_KEYS}
        if cleaned.get("type") == "object":
            cleaned["additionalProperties"] = False
        return cleaned
    if isinstance(node, list):
        return [_strict_node(v) for v in node]
    return node


def strict_json_schema(
    model: type[BaseModel],
    *,
    include: set[str] | None = None,
    exclude: set[str] | None = None,
) -> dict[str, Any]:
    """Project a Pydantic model into a structured-output-safe JSON schema (ADR-014).

    Sets ``additionalProperties: false`` on every object (including ``$defs``),
    strips unsupported constraint keywords, and restricts the top-level properties
    to ``include`` (or all-but-``exclude``), with ``required`` matching.

    Args:
        model: the Pydantic model describing the call's JSON output.
        include: if given, keep only these top-level properties.
        exclude: if given, drop these top-level properties.
    """
    schema = _strict_node(model.model_json_schema())
    props: dict[str, Any] = schema.get("properties", {})
    if include is not None:
        props = {k: v for k, v in props.items() if k in include}
    if exclude is not None:
        props = {k: v for k, v in props.items() if k not in exclude}
    schema["properties"] = props
    schema["required"] = sorted(props)
    schema["additionalProperties"] = False
    return schema


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
        schema: dict[str, Any] | None = None,
    ) -> str:
        """Return the model's text response for a single-turn completion.

        Args:
            thinking: enable adaptive extended thinking (ADR-008).
            effort: ``output_config`` effort when thinking is on; defaults to the
                project content-synthesis default (``high``). Ignored when
                ``thinking`` is False.
            schema: when given, constrain the response to this JSON schema via
                ``output_config.format`` (structured output, ADR-014). Composes
                with ``thinking``/``effort``.

        Raises:
            APIRequestError: if the SDK rejects the request (e.g. a model that does
                not support ``output_config.format``).
            GenerationError: on any other API failure.
        """
        if thinking and effort is None:
            effort = _DEFAULT_EFFORT
        result = self._invoke(
            model=model, system=system, user=user, thinking=thinking, effort=effort, schema=schema
        )
        if isinstance(result, tuple):
            text, usage = result
            self._usage.append(CallUsage(model, int(usage[0]), int(usage[1])))
            return text
        return result

    def complete_json(
        self,
        *,
        model: str,
        system: str,
        user: str,
        what: str,
        thinking: bool = False,
        effort: str | None = None,
        schema: dict[str, Any] | None = None,
        attempts: int = 3,
    ) -> dict[str, Any]:
        """Complete and parse a JSON object, re-sampling on a malformed response (ADR-014).

        Resilient call/parse boundary: a single malformed response re-samples only
        this call (feeding the parser error back) instead of aborting the run. When
        ``schema`` is given the response is constrained via structured output; if
        the model rejects that (``APIRequestError``), the schema is dropped and the
        remaining attempts run unconstrained. Usage accumulates per attempt.

        Args:
            what: a short leaf label for error messages (e.g. "agent mandate").
            attempts: total tries before failing (default 3 = 1 + 2 retries).

        Raises:
            GenerationError: if no attempt yields valid JSON; the message names the
                leaf and the attempt count.
        """
        active_schema = schema
        prompt = user
        last_error: Exception | None = None
        for _ in range(max(1, attempts)):
            try:
                raw = self.complete(
                    model=model,
                    system=system,
                    user=prompt,
                    thinking=thinking,
                    effort=effort,
                    schema=active_schema,
                )
            except APIRequestError as exc:
                if active_schema is not None:
                    # Model rejected structured output — fall back to plain JSON.
                    active_schema = None
                    last_error = exc
                    continue
                raise
            try:
                return parse_json_response(raw, what=what)
            except GenerationError as exc:
                last_error = exc
                prompt = (
                    f"{user}\n\nYour previous reply was not valid JSON ({exc}). "
                    "Return ONLY valid JSON — no prose, no markdown code fence."
                )
        raise GenerationError(
            f"{what}: model did not return valid JSON after {attempts} attempts: {last_error}"
        )

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
        self,
        *,
        model: str,
        system: str,
        user: str,
        thinking: bool,
        effort: str | None,
        schema: dict[str, Any] | None = None,
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
        # effort (when thinking) and format (when a schema is given) both live in
        # output_config and coexist (ADR-008 / ADR-014).
        output_config: dict[str, object] = {}
        if thinking:
            kwargs["thinking"] = {"type": "adaptive"}
            output_config["effort"] = effort or _DEFAULT_EFFORT
        if schema is not None:
            output_config["format"] = {"type": "json_schema", "schema": schema}
        if output_config:
            kwargs["output_config"] = output_config

        parts: list[str] = []
        try:
            with self._sdk.messages.stream(**kwargs) as stream:  # type: ignore[attr-defined]
                for chunk in stream.text_stream:
                    parts.append(chunk)
            usage = stream.get_final_message().usage
        except anthropic.BadRequestError as exc:
            # e.g. a model that does not support output_config.format — let
            # complete_json fall back to the unconstrained retry path (ADR-014).
            raise APIRequestError(f"Anthropic API rejected the request: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 - surface any other SDK failure clearly
            raise GenerationError(f"Anthropic API call failed: {exc}") from exc
        return "".join(parts), (usage.input_tokens, usage.output_tokens)
