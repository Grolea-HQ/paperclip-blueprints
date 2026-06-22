"""Integration test (T055): one real Anthropic call generating a FULL bundle.

Gated behind ``--integration`` (see ``conftest.py``) so the default suite never
makes a live call (Constitution III). Requires ``ANTHROPIC_API_KEY`` in the
environment. Generates the full multi-agent bundle from the sanitized
``research-digest`` example brief (which names the content-operations pattern) and
asserts the full-bundle contract holds: a multi-agent org, OPERATIONS.md,
PROJECT-INVENTORY.md, projects, tasks, and a non-zero cost summary (SC-001, SC-002,
SC-008, SC-011). The bundle is validated before write, so a successful run means it
passed the validator.
"""

from pathlib import Path

import pytest

from paperclip_blueprints.generators.client import LLMClient
from paperclip_blueprints.models.input import parse_brief
from paperclip_blueprints.renderers.bundle import build_and_write

_EXAMPLE_BRIEF = (
    Path(__file__).resolve().parent.parent / "examples" / "example-brief-research-digest.md"
)


@pytest.mark.integration
def test_full_bundle_real_api(tmp_path: Path) -> None:
    brief = parse_brief(_EXAMPLE_BRIEF.read_text(encoding="utf-8"))
    client = LLMClient()  # real transport; reads ANTHROPIC_API_KEY from env

    dest = build_and_write(brief, tmp_path, client)  # default = full multi-agent

    # Full-bundle artifacts present.
    assert (dest / "OPERATIONS.md").exists()
    assert (dest / "PROJECT-INVENTORY.md").exists()

    agent_dirs = [d for d in (dest / "agents").iterdir() if d.is_dir()]
    assert len(agent_dirs) >= 2, "a full bundle should plan a multi-agent org"
    for adir in agent_dirs:
        for name in ("AGENTS.md", "SOUL.md", "HEARTBEAT.md", "TOOLS.md"):
            assert (adir / name).exists()

    assert (dest / "projects").is_dir() and any((dest / "projects").iterdir())
    assert (dest / "tasks").is_dir() and any((dest / "tasks").iterdir())
    assert (dest / "skills").is_dir() and any((dest / "skills").iterdir())

    # The identity is the operator's, not a reference company regenerated.
    company_md = (dest / "COMPANY.md").read_text(encoding="utf-8").lower()
    assert "research digest" in company_md
    for ref in ("newsletter-press", "niche-site-empire", "agency-engine", "membership-stack"):
        assert ref not in company_md

    # The run reported a cost (SC-011).
    assert client.usage_summary()["total"]["calls"] > 0


# Platforms/tools the company works with (subject matter) — never the company (ADR-018).
_PLATFORM_POSSESSIVES = ("Paperclip's", "Hermes's", "OpenClaw's")

_PLATFORM_HEAVY_BRIEF = """\
# Company Brief

## 1. Company name and slug

**Name:** Prospector

**Slug:** prospector

**One-sentence description:** An opportunity-discovery company surfacing leads from public repos.

## 2. North star

**Your north star:**

Surface 50 operator-qualified opportunities per month within 6 months.

## 3. Goals

**Your goals:**

1. Maintain a 70%+ relevance rate on surfaced opportunities
2. Keep scan-to-surface latency under 24 hours

## 4. We are

**Your "we are" paragraph:**

We are an opportunity-discovery company. We continuously scan the Paperclip ecosystem,
Hermes runtimes, OpenClaw gateways, and GitHub watchlist repositories to surface
high-signal opportunities for the operator. Paperclip, Hermes, and OpenClaw are the
platforms we observe — they are our subject matter, not us.

## 5. We are NOT

**Your "we are not" list:**

1. **We are NOT** a Paperclip plugin. We observe the platform; we do not build on it.
2. **We are NOT** a general web scraper. We focus on the Paperclip / Hermes / OpenClaw ecosystem.

## 6. Constraints

**Your constraints:**

1. Every opportunity is source-attributed to its origin repository.
2. We never modify the platforms we scan; observation only.

## 7. Use case pattern (optional)

**Your choice:** custom

## 8. Governance spectrum position

**Your choice:** balanced
"""


@pytest.mark.integration
def test_platform_name_does_not_bleed_into_company_identity(tmp_path: Path) -> None:
    """A platform-heavy brief must not let a platform name stand in as the company.

    The brief names Paperclip/Hermes/OpenClaw/GitHub heavily as subject matter; the
    company is "Prospector". Asserts the company's own name appears in every agent's
    AGENTS.md mandate and that no platform name appears as a possessive company
    referent (e.g. "Paperclip's") in COMPANY.md, the AGENTS.md files, or OPERATIONS.md
    (ADR-018). Legitimate non-possessive platform mentions ("scans the Paperclip repo")
    are expected and allowed.
    """
    brief = parse_brief(_PLATFORM_HEAVY_BRIEF)
    assert brief.name == "Prospector"
    client = LLMClient()  # real transport

    dest = build_and_write(brief, tmp_path, client)

    company_referent_files = [dest / "COMPANY.md", dest / "OPERATIONS.md"]
    for adir in (d for d in (dest / "agents").iterdir() if d.is_dir()):
        agents_md = (adir / "AGENTS.md").read_text(encoding="utf-8")
        # The company's own name must appear in the mandate.
        assert "Prospector" in agents_md, f"{adir.name}/AGENTS.md never names the company"
        company_referent_files.append(adir / "AGENTS.md")

    for f in company_referent_files:
        text = f.read_text(encoding="utf-8")
        for poss in _PLATFORM_POSSESSIVES:
            assert poss not in text, f"{f.name} uses {poss!r} as a company referent (ADR-018)"
