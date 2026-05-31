"""Integration smoke test (T048): one real Anthropic call, end to end.

Gated behind ``--integration`` (see ``conftest.py``) so the default suite never
makes a live call (Constitution III). Requires ``ANTHROPIC_API_KEY`` in the
environment. Generates a single-agent bundle from the sanitized example brief and
asserts the 9-file contract holds and the identity reflects the brief, not a
reference company (SC-001, SC-002, SC-004).
"""

from pathlib import Path

import pytest

from paperclip_blueprints.generators.client import LLMClient
from paperclip_blueprints.models.input import parse_brief
from paperclip_blueprints.renderers.bundle import build_and_write

_EXAMPLE_BRIEF = (
    Path(__file__).resolve().parent.parent / "examples" / "example-brief-indie-game-studio.md"
)


@pytest.mark.integration
def test_single_agent_bundle_real_api(tmp_path: Path) -> None:
    brief = parse_brief(_EXAMPLE_BRIEF.read_text(encoding="utf-8"))
    client = LLMClient()  # real transport; reads ANTHROPIC_API_KEY from env

    dest = build_and_write(brief, tmp_path, client, single_agent=True)

    files = {str(p.relative_to(dest)) for p in dest.rglob("*") if p.is_file()}
    assert len(files) == 9
    assert (dest / "COMPANY.md").exists()
    assert (dest / f"agents/{brief.slug}").exists() or (dest / "agents").is_dir()

    # The identity must be the operator's, not a reference company regenerated.
    company_md = (dest / "COMPANY.md").read_text(encoding="utf-8").lower()
    assert "newsletter-press" not in company_md
    assert "niche-site-empire" not in company_md
