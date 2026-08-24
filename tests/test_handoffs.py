"""Handoff targets are drawn from a closed set (feature 023).

Mirrors ``src/paperclip_blueprints/generators/handoffs.py``. Contract clauses cited from
``specs/023-closed-set-handoffs/contracts/handoff-generation.md``.

Every assertion here is reachable without a transport: the legal set, the schema fragment
and the membership check are pure. That is deliberate — the guarantee this feature makes
must not depend on what any model does (FR-007).
"""

from __future__ import annotations

import pathlib

import pytest

from paperclip_blueprints.generators.client import GenerationError
from paperclip_blueprints.generators.handoffs import (
    handoff_schema,
    legal_targets,
    parse_handoffs,
)

_PLAN_SLUGS = ["ceo", "cto", "qa-lead", "writer", "editor"]


# --- the legal set ----------------------------------------------------------


def test_legal_set_is_every_other_agent_including_non_adjacent() -> None:
    """C1.2 (FR-002). The wide-set decision, made falsifiable.

    ``editor`` is adjacent to nobody in a plan where ``ceo`` is root: it is neither the
    manager, nor a direct report, nor a peer. Its presence here is what distinguishes the
    accepted design from the rejected adjacent-set variant (spec → Rejected Alternatives).
    """
    targets = legal_targets(_PLAN_SLUGS, exclude="ceo")
    assert targets == ["cto", "qa-lead", "writer", "editor"]
    assert "editor" in targets
    assert "ceo" not in targets


def test_legal_set_preserves_plan_order_and_deduplicates() -> None:
    """C1.2. Stable ordering keeps the emitted schema stable between runs."""
    assert legal_targets(["b", "a", "b", "c"], exclude="c") == ["b", "a"]


def test_legal_set_of_a_single_agent_company_is_empty() -> None:
    """C1.5 (FR-009). There is no legal target, so none may be offered."""
    assert legal_targets(["solo"], exclude="solo") == []


# --- the schema fragment ----------------------------------------------------


def test_schema_enumerates_exactly_the_legal_set() -> None:
    """C1.1, C1.2 (FR-001, FR-003). The target is a field; the prose is not constrained."""
    frag = handoff_schema(["cto", "qa-lead"])
    assert frag["type"] == "array"
    props = frag["items"]["properties"]
    assert props["agent"]["enum"] == ["cto", "qa-lead"]
    assert props["flow"] == {"type": "string"}, "the prose must stay unconstrained"
    assert frag["items"]["additionalProperties"] is False
    assert sorted(frag["items"]["required"]) == ["agent", "flow"]


def test_schema_enum_is_not_stripped_by_the_strict_projection() -> None:
    """C1.3 (R1).

    ``_strict_node`` removes the keywords the structured-output dialect does not support.
    ``enum`` is supported and must survive — if a future edit adds it to that set, this
    feature's prevention half silently becomes a no-op and nothing else would notice.
    """
    from paperclip_blueprints.generators.client import _UNSUPPORTED_SCHEMA_KEYS, _strict_node

    assert "enum" not in _UNSUPPORTED_SCHEMA_KEYS
    projected = _strict_node(handoff_schema(["cto", "qa-lead"]))
    assert projected["items"]["properties"]["agent"]["enum"] == ["cto", "qa-lead"]


# --- membership ------------------------------------------------------------


def _parse(entries: object, targets: list[str] | None = None) -> list[str]:
    return parse_handoffs(
        entries,
        targets=targets if targets is not None else ["cto", "qa-lead"],
        field="hands_to",
        owner="ceo",
    )


def test_a_target_in_the_set_is_joined_into_the_form_downstream_expects() -> None:
    """C5.1 (FR-010)."""
    assert _parse([{"agent": "qa-lead", "flow": "verified builds"}]) == [
        "qa-lead — verified builds"
    ]


def test_an_out_of_set_target_is_rejected() -> None:
    """C2.1 (FR-004)."""
    with pytest.raises(GenerationError):
        _parse([{"agent": "qa-led", "flow": "verified builds"}])


def test_the_rejection_names_owner_field_target_and_legal_set() -> None:
    """C2.2 (FR-006). The re-sample can only succeed if it is told what was wrong."""
    with pytest.raises(GenerationError) as exc:
        _parse([{"agent": "qa-led", "flow": "verified builds"}])
    message = str(exc.value)
    assert "ceo" in message, "names the agent being generated"
    assert "hands_to" in message, "names the field"
    assert "qa-led" in message, "names the offending target"
    assert "qa-lead" in message and "cto" in message, "names the legal set"


@pytest.mark.parametrize("target", ["", "   ", None])
def test_an_empty_or_absent_target_is_rejected_not_skipped(target: object) -> None:
    """C2.6 (FR-013).

    ``_handoff_head`` returns "" for such an entry and I8 skips it, so an empty handoff
    passes validation today. A check that skips its own input reports clean on the case it
    exists for.
    """
    entry: dict[str, object] = {"flow": "something"}
    if target is not None:
        entry["agent"] = target
    with pytest.raises(GenerationError):
        _parse([entry])


@pytest.mark.parametrize("entry", ["qa-lead — verified builds", ["qa-lead"], 42, None])
def test_an_entry_that_is_not_an_object_is_rejected(entry: object) -> None:
    """C2.7 (R4).

    Accepting the joined string would restore free-text authoring of the slug on exactly
    the path where the schema constrains nothing — the unconstrained retry.
    """
    with pytest.raises(GenerationError):
        _parse([entry])


def test_empty_entries_are_allowed() -> None:
    """An agent with no handoffs is legitimate; only a named non-agent is not."""
    assert _parse([]) == []


def test_a_missing_flow_yields_the_bare_slug() -> None:
    """C5.1. Both forms give the slug back to ``_handoff_head``."""
    assert _parse([{"agent": "cto", "flow": ""}]) == ["cto"]


# --- nothing is repaired ----------------------------------------------------


def test_a_one_character_near_miss_rejects_and_never_resolves() -> None:
    """C4.1 (FR-008, SC-003, SC-006). The failure that motivated the feature.

    A silent correction turns a visible failure into an invisible guess, and the failure
    mode is an agent handing work to the wrong role with nothing reporting it.
    """
    with pytest.raises(GenerationError) as exc:
        _parse([{"agent": "qa-led", "flow": "verified builds"}])
    # The legal set is quoted in the message; what must not happen is a returned value.
    assert exc.value.args and "qa-led" in str(exc.value)


@pytest.mark.parametrize("decorated", ["`qa-lead`", "  qa-lead  ", "``qa-lead``", "\tqa-lead\n"])
def test_formatting_that_carries_no_identity_is_normalised(decorated: str) -> None:
    """C4.3 (FR-011). The prompt renders slugs in backticks, so the model echoing them is
    expected. Stripping them cannot map one agent onto another."""
    assert _parse([{"agent": decorated, "flow": "verified builds"}]) == [
        "qa-lead — verified builds"
    ]


@pytest.mark.parametrize("mangled", ["QA-Lead", "qa_lead", "QA-LEAD", "qa lead", "qalead"])
def test_transformations_that_could_map_one_agent_onto_another_are_rejected(
    mangled: str,
) -> None:
    """C4.3 (FR-011).

    Case folding and punctuation collapsing are repair wearing normalisation's clothes:
    slugs are lowercase-hyphenated by ``AgentStub``'s validator, so such a rule could
    resolve two distinct planned agents onto one target.
    """
    with pytest.raises(GenerationError):
        _parse([{"agent": mangled, "flow": "verified builds"}])


def test_no_similarity_comparison_over_slugs_exists_anywhere_in_the_source() -> None:
    """C4.2 (FR-008, SC-003).

    Asserted by inspection as well as by behaviour: a behavioural assertion alone is
    satisfied by a repair that happens to guess correctly on the sampled case. This is the
    assertion that would fail if someone later "helpfully" closed the one-character gap.
    """
    src = pathlib.Path(__file__).resolve().parent.parent / "src" / "paperclip_blueprints"
    banned = ("difflib", "get_close_matches", "SequenceMatcher", "levenshtein", "edit_distance")
    offenders = [
        f"{path.relative_to(src)}: {token}"
        for path in src.rglob("*.py")
        for token in banned
        if token.lower() in path.read_text(encoding="utf-8").lower()
    ]
    assert not offenders, f"nearest-match repair of agent slugs is prohibited: {offenders}"
