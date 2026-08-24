"""Fan-out orchestration tests for the full multi-agent pipeline (T014).

Uses an injected dispatch transport (no live calls). Verifies the staged
sequencing (identity → org → parallel leaves → operations-last), bounded
concurrency, and that a malformed response in any leaf aborts with no partial.
"""

import threading
import time

import pytest

from paperclip_blueprints.generators.client import GenerationError, LLMClient
from paperclip_blueprints.models.input import CompanyBrief
from paperclip_blueprints.renderers.bundle import (
    _CONCURRENCY,
    build_and_write,
    generate_bundle_full,
)
from test_cli import _dispatch_full


def _brief() -> CompanyBrief:
    return CompanyBrief(
        name="Indie Game Studio",
        slug="indie-game-studio",
        description="A solo-founder premium mobile puzzle studio shipping one game a year.",
        north_star="$30,000 monthly net revenue within 12 months.",
        goals=["4.6+ App Store rating sustained", "refund rate below 3% per quarter"],
        we_are="We are a single-title premium mobile studio.",
        we_are_not=["We are NOT a free-to-play studio.", "We are NOT a multi-title shop."],
        constraints=["One title at a time.", "No dark patterns."],
        governance_position="balanced",
    )


def test_full_pipeline_assembles_multi_agent_config() -> None:
    config = generate_bundle_full(_brief(), LLMClient(_invoke=_dispatch_full))
    assert config.mode == "full"
    assert {a.slug for a in config.agents} == {"ceo", "engineer"}
    assert len(config.projects) == 1
    assert len(config.tasks) == 1
    assert config.operations is not None
    # The non-root agent imports without an explicit role; the root is the CEO.
    roles = {a.slug: a.role for a in config.agents}
    assert roles["ceo"] == "ceo"
    assert roles["engineer"] is None


def test_pipeline_sequences_identity_org_then_leaves_then_operations() -> None:
    order: list[str] = []

    def tracking(**kw: object) -> str:
        system = str(kw["system"]).lower()
        if "identity" in system:
            order.append("identity")
        elif "org" in system:
            order.append("org")
        elif "operations" in system:
            order.append("operations")
        else:
            order.append("leaf")
        return _dispatch_full(**kw)

    generate_bundle_full(_brief(), LLMClient(_invoke=tracking))
    assert order[0] == "identity"
    assert order[1] == "org"
    assert order[-1] == "operations"
    assert "leaf" in order  # the fan-out ran between org and operations


def test_concurrency_is_bounded_by_semaphore() -> None:
    active = 0
    peak = 0
    lock = threading.Lock()

    def slow(**kw: object) -> str:
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        time.sleep(0.01)
        with lock:
            active -= 1
        return _dispatch_full(**kw)

    generate_bundle_full(_brief(), LLMClient(_invoke=slow))
    assert peak <= _CONCURRENCY


def test_malformed_leaf_aborts_with_no_partial(tmp_path) -> None:
    def broken(**kw: object) -> str:
        if "project" in str(kw["system"]).lower():
            return "no json here at all"
        return _dispatch_full(**kw)

    out = tmp_path / "out"
    with pytest.raises(GenerationError):
        build_and_write(_brief(), out, LLMClient(_invoke=broken))
    assert not out.exists()


# --- the closed handoff set reaches the call, end to end (feature 023) ------


def _dispatch_with_handoffs(**kwargs: object) -> str:
    """``_dispatch_full``, but each agent hands to the OTHER agent in the plan.

    The shared fixture returns empty handoff lists, so on its own it exercises none of
    this feature: a wrong legal set — or a forgotten argument — would leave every test
    green. This transport reads which agent is being generated and answers with a handoff
    naming its counterpart, which is legal only if ``bundle.py`` computed the set from the
    whole plan and excluded the agent itself.
    """
    system = str(kwargs["system"]).lower()
    if "mandate" not in system:
        return _dispatch_full(**kwargs)
    prompt = str(kwargs["user"])
    other = "engineer" if "- Slug: ceo" in prompt else "ceo"
    return (
        '```json\n{"mandate": "Owns the outcome.", "triggers": ["A build is ready."], '
        f'"receives_from": [{{"agent": "{other}", "flow": "the work"}}], '
        f'"hands_to": [{{"agent": "{other}", "flow": "the decision"}}], '
        '"deliverables": ["Shipped builds."], "can_approve": ["Routine scope."], '
        '"must_escalate": ["Pricing changes."], '
        '"escalation_text": "Escalate to the operator on pricing.", '
        '"tools_role_specific": "Reviews build status."}\n```'
    )


def test_each_agent_may_hand_to_every_other_agent_in_the_plan() -> None:
    """C1.2 (FR-002), through the real orchestration path.

    Asserts the wiring in ``bundle.py``: the legal set is the whole plan minus self. If
    the set were narrowed, or self were left in, or the argument omitted, this fails.
    """
    config = generate_bundle_full(_brief(), LLMClient(_invoke=_dispatch_with_handoffs))
    by_slug = {a.slug: a for a in config.agents}
    assert by_slug["ceo"].hands_to == ["engineer — the decision"]
    assert by_slug["engineer"].hands_to == ["ceo — the decision"]
    assert by_slug["ceo"].receives_from == ["engineer — the work"]


def test_a_handoff_to_a_non_existent_agent_aborts_the_run_not_the_validator() -> None:
    """C2.1, C2.5 (FR-004, SC-006), through the real orchestration path.

    The motivating failure: a one-character near-miss. It must now stop at the agent that
    produced it rather than surviving to validator I8 at the end of the bundle.
    """

    def near_miss(**kwargs: object) -> str:
        out = _dispatch_with_handoffs(**kwargs)
        return out.replace('"agent": "engineer"', '"agent": "enginer"')

    with pytest.raises(GenerationError) as exc:
        generate_bundle_full(_brief(), LLMClient(_invoke=near_miss))
    assert "enginer" in str(exc.value)


def test_the_orchestration_path_passes_a_set_that_excludes_the_agent_itself() -> None:
    """C1.2. Self-handoff is not offered, so the constraint cannot suggest one."""
    seen: list[list[str]] = []

    def capture(**kwargs: object) -> str:
        system = str(kwargs["system"]).lower()
        if "mandate" in system:
            schema = kwargs.get("schema")
            assert isinstance(schema, dict)
            seen.append(schema["properties"]["hands_to"]["items"]["properties"]["agent"]["enum"])
        return _dispatch_with_handoffs(**kwargs)

    generate_bundle_full(_brief(), LLMClient(_invoke=capture))
    assert sorted(seen) == [["ceo"], ["engineer"]], (
        "each agent's legal set must be the plan minus itself"
    )
