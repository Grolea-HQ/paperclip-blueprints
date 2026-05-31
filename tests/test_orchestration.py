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
