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


def test_s7_anti_drift_must_echo_constraints() -> None:
    config, files = _valid()
    # Drop a constraint from the operations anti-drift checks.
    assert config.operations is not None
    config.operations.anti_drift_checks = ["We are NOT a free-to-play studio."]
    with pytest.raises(BundleValidationError, match="S7"):
        validate_bundle(config, files)


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
