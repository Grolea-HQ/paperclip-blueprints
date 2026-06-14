"""Resilient JSON generation — extraction, retry, schema, fallback (ADR-014)."""

import pytest

from paperclip_blueprints.generators.client import (
    APIRequestError,
    GenerationError,
    LLMClient,
    extract_json_text,
    strict_json_schema,
)
from paperclip_blueprints.models.agent import AgentDefinition, AgentSoul
from paperclip_blueprints.models.skill import SkillDefinition
from paperclip_blueprints.models.task import TaskDefinition

# --- extract_json_text (E1–E6) ----------------------------------------------


def test_extract_json_fence() -> None:
    assert extract_json_text('```json\n{"a": 1}\n```') == '{"a": 1}'


def test_extract_untagged_fence() -> None:
    assert extract_json_text('```\n{"a": 1}\n```') == '{"a": 1}'


def test_extract_raw_object() -> None:
    assert extract_json_text('{"a": 1}') == '{"a": 1}'


def test_extract_prose_wrapped() -> None:
    out = extract_json_text('Sure! Here it is:\n{"a": 1}\nHope that helps.')
    assert out == '{"a": 1}'


def test_extract_top_level_array() -> None:
    assert extract_json_text("[1, 2, 3]") == "[1, 2, 3]"


def test_extract_no_json_raises() -> None:
    with pytest.raises(GenerationError):
        extract_json_text("there is no json here")


def test_extract_outermost_object_with_nesting() -> None:
    raw = 'prefix {"a": {"b": [1,2]}, "c": 3} suffix'
    assert extract_json_text(raw) == '{"a": {"b": [1,2]}, "c": 3}'


# --- strict_json_schema (S1–S6) ---------------------------------------------

_UNSUPPORTED = {
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


def _walk(node: object) -> list[dict]:
    """Yield every dict node in a schema tree."""
    found: list[dict] = []
    if isinstance(node, dict):
        found.append(node)
        for v in node.values():
            found.extend(_walk(v))
    elif isinstance(node, list):
        for v in node:
            found.extend(_walk(v))
    return found


def _assert_strict(schema: dict) -> None:
    for node in _walk(schema):
        assert not (_UNSUPPORTED & set(node)), f"unsupported keyword in {node}"
        if node.get("type") == "object":
            assert node.get("additionalProperties") is False


def test_strict_full_model_all_required() -> None:
    s = strict_json_schema(AgentSoul)
    _assert_strict(s)
    assert set(s["required"]) == set(s["properties"])  # all fields required
    assert "beliefs" in s["properties"]


def test_strict_include_subset() -> None:
    body = {"mandate", "triggers", "deliverables"}
    s = strict_json_schema(AgentDefinition, include=body)
    _assert_strict(s)
    assert set(s["properties"]) == body
    assert set(s["required"]) == body
    assert "soul" not in s["properties"] and "slug" not in s["properties"]


def test_strict_exclude_subset() -> None:
    s = strict_json_schema(SkillDefinition, exclude={"slug"})
    _assert_strict(s)
    assert "slug" not in s["properties"]
    assert "procedure" in s["properties"]


def test_strict_task_subset() -> None:
    s = strict_json_schema(TaskDefinition, include={"objective", "completion_criteria"})
    _assert_strict(s)
    assert set(s["properties"]) == {"objective", "completion_criteria"}
    assert "project" not in s["properties"] and "assignee" not in s["properties"]


# --- complete_json: retry / fallback / exhaustion (C1–C8) -------------------


def _seq_transport(responses: list[object]):
    """A transport that returns each response in turn; tuples carry usage."""
    calls = {"n": 0}

    def invoke(**kwargs: object) -> object:
        i = min(calls["n"], len(responses) - 1)
        calls["n"] += 1
        out = responses[i]
        if isinstance(out, Exception):
            raise out
        return out

    return invoke, calls


def test_complete_json_first_try() -> None:
    invoke, calls = _seq_transport(['{"a": 1}'])
    client = LLMClient(_invoke=invoke)
    assert client.complete_json(model="m", system="s", user="u", what="x") == {"a": 1}
    assert calls["n"] == 1


def test_complete_json_malformed_then_valid() -> None:
    invoke, calls = _seq_transport(['{"a": 1', '{"a": 1}'])
    client = LLMClient(_invoke=invoke)
    assert client.complete_json(model="m", system="s", user="u", what="x") == {"a": 1}
    assert calls["n"] == 2  # one retry


def test_complete_json_retry_prompt_includes_error() -> None:
    seen: list[str] = []

    def invoke(*, user: str, **_: object) -> str:
        seen.append(user)
        return '{"bad"' if len(seen) == 1 else '{"ok": true}'

    client = LLMClient(_invoke=invoke)
    client.complete_json(model="m", system="s", user="ORIGINAL", what="x")
    assert "ORIGINAL" in seen[1]
    assert "not valid JSON" in seen[1]


def test_complete_json_exhaustion_names_leaf() -> None:
    invoke, calls = _seq_transport(['{"bad"'])
    client = LLMClient(_invoke=invoke)
    with pytest.raises(GenerationError) as exc:
        client.complete_json(model="m", system="s", user="u", what="agent mandate", attempts=3)
    assert "agent mandate" in str(exc.value)
    assert "3 attempts" in str(exc.value)
    assert calls["n"] == 3


def test_complete_json_counts_retried_usage() -> None:
    invoke, _ = _seq_transport([('{"bad"', (10, 5)), ('{"ok": 1}', (10, 5))])
    client = LLMClient(_invoke=invoke)
    client.complete_json(model="claude-opus-4-7", system="s", user="u", what="x")
    summary = client.usage_summary()
    assert summary["total"]["calls"] == 2  # both attempts counted


def test_complete_json_forwards_schema() -> None:
    captured: dict[str, object] = {}

    def invoke(*, schema: object = None, **_: object) -> str:
        captured["schema"] = schema
        return '{"ok": 1}'

    client = LLMClient(_invoke=invoke)
    schema = strict_json_schema(AgentSoul)
    client.complete_json(model="m", system="s", user="u", what="x", schema=schema)
    assert captured["schema"] == schema


def test_complete_json_falls_back_when_schema_rejected() -> None:
    calls = {"n": 0}

    def invoke(*, schema: object = None, **_: object) -> str:
        calls["n"] += 1
        if schema is not None:
            raise APIRequestError("model does not support output_config.format")
        return '{"ok": 1}'

    client = LLMClient(_invoke=invoke)
    out = client.complete_json(
        model="m", system="s", user="u", what="x", schema=strict_json_schema(AgentSoul)
    )
    assert out == {"ok": 1}
    assert calls["n"] == 2  # one rejected (with schema), one succeeded (without)


def test_complete_json_non_object_raises() -> None:
    invoke, _ = _seq_transport(["[1, 2, 3]"])
    client = LLMClient(_invoke=invoke)
    with pytest.raises(GenerationError):
        client.complete_json(model="m", system="s", user="u", what="x", attempts=1)
