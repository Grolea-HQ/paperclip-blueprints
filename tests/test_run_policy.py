"""Bundle-configurable run-policy caps (ADR-027).

Covers the deterministic role reasoning (CEO/root → tighter concurrency; a bounded poller →
low turns; otherwise deployer-matching defaults), and the `.paperclip.yaml` `runPolicy`
carrier, per-agent, wired through the full pipeline.
"""

from __future__ import annotations

from ruamel.yaml import YAML

from paperclip_blueprints.generators.client import LLMClient
from paperclip_blueprints.models.agent import AgentDefinition
from paperclip_blueprints.renderers.bundle import generate_bundle_full
from paperclip_blueprints.renderers.render import render_files
from paperclip_blueprints.renderers.run_policy import (
    CEO_MAX_CONCURRENT_RUNS,
    DEFAULT_MAX_CONCURRENT_RUNS,
    DEFAULT_MAX_TURNS_PER_RUN,
    POLLER_MAX_TURNS_PER_RUN,
    assign_run_policies,
    derive_run_policy,
)
from test_cli import _dispatch_full
from test_models import _agent_kwargs
from test_orchestration import _brief

# --- pure reasoning ----------------------------------------------------------


def test_defaults_match_the_deployer_defaults() -> None:
    # A plain non-root worker with no poller signal keeps the current deployer behavior.
    p = derive_run_policy(is_root=False, title="Writer", mandate="Draft and polish copy.")
    assert p.max_turns_per_run == DEFAULT_MAX_TURNS_PER_RUN == 30
    assert p.max_concurrent_runs == DEFAULT_MAX_CONCURRENT_RUNS == 2


def test_ceo_gets_tighter_concurrency() -> None:
    p = derive_run_policy(is_root=True, title="CEO", mandate="Owns the north star.")
    assert p.max_concurrent_runs == CEO_MAX_CONCURRENT_RUNS == 1
    assert p.max_turns_per_run == DEFAULT_MAX_TURNS_PER_RUN  # not a poller


def test_bounded_poller_gets_low_turns() -> None:
    p = derive_run_policy(
        is_root=False, title="Signal Monitor", mandate="Monitor the queue and sweep for stalls."
    )
    assert p.max_turns_per_run == POLLER_MAX_TURNS_PER_RUN == 10
    assert p.max_concurrent_runs == DEFAULT_MAX_CONCURRENT_RUNS


def test_poller_signal_is_word_boundaried() -> None:
    # "watchdog"/"sweepstakes" contain poller substrings but must NOT trip the low-turn cap.
    p = derive_run_policy(
        is_root=False, title="Ops", mandate="Run the watchdog demo and sweepstakes launch."
    )
    assert p.max_turns_per_run == DEFAULT_MAX_TURNS_PER_RUN


def test_assign_run_policies_keys_by_slug() -> None:
    ceo = AgentDefinition(**_agent_kwargs(slug="ceo", title="CEO", reports_to=None))
    poller = AgentDefinition(
        **_agent_kwargs(
            slug="poller",
            title="Poller",
            reports_to="ceo",
            mandate="Poll external feeds each hour.",
        )
    )
    policies = assign_run_policies([ceo, poller])
    assert policies["ceo"].max_concurrent_runs == 1
    assert policies["poller"].max_turns_per_run == POLLER_MAX_TURNS_PER_RUN


# --- .paperclip.yaml carrier -------------------------------------------------


def test_paperclip_yaml_carries_per_agent_run_policy() -> None:
    from test_templates import _config

    out = render_files(_config())[".paperclip.yaml"]
    ceo = YAML(typ="safe").load(out)["agents"]["ceo"]["runPolicy"]
    assert ceo == {"maxTurnsPerRun": 30, "maxConcurrentRuns": 1}


def test_full_pipeline_emits_run_policy_for_each_role() -> None:
    config = generate_bundle_full(_brief(), LLMClient(_invoke=_dispatch_full))
    out = render_files(config)[".paperclip.yaml"]
    agents = YAML(typ="safe").load(out)["agents"]
    # CEO (root) → tight concurrency; engineer (non-root worker) → default concurrency.
    assert agents["ceo"]["runPolicy"] == {"maxTurnsPerRun": 30, "maxConcurrentRuns": 1}
    assert agents["engineer"]["runPolicy"] == {"maxTurnsPerRun": 30, "maxConcurrentRuns": 2}
