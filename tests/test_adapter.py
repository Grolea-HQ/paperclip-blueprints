"""Unit tests for the per-agent model-preference assigner (ADR-017, contract A1-A7)."""

from paperclip_blueprints.config import PORTABLE_ADAPTER_TYPES
from paperclip_blueprints.renderers.adapter import AdapterChoice, assign_adapters


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
