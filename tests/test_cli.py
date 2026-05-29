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


def _forbid_client():
    """A ``_make_client`` replacement that fails the test if ever called.

    Used to prove `validate` (and a pre-API `preview` abort) make zero API calls.
    """

    def _factory() -> LLMClient:
        raise AssertionError("no Anthropic client may be constructed here")

    return _factory


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
 "must_escalate": ["Pricing changes."],
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


# --- US2: validate (T044) ---------------------------------------------------


def test_validate_clean_brief_exits_zero(tmp_path, monkeypatch) -> None:
    # A clean brief validates with no API call (any client construction fails).
    monkeypatch.setattr(cli_module, "_make_client", _forbid_client())
    brief = _write_brief(tmp_path)
    result = runner.invoke(app, ["validate", "--input", str(brief)])
    assert result.exit_code == 0, result.output
    assert "indie-game-studio" in result.output


def test_validate_defective_brief_lists_all_violations(tmp_path, monkeypatch) -> None:
    # Two independent violations must BOTH be reported (FR-002 aggregation),
    # and still no API call is made.
    monkeypatch.setattr(cli_module, "_make_client", _forbid_client())
    bad = VALID_BRIEF.replace("**Slug:** indie-game-studio", "**Slug:** Indie Studio").replace(
        "2. **We are NOT** a multi-title shop. We do not split focus; "
        "the live title gets all attention.\n",
        "",
    )
    p = tmp_path / "bad.md"
    p.write_text(bad, encoding="utf-8")
    result = runner.invoke(app, ["validate", "--input", str(p)])
    assert result.exit_code == 1
    assert "slug" in result.output
    assert "we are not" in result.output.lower()


# --- US3: preview (T046) ----------------------------------------------------


def test_preview_prints_only_company_md_to_stdout(tmp_path, monkeypatch) -> None:
    _patch_client(monkeypatch)
    brief = _write_brief(tmp_path)
    result = runner.invoke(app, ["preview", "--input", str(brief)])
    assert result.exit_code == 0, result.output
    assert "schema: agentcompanies/v1" in result.output
    assert "# Indie Game Studio" in result.output
    # No bundle directory or sibling files are produced.
    assert not (tmp_path / "indie-game-studio").exists()


def test_preview_makes_exactly_one_identity_call(tmp_path, monkeypatch) -> None:
    calls: list[str] = []

    def counting(**kwargs: object) -> str:
        calls.append(str(kwargs["system"]).lower())
        return _dispatch(**kwargs)

    _patch_client(monkeypatch, counting)
    brief = _write_brief(tmp_path)
    result = runner.invoke(app, ["preview", "--input", str(brief)])
    assert result.exit_code == 0, result.output
    assert len(calls) == 1
    assert "identity" in calls[0]


def test_preview_output_flag_writes_only_company_md(tmp_path, monkeypatch) -> None:
    _patch_client(monkeypatch)
    brief = _write_brief(tmp_path)
    out = tmp_path / "preview" / "COMPANY.md"
    result = runner.invoke(app, ["preview", "--input", str(brief), "--output", str(out)])
    assert result.exit_code == 0, result.output
    assert out.exists()
    assert "schema: agentcompanies/v1" in out.read_text(encoding="utf-8")
    # Only COMPANY.md lands in the output dir — no .paperclip.yaml/README/agent/skill.
    assert [p.name for p in out.parent.iterdir()] == ["COMPANY.md"]


def test_preview_invalid_brief_aborts_before_api(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(cli_module, "_make_client", _forbid_client())
    bad = tmp_path / "bad.md"
    bad.write_text("# Empty brief with no sections\n", encoding="utf-8")
    result = runner.invoke(app, ["preview", "--input", str(bad)])
    assert result.exit_code == 1
    assert "validation failed" in result.output
