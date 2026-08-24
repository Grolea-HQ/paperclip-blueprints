"""Tests for the bundle validator — schema-shape + integrity (T046).

Builds a valid full bundle, then mutates the config or the rendered files to
trigger each rule. Integrity rules read the structured config (mutated after
construction, which bypasses the model validators); shape rules read the files.
"""

import pytest

from paperclip_blueprints.models.agent import AgentDefinition
from paperclip_blueprints.models.output import CompanyConfig
from paperclip_blueprints.renderers.render import render_files
from paperclip_blueprints.validators import BundleValidationError, validate_bundle
from paperclip_blueprints.validators.integrity import check_integrity
from test_models import _agent_kwargs, _full_config_kwargs


def _valid() -> tuple[CompanyConfig, dict[str, str]]:
    config = CompanyConfig(**_full_config_kwargs())
    return config, render_files(config)


def test_valid_full_bundle_passes() -> None:
    config, files = _valid()
    validate_bundle(config, files)  # must not raise


def test_s16_run_policy_heartbeat_must_be_boolean() -> None:
    # S16 (feature 014): runPolicy.heartbeatEnabled, when present, must be a boolean.
    from paperclip_blueprints.validators.schema_shape import _check_run_policy_fields

    ok = (
        "agents:\n  ceo:\n    runPolicy:\n      maxTurnsPerRun: 30\n"
        "      maxConcurrentRuns: 1\n      heartbeatEnabled: false\n"
    )
    assert _check_run_policy_fields(ok) == []

    bad = (
        "agents:\n  ceo:\n    runPolicy:\n      maxTurnsPerRun: 30\n"
        "      maxConcurrentRuns: 1\n      heartbeatEnabled: maybe\n"
    )
    problems = _check_run_policy_fields(bad)
    assert len(problems) == 1
    assert "S16" in problems[0]
    assert "ceo" in problems[0]


def test_valid_single_bundle_passes() -> None:
    from test_templates import _config

    config = _config()
    validate_bundle(config, render_files(config))


# --- schema-shape rejections ------------------------------------------------


def test_s1_wrong_paperclip_schema() -> None:
    config, files = _valid()
    files[".paperclip.yaml"] = files[".paperclip.yaml"].replace("paperclip/v1", "paperclip/v9")
    with pytest.raises(BundleValidationError, match="S1"):
        validate_bundle(config, files)


def test_s2_missing_agentcompanies_schema() -> None:
    config, files = _valid()
    key = next(k for k in files if k.endswith("TASK.md"))
    files[key] = files[key].replace("agentcompanies/v1", "wrong/v1")
    with pytest.raises(BundleValidationError, match="S2"):
        validate_bundle(config, files)


def test_s6_missing_idle_belief() -> None:
    config, files = _valid()
    key = next(k for k in files if k.endswith("SOUL.md"))
    files[key] = files[key].replace("Idle", "Busy").replace("idle", "busy")
    with pytest.raises(BundleValidationError, match="S6"):
        validate_bundle(config, files)


def test_s7_anti_drift_must_cover_every_constraint() -> None:
    config, files = _valid()
    # Only one of the four constraints/negations is covered; the rest are dropped.
    assert config.operations is not None
    config.operations.anti_drift_checks = ["We are NOT a free-to-play studio."]
    with pytest.raises(BundleValidationError, match="S7"):
        validate_bundle(config, files)


def test_s7_accepts_paraphrased_anti_drift() -> None:
    # Path C: an operational check that REWORDS each item but keeps its distinctive
    # terms must pass — verbatim reproduction is not required (R-003 / ADR-009).
    config, files = _valid()
    assert config.operations is not None
    config.operations.anti_drift_checks = [
        "Before taking work, confirm we keep one title in focus at a time.",
        "Watch monetization for dark patterns and strip them out.",
        "Reject anything that would turn us into a free-to-play studio.",
        "Decline pitches that would make us a multi-title shop.",
    ]
    validate_bundle(config, files)  # must not raise


def test_s9_body_only_file_must_not_carry_schema() -> None:
    config, files = _valid()
    key = next(k for k in files if k.endswith("SOUL.md"))
    files[key] = "---\nschema: agentcompanies/v1\n---\n" + files[key]
    with pytest.raises(BundleValidationError, match="S9"):
        validate_bundle(config, files)


# --- integrity rejections ---------------------------------------------------


def test_i1_two_roots() -> None:
    config, files = _valid()
    config.agents[1].reports_to = None  # now two roots
    with pytest.raises(BundleValidationError, match="I1"):
        validate_bundle(config, files)


def test_i2_unknown_manager() -> None:
    config, files = _valid()
    config.agents[1].reports_to = "ghost"
    with pytest.raises(BundleValidationError, match="I2"):
        validate_bundle(config, files)


def test_i5_dangling_skill_reference() -> None:
    config, files = _valid()
    config.agents[0].skills = ["ghost-skill"]
    with pytest.raises(BundleValidationError, match="I5"):
        validate_bundle(config, files)


def test_i6_dangling_task_project() -> None:
    config, files = _valid()
    config.tasks[0].project = "ghost-project"
    with pytest.raises(BundleValidationError, match="I6"):
        validate_bundle(config, files)


def test_i4_span_of_control() -> None:
    base = _full_config_kwargs()
    ceo = base["agents"][0]
    reports = [
        AgentDefinition(
            **_agent_kwargs(
                slug=f"r{i}",
                name=f"R{i}",
                title=f"R{i}",
                reports_to="ceo",
                skills=["release-checklist"],
            )
        )
        for i in range(8)
    ]
    # model_construct bypasses the CompanyConfig validator so the validator can be
    # exercised on a config that should never have been assembled.
    config = CompanyConfig.model_construct(**{**base, "agents": [ceo, *reports]})
    violations = check_integrity(config, {})
    assert any(x.startswith("I4") for x in violations)


def test_aggregates_multiple_violations() -> None:
    config, files = _valid()
    config.agents[1].reports_to = "ghost"  # I2
    config.tasks[0].assignee = "nobody"  # I6
    with pytest.raises(BundleValidationError) as exc:
        validate_bundle(config, files)
    assert any("I2" in x for x in exc.value.violations)
    assert any("I6" in x for x in exc.value.violations)


# --- per-agent budgets (ADR-012) --------------------------------------------


def _capped() -> tuple[CompanyConfig, dict[str, str]]:
    from paperclip_blueprints.models.input import CompanyBrief
    from test_models import _brief_kwargs

    brief = CompanyBrief(**_brief_kwargs(capital_monthly_eur=100))
    config = CompanyConfig(**_full_config_kwargs(brief=brief))
    return config, render_files(config)


def test_capped_budget_bundle_passes() -> None:
    config, files = _capped()
    validate_bundle(config, files)  # budgets sum within cap → no violation


def test_i11_budgets_exceeding_cap_rejected() -> None:
    config, files = _capped()
    # Inflate one agent's budget past the whole cap (100 EUR = 10000 cents).
    files[".paperclip.yaml"] = files[".paperclip.yaml"].replace(
        "budgetMonthlyCents:", "budgetMonthlyCents: 99999  #", 1
    )
    with pytest.raises(BundleValidationError) as exc:
        validate_bundle(config, files)
    assert any(x.startswith("I11") for x in exc.value.violations)


def test_s10_non_integer_budget_rejected() -> None:
    config, files = _capped()
    files[".paperclip.yaml"] = files[".paperclip.yaml"].replace(
        "budgetMonthlyCents:", "budgetMonthlyCents: 12.5  #", 1
    )
    with pytest.raises(BundleValidationError) as exc:
        validate_bundle(config, files)
    assert any(x.startswith("S10") for x in exc.value.violations)


# --- import fidelity: project slug == slugify(name) (ADR-013) ----------------


def test_i12_project_slug_must_equal_slugify_name() -> None:
    config, files = _valid()
    # the fixture project is "Launch v1" / slug "launch-v1"; break the slug
    config.projects[0].slug = "launch"  # != slugify("Launch v1") == "launch-v1"
    violations = check_integrity(config, files)
    assert any(x.startswith("I12") for x in violations)


def test_i12_allows_collision_suffix() -> None:
    from paperclip_blueprints.validators.integrity import check_integrity

    config, files = _valid()
    # a -N suffix on the slugified base is allowed (matches Paperclip uniqueSlug)
    config.projects[0].name = "Launch"
    config.projects[0].slug = "launch-2"
    assert not any(x.startswith("I12") for x in check_integrity(config, files))


# --- governance: naming guard I13 (ADR-016) ---------------------------------


@pytest.mark.parametrize(
    "value",
    ["Founder / CEO", "Founder", "Co-Founder", "co-founder", "cofounder", "Board", "Board Member"],
)
def test_i13_rejects_founder_board_name(value: str) -> None:
    config, files = _valid()
    config.agents[0].name = value
    violations = check_integrity(config, files)
    assert any(x.startswith("I13") for x in violations)
    assert config.agents[0].slug in " ".join(v for v in violations if v.startswith("I13"))


def test_i13_rejects_reserved_in_title() -> None:
    config, files = _valid()
    config.agents[0].title = "Founder / CEO"
    assert any(x.startswith("I13") for x in check_integrity(config, files))


@pytest.mark.parametrize(
    "value",
    ["CEO", "Managing Editor", "Studio Head", "Growth Lead", "Product Owner", "Store Owner"],
)
def test_i13_allows_legitimate_roles(value: str) -> None:
    config, files = _valid()
    config.agents[0].name = value
    config.agents[0].title = value
    assert not any(x.startswith("I13") for x in check_integrity(config, files))


@pytest.mark.parametrize("value", ["Onboarding Lead", "Billboard Designer", "Boardroom Liaison"])
def test_i13_ignores_substrings(value: str) -> None:
    # reserved words must match standalone tokens, not substrings.
    config, files = _valid()
    config.agents[0].title = value
    assert not any(x.startswith("I13") for x in check_integrity(config, files))


# --- platform: built-in agent name collision I15 ----------------------------


@pytest.mark.parametrize(
    "value",
    [
        "Summarizer",
        "summarizer",
        "Reflection Coach",
        "reflection-coach",
        "Briefs Agent",
        "Learning Agent",
        "  Summarizer  ",
        "REFLECTION COACH",
        "Reflection  Coach",
    ],
)
def test_i15_rejects_builtin_agent_name(value: str) -> None:
    # Paperclip derives an agent's key from its display name, so any name that
    # normalizes onto a built-in's key collides in the shared namespace.
    config, files = _valid()
    config.agents[0].name = value
    violations = check_integrity(config, files)
    assert any(x.startswith("I15") for x in violations)
    assert config.agents[0].slug in " ".join(v for v in violations if v.startswith("I15"))


def test_i15_rejects_builtin_in_title() -> None:
    config, files = _valid()
    config.agents[0].title = "Summarizer"
    assert any(x.startswith("I15") for x in check_integrity(config, files))


@pytest.mark.parametrize(
    "value",
    # Near-misses that do NOT normalize onto a reserved key, and the two registry
    # *keys* whose derived slugs differ ("briefs"/"learning" vs "briefs-agent"/
    # "learning-agent") — reserving those would block legitimate roles.
    [
        "Content Summarizer",
        "Summary Writer",
        "Coach",
        "Briefs",
        "Learning",
        "Learning Designer",
        "Reflection Lead",
    ],
)
def test_i15_allows_non_colliding_names(value: str) -> None:
    config, files = _valid()
    config.agents[0].name = value
    config.agents[0].title = value
    assert not any(x.startswith("I15") for x in check_integrity(config, files))


# --- governance: board-authority presence S11 (ADR-016) ---------------------


def test_s11_passes_with_board_authority() -> None:
    config, files = _valid()  # _operations fixture states the Board is sole approver
    validate_bundle(config, files)  # must not raise on S11 grounds


def test_s11_rejects_missing_board_authority() -> None:
    config, files = _valid()
    ops = files["OPERATIONS.md"]
    # strip every board-authority cue
    for cue in ("Board is the sole approver", "sole approver", "ready for Board review", "Board"):
        ops = ops.replace(cue, "the lead")
    files["OPERATIONS.md"] = ops
    with pytest.raises(BundleValidationError) as exc:
        validate_bundle(config, files)
    assert any(x.startswith("S11") for x in exc.value.violations)


def test_s11_skipped_for_single_agent_bundle() -> None:
    from test_templates import _config

    config = _config()  # single-agent: no OPERATIONS.md
    validate_bundle(config, render_files(config))  # S11 must not fire


# --- per-agent model preference: S12 (ADR-017) ------------------------------


def test_s12_valid_adapter_bundle_passes() -> None:
    config, files = _valid()  # adapters render as claude_local/codex_local, no env
    validate_bundle(config, files)  # must not raise on S12 grounds


def test_s12_rejects_unknown_adapter_type() -> None:
    config, files = _valid()
    files[".paperclip.yaml"] = files[".paperclip.yaml"].replace(
        "type: claude_local", "type: process", 1
    )
    with pytest.raises(BundleValidationError) as exc:
        validate_bundle(config, files)
    assert any(x.startswith("S12") for x in exc.value.violations)


def test_s12_rejects_adapter_env() -> None:
    config, files = _valid()
    # inject an env block under the first agent's adapter.config
    files[".paperclip.yaml"] = files[".paperclip.yaml"].replace(
        "        model: claude-opus-4-8",
        "        model: claude-opus-4-8\n        env:\n          PROVIDER: openrouter",
        1,
    )
    with pytest.raises(BundleValidationError) as exc:
        validate_bundle(config, files)
    assert any(x.startswith("S12") for x in exc.value.violations)


def test_s12_single_agent_bundle_is_clean() -> None:
    from test_templates import _config

    config = _config()  # single agent still carries a valid adapter; no env
    validate_bundle(config, render_files(config))  # must not raise


# --- I16: no carrier asserts a rhythm the bundle has no routine for (feature 024) ---
#
# Contract clauses from specs/024-routine-claim-coherence/contracts/routine-claim-coherence.md.


def _recurring(config: CompanyConfig) -> CompanyConfig:
    """The same bundle with its first task given a cadence, so routines are emitted."""
    from paperclip_blueprints.models.cadence import Cadence

    tasks = list(config.tasks)
    tasks[0] = tasks[0].model_copy(update={"recurrence": Cadence.coerce("tue")})
    return config.model_copy(update={"tasks": tasks})


def test_no_mechanism_term_matches_text_a_template_emits_unconditionally() -> None:
    """The unsatisfiability guard — the most important test in this feature.

    If any I16 term matched text a template always emits, the rule would fire on every
    zero-routine bundle and NO regeneration could ever clear it. That is exactly the trap this
    feature was redesigned to avoid: the original plan was to build the rule without telling the
    generator anything, and it failed precisely because the prompt mandated the language
    unconditionally.

    This renders a clean zero-routine bundle — one whose generated content claims nothing — and
    asserts the rule stays silent. If someone later adds "routine" or "weekly" to the term set,
    this fails before the unsatisfiable rule can ship.
    """
    config, files = _valid()
    assert not any("I16" in v for v in check_integrity(config, files)), (
        "a clean zero-routine bundle must pass; a term matching unconditional template text "
        "would make every zero-cadence brief ungenerable"
    )


def test_i16_operations_asserting_a_scheduled_run_with_no_routines() -> None:
    """C3.1, C3.3, C3.6 (FR-004, FR-005). The reported instruction, verbatim."""
    config, files = _valid()
    files["OPERATIONS.md"] += "\n- On each scheduled run, audit that no gate is unowned.\n"
    findings = [v for v in check_integrity(config, files) if v.startswith("I16")]
    assert len(findings) == 1
    assert "OPERATIONS.md" in findings[0] and "scheduled run" in findings[0]


def test_i16_fires_per_agent_file_not_only_on_operations() -> None:
    """C3.2 (FR-006, SC-003). The leading finding.

    The idle-state protocol is rendered from one source into OPERATIONS.md *and* verbatim into
    every agent's AGENTS.md, where V-gov requires it. A rule that checked only OPERATIONS.md
    would report the visible share of a defect that is already distributed per-agent — which is
    how eight deployed agents each came to carry it.
    """
    config, files = _valid()
    for a in config.agents:
        files[f"agents/{a.slug}/AGENTS.md"] += "\nThe routine schedule is your liveness.\n"
    findings = [v for v in check_integrity(config, files) if v.startswith("I16")]
    assert len(findings) == len(config.agents) >= 2
    for a in config.agents:
        assert any(f"agents/{a.slug}/AGENTS.md" in f for f in findings), (
            f"{a.slug} carries the claim but was not reported"
        )


def test_i16_silent_when_the_bundle_emits_a_routine() -> None:
    """C3.4 (FR-007). With a routine behind it, the claim is true."""
    config = _recurring(CompanyConfig(**_full_config_kwargs()))
    files = render_files(config)
    files["OPERATIONS.md"] += "\n- On each scheduled run, audit that no gate is unowned.\n"
    assert "routines:" in files[".paperclip.yaml"], "fixture must actually emit a routine"
    assert not [v for v in check_integrity(config, files) if v.startswith("I16")]


def test_i16_does_not_fire_on_an_operator_driven_rhythm() -> None:
    """C3.5 (FR-004).

    A cadence adjective describes a rhythm whose actor may be the operator, and that needs no
    routine. Rejecting it would make the rule wrong in the case an operator most likely wrote
    deliberately. The accepted cost is that an adjective-only over-claim is not caught.
    """
    config, files = _valid()
    files["OPERATIONS.md"] += (
        "\n- The operator reviews output weekly and reports monthly to the board.\n"
        "- Each agent approves routine, low-consequence work on its own.\n"
    )
    assert not [v for v in check_integrity(config, files) if v.startswith("I16")]


def test_i16_ignores_single_agent_bundles() -> None:
    """C3.7. No OPERATIONS.md, no OperationsDefinition, nothing propagated."""
    from test_templates import _config

    config = _config()
    files = render_files(config)
    assert not [v for v in check_integrity(config, files) if v.startswith("I16")]


def test_i16_blocks_the_write() -> None:
    """SC-001. A bundle claiming a phantom rhythm does not reach disk."""
    config, files = _valid()
    files["OPERATIONS.md"] += "\n- Work runs on a schedule.\n"
    with pytest.raises(BundleValidationError) as exc:
        validate_bundle(config, files)
    assert any("I16" in v for v in exc.value.violations)
