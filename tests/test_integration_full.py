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
