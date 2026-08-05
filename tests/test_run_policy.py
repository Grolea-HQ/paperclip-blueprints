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
    RunPolicyOverride,
    assign_run_policies,
    derive_run_policy,
    peer_turn_asymmetry,
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


def test_poller_signal_comes_from_the_title_not_the_mandate_prose() -> None:
    # A reviewer whose mandate merely *mentions* monitoring is not a bounded poller: the role
    # identity lives in the title. Matching prose let one word triple a reviewer's cap
    # downward. The failure directions are asymmetric — a too-tight cap fails silently (the
    # agent returns a thin verdict, not an error) while a too-loose cap fails visibly (cost),
    # so an uncertain signal must resolve to the looser cap.
    p = derive_run_policy(
        is_root=False,
        title="Evidence Reviewer",
        mandate="Monitor incoming evidence and sweep the register for stale claims.",
    )
    assert p.max_turns_per_run == DEFAULT_MAX_TURNS_PER_RUN


def test_poller_signal_is_word_boundaried() -> None:
    # "watchdog"/"sweepstakes" contain poller substrings but must NOT trip the low-turn cap.
    p = derive_run_policy(
        is_root=False, title="Ops", mandate="Run the watchdog demo and sweepstakes launch."
    )
    assert p.max_turns_per_run == DEFAULT_MAX_TURNS_PER_RUN


def test_peers_under_one_manager_with_different_turn_caps_are_warned() -> None:
    # Two reviewers reporting to the same lead, one classified a poller: the asymmetry is
    # reported so the operator can judge it. Advisory only — it never rewrites a cap, because
    # normalizing would propagate the majority value, and a majority of poller-classified
    # peers would drag a correct 30 down to 10 (the silent-failure direction).
    lead = AgentDefinition(**_agent_kwargs(slug="lead", title="Lead", reports_to="ceo"))
    watcher = AgentDefinition(
        **_agent_kwargs(slug="watcher", title="Queue Monitor", reports_to="lead")
    )
    reviewer = AgentDefinition(
        **_agent_kwargs(slug="reviewer", title="Evidence Reviewer", reports_to="lead")
    )
    agents = [lead, watcher, reviewer]
    warnings = peer_turn_asymmetry(agents, assign_run_policies(agents))
    assert len(warnings) == 1
    assert "'lead'" in warnings[0]
    assert "watcher" in warnings[0] and "reviewer" in warnings[0]


def test_peers_with_matching_turn_caps_are_not_warned() -> None:
    lead = AgentDefinition(**_agent_kwargs(slug="lead", title="Lead", reports_to="ceo"))
    a = AgentDefinition(**_agent_kwargs(slug="a", title="Evidence Reviewer", reports_to="lead"))
    b = AgentDefinition(**_agent_kwargs(slug="b", title="Feasibility Reviewer", reports_to="lead"))
    agents = [lead, a, b]
    assert peer_turn_asymmetry(agents, assign_run_policies(agents)) == []


def test_operator_stated_turn_caps_do_not_trip_the_asymmetry_warning() -> None:
    # A brief that names an agent's turns is an authority statement, not an accident (ADR-034).
    lead = AgentDefinition(**_agent_kwargs(slug="lead", title="Lead", reports_to="ceo"))
    a = AgentDefinition(**_agent_kwargs(slug="a", title="Evidence Reviewer", reports_to="lead"))
    b = AgentDefinition(**_agent_kwargs(slug="b", title="Feasibility Reviewer", reports_to="lead"))
    agents = [lead, a, b]
    overrides = {"b": RunPolicyOverride(max_turns_per_run=8)}
    policies = assign_run_policies(agents, overrides)
    assert policies["b"].max_turns_per_run == 8  # the override landed
    assert peer_turn_asymmetry(agents, policies, overrides) == []


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


# --- brief-driven override layer (feature 014, ADR-034) ----------------------

import pytest  # noqa: E402

from paperclip_blueprints.renderers.run_policy import (  # noqa: E402
    RunPolicy,
    parse_run_policy_line,
    parse_run_policy_preferences,
)


def _ag(slug: str, *, title: str = "Worker", reports_to: str | None = "ceo") -> AgentDefinition:
    return AgentDefinition(**_agent_kwargs(slug=slug, title=title, reports_to=reports_to))


# tri-state dataclasses


def test_run_policy_heartbeat_defaults_none() -> None:
    p = RunPolicy(max_turns_per_run=30, max_concurrent_runs=2)
    assert p.heartbeat_enabled is None


def test_run_policy_override_all_fields_default_none() -> None:
    o = RunPolicyOverride()
    assert (o.max_turns_per_run, o.max_concurrent_runs, o.heartbeat_enabled) == (None, None, None)


# line parsing


def test_parse_line_turns_and_concurrent() -> None:
    ref, o = parse_run_policy_line("research-analyst: max turns 8, max concurrent 1")
    assert ref == "research-analyst"
    assert o.max_turns_per_run == 8
    assert o.max_concurrent_runs == 1
    assert o.heartbeat_enabled is None


def test_parse_line_heartbeat_off_and_on() -> None:
    assert parse_run_policy_line("ceo: heartbeat off")[1].heartbeat_enabled is False
    assert parse_run_policy_line("ceo: heartbeat on")[1].heartbeat_enabled is True


def test_parse_line_aliases_and_case() -> None:
    _, o = parse_run_policy_line("X: Turns 5, Concurrency 3, Heartbeat Disabled")
    assert (o.max_turns_per_run, o.max_concurrent_runs, o.heartbeat_enabled) == (5, 3, False)


@pytest.mark.parametrize(
    "bad",
    [
        "no colon here",
        "ceo:",  # no clause
        "ceo: max turns 0",  # non-positive
        "ceo: max turns -3",
        "ceo: max turns abc",  # non-integer
        "ceo: max concurrent 0",
        "ceo: heartbeat maybe",  # bad token
        "ceo: frobnicate 5",  # unknown clause
        "ceo: max turns 5, max turns 8",  # within-line conflict
    ],
)
def test_parse_line_malformed_raises(bad: str) -> None:
    with pytest.raises(ValueError):
        parse_run_policy_line(bad)


# reference → agent matching


def test_parse_prefs_none_returns_empty() -> None:
    assert parse_run_policy_preferences(None, []) == ({}, [])


def test_parse_prefs_matches_by_slug() -> None:
    agents = [_ag("ceo", title="CEO", reports_to=None), _ag("research-analyst", title="Analyst")]
    overrides, unmatched = parse_run_policy_preferences(["research-analyst: max turns 8"], agents)
    assert unmatched == []
    assert overrides["research-analyst"].max_turns_per_run == 8


def test_parse_prefs_is_boundary_safe() -> None:
    agents = [_ag("senior-analyst", title="Senior Analyst")]
    overrides, unmatched = parse_run_policy_preferences(["analyst: max turns 5"], agents)
    assert overrides == {}
    assert unmatched == ["analyst: max turns 5"]


def test_parse_prefs_unmatched_reference_reported() -> None:
    agents = [_ag("ceo", title="CEO", reports_to=None)]
    overrides, unmatched = parse_run_policy_preferences(["ghost: heartbeat off"], agents)
    assert overrides == {}
    assert unmatched == ["ghost: heartbeat off"]


# per-field overlay merge


def test_assign_overlay_is_per_field() -> None:
    ceo = _ag("ceo", title="CEO", reports_to=None)
    eng = _ag("engineer", title="Engineer")
    overrides = {"engineer": RunPolicyOverride(max_turns_per_run=8)}
    policies = assign_run_policies([ceo, eng], overrides)
    assert policies["engineer"].max_turns_per_run == 8  # overridden
    assert policies["engineer"].max_concurrent_runs == DEFAULT_MAX_CONCURRENT_RUNS  # base kept
    # other agent identical to a no-override run
    assert policies["ceo"] == assign_run_policies([ceo, eng])["ceo"]


def test_assign_no_overrides_is_identical_to_today() -> None:
    ceo = _ag("ceo", title="CEO", reports_to=None)
    eng = _ag("engineer", title="Engineer")
    base = assign_run_policies([ceo, eng])
    assert assign_run_policies([ceo, eng], None) == base
    assert assign_run_policies([ceo, eng], {}) == base


def test_assign_heartbeat_only_from_override() -> None:
    eng = _ag("engineer", title="Engineer")
    policies = assign_run_policies([eng], {"engineer": RunPolicyOverride(heartbeat_enabled=False)})
    assert policies["engineer"].heartbeat_enabled is False
    # an unmentioned agent stays None
    assert assign_run_policies([eng], {})["engineer"].heartbeat_enabled is None


# render-path carrier


def test_render_emits_overrides_and_warns_unmatched() -> None:
    config = generate_bundle_full(_brief(), LLMClient(_invoke=_dispatch_full))
    config.brief.run_policy_preferences = [
        "engineer: max turns 8, heartbeat off",
        "ghost: heartbeat on",
    ]
    warnings: list[str] = []
    out = render_files(config, warn=warnings.append)[".paperclip.yaml"]
    agents = YAML(typ="safe").load(out)["agents"]
    assert agents["engineer"]["runPolicy"]["maxTurnsPerRun"] == 8
    assert agents["engineer"]["runPolicy"]["maxConcurrentRuns"] == 2  # base kept
    assert agents["engineer"]["runPolicy"]["heartbeatEnabled"] is False
    # unmentioned agent unchanged, no heartbeat key
    assert agents["ceo"]["runPolicy"] == {"maxTurnsPerRun": 30, "maxConcurrentRuns": 1}
    assert any("ghost" in w for w in warnings)


def test_render_heartbeat_key_absent_when_unstated() -> None:
    config = generate_bundle_full(_brief(), LLMClient(_invoke=_dispatch_full))
    out = render_files(config)[".paperclip.yaml"]
    assert "heartbeatEnabled" not in out
