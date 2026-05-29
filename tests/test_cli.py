"""End-to-end CLI tests for `generate --single-agent` (T043), mocked API.

A fake transport dispatches canned JSON by the system prompt so the whole real
pipeline runs without any live Anthropic call.
"""

from pathlib import Path

from typer.testing import CliRunner

import paperclip_blueprints.cli as cli_module
from paperclip_blueprints.cli import app
from paperclip_blueprints.generators.client import LLMClient
from test_models import VALID_BRIEF

runner = CliRunner()

_IDENTITY = """```json
{"name": "Indie Game Studio", "description": "A solo-founder premium puzzle studio.",
 "goals": ["4.6+ rating sustained", "refund rate below 3% per quarter"],
 "we_are": "We are a single-title premium mobile studio.",
 "we_are_not": ["We are NOT a free-to-play studio.", "We are NOT a multi-title shop."],
 "north_star": "$30,000 monthly net revenue within 12 months.",
 "constraints": ["One title at a time.", "No dark patterns."],
 "tone": "purple", "mono": "N", "version": "1.0.0", "tags": []}
```"""

_ORG = """```json
{"slug": "ceo", "name": "Founder / CEO", "title": "Founder / CEO",
 "reports_to": null, "skills": ["release-checklist"]}
```"""

_SOUL = """```json
{"identity": "I am the Founder/CEO.", "what_we_are": "A single-title studio.",
 "product_reality": "One polished game.",
 "beliefs": ["Focus is the moat.", "Idle is a success state; I wait between cycles."],
 "how_i_act": ["I decide quickly on scope."], "what_i_dont_do": ["No dark patterns."],
 "my_north_star": "$30,000 MRR within 12 months."}
```"""

_AGENT = """```json
{"mandate": "Owns the north star and ships the title.",
 "triggers": ["A release candidate is ready."], "receives_from": [], "hands_to": [],
 "deliverables": ["Approved release builds."],
 "can_approve": ["Store metadata within the plan."],
 "must_escalate": ["Pricing changes (budget_override)."],
 "escalation_text": "Escalate to the operator on pricing.",
 "tools_role_specific": "Reviews build status in App Store Connect."}
```"""

_SKILL = """```json
{"slug": "release-checklist", "name": "release-checklist",
 "description": "Pre-submission checklist for a store release.",
 "when_to_load": ["A build is a release candidate."], "inputs": ["The candidate build."],
 "procedure": ["Verify the build number.", "Run the smoke pass."],
 "outputs": ["A signed-off build."], "anti_patterns": ["Shipping without the smoke pass."],
 "references": []}
```"""


def _dispatch(**kwargs: object) -> str:
    system = str(kwargs["system"]).lower()
    if "identity" in system:
        return _IDENTITY
    if "org" in system:
        return _ORG
    if "persona" in system:
        return _SOUL
    if "mandate" in system:
        return _AGENT
    if "skill" in system:
        return _SKILL
    raise AssertionError(f"unexpected system prompt: {system!r}")


def _patch_client(monkeypatch, transport=_dispatch) -> None:
    monkeypatch.setattr(cli_module, "_make_client", lambda: LLMClient(_invoke=transport))


def _write_brief(tmp_path: Path) -> Path:
    p = tmp_path / "brief.md"
    p.write_text(VALID_BRIEF, encoding="utf-8")
    return p


def test_generate_happy_path(tmp_path, monkeypatch) -> None:
    _patch_client(monkeypatch)
    brief = _write_brief(tmp_path)
    out = tmp_path / "out"
    result = runner.invoke(
        app, ["generate", "--input", str(brief), "--output", str(out), "--single-agent"]
    )
    assert result.exit_code == 0, result.output
    dest = out / "indie-game-studio"
    files = {str(p.relative_to(dest)) for p in dest.rglob("*") if p.is_file()}
    assert len(files) == 9
    assert (dest / "COMPANY.md").exists()
    assert (dest / "agents/ceo/SOUL.md").exists()


def test_generate_requires_single_agent_flag(tmp_path, monkeypatch) -> None:
    _patch_client(monkeypatch)
    brief = _write_brief(tmp_path)
    result = runner.invoke(
        app, ["generate", "--input", str(brief), "--output", str(tmp_path / "out")]
    )
    assert result.exit_code == 1
    assert "single-agent" in result.output


def test_generate_invalid_brief_exits_nonzero(tmp_path, monkeypatch) -> None:
    _patch_client(monkeypatch)
    bad = tmp_path / "bad.md"
    bad.write_text("# Empty brief with no sections\n", encoding="utf-8")
    result = runner.invoke(
        app, ["generate", "--input", str(bad), "--output", str(tmp_path / "out"), "--single-agent"]
    )
    assert result.exit_code == 1
    assert "validation failed" in result.output


def test_generate_malformed_response_leaves_no_partial_bundle(tmp_path, monkeypatch) -> None:
    def broken(**kwargs: object) -> str:
        system = str(kwargs["system"]).lower()
        if "identity" in system:
            return _IDENTITY
        return "no json here"  # org step fails

    _patch_client(monkeypatch, broken)
    brief = _write_brief(tmp_path)
    out = tmp_path / "out"
    result = runner.invoke(
        app, ["generate", "--input", str(brief), "--output", str(out), "--single-agent"]
    )
    assert result.exit_code == 1
    assert not (out / "indie-game-studio").exists()


def test_generate_refuses_nonempty_dir_without_force(tmp_path, monkeypatch) -> None:
    _patch_client(monkeypatch)
    brief = _write_brief(tmp_path)
    out = tmp_path / "out"
    first = runner.invoke(
        app, ["generate", "--input", str(brief), "--output", str(out), "--single-agent"]
    )
    assert first.exit_code == 0
    second = runner.invoke(
        app, ["generate", "--input", str(brief), "--output", str(out), "--single-agent"]
    )
    assert second.exit_code == 1
    # with --force it succeeds
    forced = runner.invoke(
        app,
        ["generate", "--input", str(brief), "--output", str(out), "--single-agent", "--force"],
    )
    assert forced.exit_code == 0
