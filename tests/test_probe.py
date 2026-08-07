"""The cadence-fidelity probe must never bill a plain ``pytest`` run (C6.3).

The probe makes two real model calls. It lives under ``scripts/``, which ``testpaths`` excludes
from collection — a structural exclusion rather than a marker someone can forget. These tests
assert that property and exercise the probe's checking logic against a stubbed transport, so the
logic is covered without any call.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
import tomllib

REPO = pathlib.Path(__file__).resolve().parent.parent
PROBE = REPO / "scripts" / "probe_cadence_fidelity.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("probe_cadence_fidelity", PROBE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # Register before exec: a module loaded this way is otherwise absent from sys.modules, and
    # anything resolving its own __module__ at class-creation time fails.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_probe_lives_outside_the_collected_test_paths() -> None:
    config = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    testpaths = config["tool"]["pytest"]["ini_options"]["testpaths"]
    assert testpaths == ["tests"], "probe exclusion relies on testpaths staying scoped to tests/"
    assert PROBE.exists()
    assert "scripts" not in testpaths


def test_probe_makes_no_call_at_import_time() -> None:
    # Importing must not construct a client or reach the network — the work is behind main().
    module = _load_probe()
    assert hasattr(module, "main")
    assert module.BRIEF_PATH.exists()


def test_probe_detects_a_fully_compliant_plan() -> None:
    """The checks must pass on a plan that kept every stated value."""
    module = _load_probe()
    from paperclip_blueprints.models.org_plan import OrgPlan

    plan = OrgPlan.model_validate(
        {
            "agents": [
                {
                    "slug": "editor",
                    "name": "Editor",
                    "title": "Editor",
                    "reports_to": None,
                    "skills": ["source-verification"],
                },
            ],
            "projects": [{"slug": "reports", "name": "Reports", "owner": "editor"}],
            "tasks": [
                {
                    "slug": "source-sweep",
                    "name": "Source sweep",
                    "project": "reports",
                    "assignee": "editor",
                    "recurrence": {"frequency": "weekly", "days_of_week": ["tue"]},
                },
                {
                    "slug": "list-reconciliation",
                    "name": "List reconciliation",
                    "project": "reports",
                    "assignee": "editor",
                    "depends_on": ["source-sweep"],
                    "recurrence": {"frequency": "monthly", "day_of_month": 5},
                },
                {
                    "slug": "correction-audit",
                    "name": "Correction audit",
                    "project": "reports",
                    "assignee": "editor",
                    "recurrence": {
                        "frequency": "quarterly",
                        "day_of_month": 8,
                        "months": ["jan", "apr", "jul", "oct"],
                    },
                },
            ],
        }
    )
    assert all(fn(plan) for _, _, fn in module.CHECKS)


def test_probe_detects_the_losses_it_exists_to_find() -> None:
    """A plan that discarded every stated day must report every check as lost.

    This is the shape the probe was built for — the pre-018 behaviour, where the planner
    normalised a stated Tuesday to a bare weekly cadence and recorded no dependency.
    """
    module = _load_probe()
    from paperclip_blueprints.models.org_plan import OrgPlan

    plan = OrgPlan.model_validate(
        {
            "agents": [
                {
                    "slug": "editor",
                    "name": "Editor",
                    "title": "Editor",
                    "reports_to": None,
                    "skills": ["source-verification"],
                },
            ],
            "projects": [{"slug": "reports", "name": "Reports", "owner": "editor"}],
            "tasks": [
                {
                    "slug": "source-sweep",
                    "name": "Source sweep",
                    "project": "reports",
                    "assignee": "editor",
                    "recurrence": {"frequency": "weekly"},
                },
                {
                    "slug": "list-reconciliation",
                    "name": "List reconciliation",
                    "project": "reports",
                    "assignee": "editor",
                    "recurrence": {"frequency": "monthly"},
                },
                {
                    "slug": "correction-audit",
                    "name": "Correction audit",
                    "project": "reports",
                    "assignee": "editor",
                    "recurrence": {"frequency": "quarterly"},
                },
            ],
        }
    )
    assert not any(fn(plan) for _, _, fn in module.CHECKS)


def test_probe_brief_parses_and_states_what_the_checks_expect() -> None:
    """The fixture brief must be valid input, and must actually state the values under test.

    A probe whose brief silently stopped stating the 5th would report a loss that was never
    offered — measuring the fixture rather than the planner.
    """
    module = _load_probe()
    from paperclip_blueprints.models.input import parse_brief

    brief = parse_brief(module.BRIEF_PATH.read_text(encoding="utf-8"))
    notes = (brief.use_case_notes or "").lower()
    assert "tuesday" in notes
    assert "5th" in notes
    assert "8th" in notes
    for month in ("january", "april", "july", "october"):
        assert month in notes
    assert "consumes the output" in notes
    assert json.dumps(brief.slug)  # a fully valid brief, not just parseable prose


def test_probe_does_not_render_a_bundle() -> None:
    """C6.1 — plan-only. Rendering would add the per-agent fan-out and answer nothing extra.

    Asserted against the source rather than by running it: the cost property is the reason the
    probe is cheap enough to run repeatedly, and a later edit that reached for `render_files`
    would silently make it expensive.
    """
    source = PROBE.read_text(encoding="utf-8")
    for forbidden in ("render_files", "write_bundle", "generate_bundle", "generate_agent"):
        assert forbidden not in source, f"the probe must not {forbidden} — it plans only"


def test_probe_reports_every_stated_value_it_claims_to() -> None:
    """C6.2 — the summary must cover each stated value, with the brief's wording alongside."""
    module = _load_probe()
    names = [name for name, _, _ in module.CHECKS]
    assert names == ["weekday", "day-of-month", "quarterly", "dependency"]
    for _, stated, fn in module.CHECKS:
        assert stated, "each check names what the brief states, so a summary line is readable"
        assert callable(fn)
