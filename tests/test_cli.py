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
{"agents": [{"slug": "ceo", "name": "CEO", "title": "CEO",
 "reports_to": null, "skills": ["release-checklist"]}], "projects": [], "tasks": []}
```"""

_SOUL = """```json
{"identity": "I am the CEO.", "what_we_are": "A single-title studio.",
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


# --- full multi-agent mocks -------------------------------------------------

_ORG_FULL = """```json
{"agents": [
  {"slug": "ceo", "name": "CEO", "title": "CEO",
   "reports_to": null, "skills": ["release-checklist"]},
  {"slug": "engineer", "name": "Engineer", "title": "Engineer",
   "reports_to": "ceo", "skills": ["release-checklist"]}
 ],
 "projects": [{"slug": "launch-v1", "name": "Launch v1", "owner": "engineer"}],
 "tasks": [{"slug": "ship-build", "name": "Ship the first build",
            "project": "launch-v1", "assignee": "engineer"}]}
```"""

_OPERATIONS = """```json
{"phase_model": "Build, then polish.",
 "idle_state_protocol": "Idle is a success state; wait between heartbeats.",
 "reporting_cadence": "Weekly to the CEO.", "comm_conventions": "Async first.",
 "approval_merge_rules": "The Board is the sole approver; agents escalate, not self-approve.",
 "delegation_checklist": ["Is the goal an outcome?"],
 "anti_drift_checks": ["We are NOT a free-to-play studio.", "We are NOT a multi-title shop.",
                       "One title at a time.", "No dark patterns."],
 "duplicate_prevention": "Check the inventory first.",
 "routine_slots": ["ceo: weekly review"],
 "critical_rules": ["Never ship without sign-off."]}
```"""

_PROJECT = """```json
{"summary": "Ship the first premium build to the store.",
 "success_condition": "A live, signed build that holds a 4.6+ rating."}
```"""

_TASK = """```json
{"objective": "Cut and upload the first release candidate.",
 "completion_criteria": ["Build uploads to the store", "Smoke pass is green"]}
```"""

# Goal-hierarchy owner assignment (ADR-025): one {owner, level} per company goal, in order.
# _IDENTITY carries two goals; assign one to the engineer and keep one cross-cutting.
_GOAL_ASSIGN = """```json
{"assignments": [{"owner": "engineer", "level": "agent"},
                 {"owner": "company", "level": "company"}]}
```"""


def _dispatch_full(**kwargs: object) -> str:
    system = str(kwargs["system"]).lower()
    if "identity" in system:
        return _IDENTITY
    if "org" in system:
        return _ORG_FULL
    if "persona" in system:
        return _SOUL
    if "mandate" in system:
        return _AGENT
    if "ownership" in system:  # goal-hierarchy owner assignment
        return _GOAL_ASSIGN
    if "operations" in system:
        return _OPERATIONS
    if "project" in system:
        return _PROJECT
    if "task" in system:
        return _TASK
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
    # --output IS the bundle root; no slug subdirectory is appended.
    dest = out
    assert not (out / "indie-game-studio").exists(), "must not nest a slug subdir under --output"
    files = {str(p.relative_to(dest)) for p in dest.rglob("*") if p.is_file()}
    assert len(files) == 9
    assert (dest / "COMPANY.md").exists()
    assert (dest / "agents/ceo/SOUL.md").exists()


def test_generate_warns_but_succeeds_on_slug_divergence(tmp_path, monkeypatch) -> None:
    # A brief whose slug diverges from slugify(name) must still generate (divergence
    # can be intentional), while surfacing a non-blocking warning on stderr.
    _patch_client(monkeypatch)
    brief = tmp_path / "brief.md"
    brief.write_text(VALID_BRIEF.replace("**Slug:** indie-game-studio", "**Slug:** keying-test"))
    out = tmp_path / "out"
    result = runner.invoke(
        app, ["generate", "--input", str(brief), "--output", str(out), "--single-agent"]
    )
    assert result.exit_code == 0, result.output
    assert "warning:" in result.output
    assert "keying-test" in result.output
    assert (out / "COMPANY.md").exists()


def test_generate_default_is_full_multi_agent(tmp_path, monkeypatch) -> None:
    _patch_client(monkeypatch, _dispatch_full)
    brief = _write_brief(tmp_path)
    out = tmp_path / "out"
    result = runner.invoke(app, ["generate", "--input", str(brief), "--output", str(out)])
    assert result.exit_code == 0, result.output
    # Full bundle: multiple agents, the operations + inventory files, a project and a task.
    assert (out / "OPERATIONS.md").exists()
    assert (out / "PROJECT-INVENTORY.md").exists()
    assert (out / "agents/ceo/AGENTS.md").exists()
    assert (out / "agents/engineer/AGENTS.md").exists()
    assert (out / "projects/launch-v1/PROJECT.md").exists()
    assert (out / "tasks/ship-build/TASK.md").exists()
    # The README org chart wires the reporting edge.
    assert "ceo --> engineer" in (out / "README.md").read_text()


_OPERATIONS_NO_ECHO = """```json
{"phase_model": "Build then polish.", "idle_state_protocol": "Idle is a success state.",
 "reporting_cadence": "Weekly.", "comm_conventions": "Async.",
 "approval_merge_rules": "The board approves strategy.", "delegation_checklist": ["outcome?"],
 "anti_drift_checks": ["Stay on mission and ship quality work."],
 "duplicate_prevention": "Check the inventory first.",
 "routine_slots": ["ceo: weekly review"], "critical_rules": ["Sign-off before ship."]}
```"""


def test_generate_dumps_failed_bundle_for_inspection(tmp_path, monkeypatch) -> None:
    # An OPERATIONS payload whose anti-drift checks echo none of the constraints
    # fails S7; the rejected bundle must be dumped to <output>-failed/ (#3).
    def failing_ops(**kwargs: object) -> str:
        if "operations" in str(kwargs["system"]).lower():
            return _OPERATIONS_NO_ECHO
        return _dispatch_full(**kwargs)

    _patch_client(monkeypatch, failing_ops)
    brief = _write_brief(tmp_path)
    out = tmp_path / "out"
    result = runner.invoke(app, ["generate", "--input", str(brief), "--output", str(out)])
    assert result.exit_code == 1
    assert not out.exists()  # no valid bundle written
    failed = tmp_path / "out-failed"
    assert failed.exists()
    assert (failed / "OPERATIONS.md").exists()  # the rejected artifact is inspectable
    errors = (failed / "VALIDATION-ERRORS.txt").read_text()
    assert "S7" in errors
    assert "REJECTED" in errors
    assert "-failed" in result.output


def test_generate_prints_cost_summary(tmp_path, monkeypatch) -> None:
    # A usage-reporting transport makes the run print its cost summary (SC-011).
    def with_usage(**kwargs: object) -> tuple[str, tuple[int, int]]:
        return (_dispatch_full(**kwargs), (5, 7))

    _patch_client(monkeypatch, with_usage)
    brief = _write_brief(tmp_path)
    out = tmp_path / "out"
    result = runner.invoke(app, ["generate", "--input", str(brief), "--output", str(out)])
    assert result.exit_code == 0, result.output
    assert "cost:" in result.output
    assert "est. $" in result.output


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
    # A failed generation leaves no bundle at the output dir at all.
    assert not out.exists()


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


def test_generate_writes_into_output_dir_no_slug_subdir(tmp_path, monkeypatch) -> None:
    """--output <dir> writes the bundle INTO <dir>, never <dir>/<slug>/."""
    _patch_client(monkeypatch)
    brief = _write_brief(tmp_path)
    out = tmp_path / "indie-game-studio"
    out.mkdir()  # operator points --output at a dir they already made
    result = runner.invoke(
        app, ["generate", "--input", str(brief), "--output", str(out), "--single-agent"]
    )
    assert result.exit_code == 0, result.output
    # COMPANY.md is a direct child of --output; the slug is NOT doubled.
    assert (out / "COMPANY.md").exists()
    assert not (out / "indie-game-studio").exists()
    assert str(out) in result.output  # reported destination is --output itself


# --- US2: validate (T044) ---------------------------------------------------


def test_validate_clean_brief_exits_zero(tmp_path, monkeypatch) -> None:
    # A clean brief validates with no API call (any client construction fails).
    monkeypatch.setattr(cli_module, "_make_client", _forbid_client())
    brief = _write_brief(tmp_path)
    result = runner.invoke(app, ["validate", "--input", str(brief)])
    assert result.exit_code == 0, result.output
    assert "indie-game-studio" in result.output


# --- US2: pattern validation + seeding (T038) -------------------------------


def test_validate_unknown_pattern_reports_available_set(tmp_path, monkeypatch) -> None:
    # An unknown use-case pattern is reported (FR-015) with zero API calls.
    monkeypatch.setattr(cli_module, "_make_client", _forbid_client())
    p = tmp_path / "brief.md"
    p.write_text(
        VALID_BRIEF.replace("**Your choice:** custom", "**Your choice:** franchise-empire"),
        encoding="utf-8",
    )
    result = runner.invoke(app, ["validate", "--input", str(p)])
    assert result.exit_code == 1
    assert "unknown use-case pattern" in result.output
    assert "solo-dev-shop" in result.output  # the available set is shown


def test_generate_passes_pattern_seed_into_org_planner(tmp_path, monkeypatch) -> None:
    captured: dict[str, str] = {}

    def capturing(**kwargs: object) -> str:
        if "org" in str(kwargs["system"]).lower():
            captured["org_user"] = str(kwargs["user"])
        return _dispatch_full(**kwargs)

    _patch_client(monkeypatch, capturing)
    p = tmp_path / "brief.md"
    p.write_text(
        VALID_BRIEF.replace("**Your choice:** custom", "**Your choice:** solo-dev-shop"),
        encoding="utf-8",
    )
    out = tmp_path / "out"
    result = runner.invoke(app, ["generate", "--input", str(p), "--output", str(out)])
    assert result.exit_code == 0, result.output
    # The solo-dev-shop seed reached the org planner prompt.
    assert "Suggested roles:" in captured["org_user"]
    assert "CTO" in captured["org_user"]


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
