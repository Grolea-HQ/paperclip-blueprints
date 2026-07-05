"""Per-agent capability derivation and carrier (ADR-026).

Covers the deterministic, conservative role/mandate → capability mapping (scanner/research
→ read-only web-fetch; a role with no special need → none), the model's known-capability
validation, the AGENTS.md frontmatter carrier, and the end-to-end pipeline attachment.
"""

from __future__ import annotations

import pytest

from paperclip_blueprints.generators.client import LLMClient
from paperclip_blueprints.models.agent import AgentDefinition
from paperclip_blueprints.patterns.capabilities import (
    WEB_FETCH,
    attach_capabilities,
    derive_capabilities,
)
from paperclip_blueprints.renderers.bundle import generate_bundle_full
from paperclip_blueprints.renderers.render import render_files
from test_cli import _dispatch_full
from test_models import _agent_kwargs
from test_orchestration import _brief

# --- pure derivation ---------------------------------------------------------


def test_scanner_role_gets_web_fetch() -> None:
    caps = derive_capabilities(
        role=None,
        title="Market Scanner",
        mandate="Scan external sources and fetch web pages for early signals.",
    )
    assert caps == [WEB_FETCH]


def test_research_role_gets_web_fetch() -> None:
    caps = derive_capabilities(
        role=None, title="Research Analyst", mandate="Research online trends every week."
    )
    assert caps == [WEB_FETCH]


def test_role_with_no_web_need_gets_nothing() -> None:
    assert derive_capabilities(
        role="ceo", title="CEO", mandate="Owns the north star and ships the title."
    ) == []
    assert derive_capabilities(
        role=None, title="Editor", mandate="Edit and polish drafts before publication."
    ) == []


def test_derivation_is_word_boundaried_not_substring() -> None:
    # "resource"/"outsource" contain "source" but must NOT trip the web-fetch grant.
    assert derive_capabilities(
        role=None, title="Ops Lead", mandate="Allocate resources and outsource nothing."
    ) == []


# --- attach + model validation -----------------------------------------------


def test_attach_sets_capabilities_by_role() -> None:
    scanner = AgentDefinition(
        **_agent_kwargs(
            slug="scanner",
            name="Scanner",
            title="Scanner",
            reports_to="ceo",
            mandate="Scan the web for leads.",
        )
    )
    editor = AgentDefinition(
        **_agent_kwargs(
            slug="editor", name="Editor", title="Editor", reports_to="ceo", mandate="Polish copy."
        )
    )
    attach_capabilities([scanner, editor])
    assert scanner.capabilities == [WEB_FETCH]
    assert editor.capabilities == []


def test_model_rejects_unknown_capability() -> None:
    with pytest.raises(ValueError, match="unknown capability"):
        AgentDefinition(**_agent_kwargs(capabilities=["root-shell"]))


def test_capabilities_default_empty_backward_compat() -> None:
    agent = AgentDefinition(**_agent_kwargs())  # no capabilities passed
    assert agent.capabilities == []


# --- carrier: AGENTS.md frontmatter ------------------------------------------


def test_agents_md_frontmatter_carries_capabilities() -> None:
    from ruamel.yaml import YAML

    from test_templates import _config

    config = _config()
    config.agents[0].capabilities = [WEB_FETCH]
    fm = render_files(config)["agents/ceo/AGENTS.md"].split("---\n", 2)[1]
    assert YAML(typ="safe").load(fm)["capabilities"] == [WEB_FETCH]


# --- end-to-end pipeline attachment ------------------------------------------


def test_full_pipeline_attaches_capabilities_field_to_every_agent() -> None:
    config = generate_bundle_full(_brief(), LLMClient(_invoke=_dispatch_full))
    # every agent carries the structured field; the canned CEO/engineer roles need no web
    # access, so it is empty for them (D7 no-op) — conservative by default.
    for agent in config.agents:
        assert agent.capabilities == []
    fm = render_files(config)["agents/engineer/AGENTS.md"]
    assert "capabilities:" in fm
