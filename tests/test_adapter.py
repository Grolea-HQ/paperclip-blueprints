"""Unit tests for the per-agent model-preference assigner (ADR-017, contract A1-A7)."""

from dataclasses import dataclass

from paperclip_blueprints.config import OPUS_MODEL, PORTABLE_ADAPTER_TYPES, SONNET_MODEL
from paperclip_blueprints.models.input import CompanyBrief
from paperclip_blueprints.models.output import CompanyConfig
from paperclip_blueprints.renderers.adapter import (
    AdapterChoice,
    assign_adapters,
    parse_model_preferences,
)
from paperclip_blueprints.renderers.render import render_files
from test_models import _brief_kwargs, _full_config_kwargs


@dataclass
class _Ag:
    """Minimal agent stand-in — parse_model_preferences reads only slug/title/name."""

    slug: str
    title: str
    name: str


def test_owner_gets_claude_local_opus() -> None:
    out = assign_adapters({"ceo": "owner"})
    assert out["ceo"] == AdapterChoice("claude_local", "claude-opus-4-8")


def test_non_owner_roles_get_claude_local_sonnet() -> None:
    # Default: every non-owner role runs on claude_local/Sonnet — a single provider
    # out of the box (engineering included; Sonnet is strong at code).
    out = assign_adapters({"mgr": "manager", "gen": "generic", "eng": "engineering"})
    assert out["mgr"] == AdapterChoice("claude_local", "claude-sonnet-4-6")
    assert out["gen"] == AdapterChoice("claude_local", "claude-sonnet-4-6")
    assert out["eng"] == AdapterChoice("claude_local", "claude-sonnet-4-6")


def test_every_default_choice_is_claude_local() -> None:
    out = assign_adapters({"a": "owner", "b": "manager", "c": "engineering", "d": "generic"})
    assert {c.type for c in out.values()} == {"claude_local"}


def test_codex_is_a_supported_alternative_worker() -> None:
    # codex_local stays first-class: env-free, in the import-safe allowlist, ready
    # to opt into by assigning CODEX_ALTERNATIVE to a role (one-line change).
    from paperclip_blueprints.renderers.adapter import CODEX_ALTERNATIVE

    assert CODEX_ALTERNATIVE == AdapterChoice("codex_local", "gpt-5.3-codex")
    assert CODEX_ALTERNATIVE.type in PORTABLE_ADAPTER_TYPES


def test_every_type_is_import_safe_and_no_env() -> None:
    roles = {"ceo": "owner", "mgr": "manager", "eng": "engineering", "ops": "generic"}
    out = assign_adapters(roles)
    for choice in out.values():
        assert choice.type in PORTABLE_ADAPTER_TYPES
        # AdapterChoice has only type + model — there is no env field at all.
        assert not hasattr(choice, "env")


def test_covers_exactly_the_input_agents() -> None:
    roles = {"a": "owner", "b": "manager", "c": "engineering"}
    assert set(assign_adapters(roles)) == set(roles)


def test_deterministic() -> None:
    roles = {"ceo": "owner", "eng": "engineering", "ops": "generic"}
    assert assign_adapters(roles) == assign_adapters(roles)


# --- honoring explicit per-role model preferences (v0.1, refines ADR-017) ----


def test_explicit_non_owner_opus_preference_overrides_the_default() -> None:
    agents = [_Ag("senior-analyst", "Senior Analyst", "Senior Analyst")]
    overrides, unmatched = parse_model_preferences(["Senior Analyst → Opus-tier"], agents)
    assert overrides == {"senior-analyst": OPUS_MODEL}
    assert unmatched == []
    # applied: the role's MODEL flips to Opus; the TYPE stays the env-free default.
    out = assign_adapters({"senior-analyst": "generic"}, overrides)
    assert out["senior-analyst"] == AdapterChoice("claude_local", "claude-opus-4-8")


def test_unspecified_roles_keep_the_default() -> None:
    agents = [_Ag("cto", "CTO", "CTO"), _Ag("analyst", "Analyst", "Analyst")]
    overrides, _ = parse_model_preferences(["CTO → Sonnet-tier"], agents)
    out = assign_adapters({"ceo": "owner", "cto": "manager", "analyst": "generic"}, overrides)
    assert out["ceo"] == AdapterChoice("claude_local", OPUS_MODEL)  # owner default untouched
    assert out["cto"] == AdapterChoice("claude_local", SONNET_MODEL)  # explicit (== default here)
    assert out["analyst"] == AdapterChoice("claude_local", SONNET_MODEL)  # default


def test_override_keeps_type_import_safe_and_no_env() -> None:
    out = assign_adapters({"analyst": "generic"}, {"analyst": OPUS_MODEL})
    assert out["analyst"].type in PORTABLE_ADAPTER_TYPES
    assert not hasattr(out["analyst"], "env")


def test_matches_by_title_when_slug_differs() -> None:
    agents = [_Ag("sa", "Senior Analyst", "Ana")]
    overrides, unmatched = parse_model_preferences(["Senior Analyst → Opus-tier"], agents)
    assert overrides == {"sa": OPUS_MODEL} and unmatched == []


def test_boundary_match_avoids_substring_false_positive() -> None:
    agents = [_Ag("analyst", "Analyst", "Analyst"), _Ag("senior-analyst", "Senior Analyst", "SA")]
    overrides, _ = parse_model_preferences(["senior-analyst → Opus"], agents)
    assert overrides == {"senior-analyst": OPUS_MODEL}  # not "analyst"


def test_non_tier_line_is_skipped_not_unmatched() -> None:
    agents = [_Ag("eng", "Engineer", "Eng")]
    overrides, unmatched = parse_model_preferences(["All engineers → codexlocal"], agents)
    assert overrides == {} and unmatched == []


def test_tier_line_matching_no_agent_is_reported_unmatched() -> None:
    agents = [_Ag("ceo", "CEO", "CEO")]
    overrides, unmatched = parse_model_preferences(["Ghost Role → Opus-tier"], agents)
    assert overrides == {} and unmatched == ["Ghost Role → Opus-tier"]


def test_no_preferences_returns_defaults() -> None:
    assert parse_model_preferences(None, [_Ag("ceo", "CEO", "CEO")]) == ({}, [])


# --- end-to-end through render_files → .paperclip.yaml ------------------------


def test_paperclip_yaml_honors_a_non_owner_opus_preference() -> None:
    brief = CompanyBrief(**_brief_kwargs(adapter_preferences=["CTO → Opus-tier"]))
    config = CompanyConfig(**_full_config_kwargs(brief=brief))
    y = render_files(config)[".paperclip.yaml"]
    # the CTO (a non-owner, Sonnet by default) now ships Opus in .paperclip.yaml
    cto_block = y[y.index("cto:") : y.index("cto:") + 160]
    assert "claude-opus-4-8" in cto_block


def test_unmatched_preference_warns_via_the_warn_sink() -> None:
    brief = CompanyBrief(**_brief_kwargs(adapter_preferences=["Nonexistent Role → Opus-tier"]))
    config = CompanyConfig(**_full_config_kwargs(brief=brief))
    warnings: list[str] = []
    render_files(config, warn=warnings.append)
    assert any("matched no agent role" in w for w in warnings)
