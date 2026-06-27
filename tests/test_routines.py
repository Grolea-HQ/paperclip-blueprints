"""Focused tests for the PROVISIONAL routines emission (ADR-022, US3).

Isolated on purpose: a live-import correction to the routine shape should be a contained,
single-file change to ``renderers/routines.py`` (+ this test file). All offline.
"""

from __future__ import annotations

from paperclip_blueprints.models.output import CompanyConfig
from paperclip_blueprints.renderers.render import render_files
from paperclip_blueprints.renderers.routines import derive_routines, routine_task_files
from test_models import _full_config_kwargs


def test_derive_routines_maps_slot_to_spec() -> None:
    specs = derive_routines(["ceo: weekly review"], {"ceo", "cto"}, ["launch-v1"])
    assert len(specs) == 1
    r = specs[0]
    assert r.assignee == "ceo"
    assert r.project == "launch-v1"  # provisional anchor: first project
    assert r.slug == "ceo-weekly-review"
    assert r.cron == "0 9 * * 1"  # weekly cadence keyword
    assert r.timezone == "UTC"
    assert r.concurrency_policy == "coalesce_if_active"
    assert r.catch_up_policy == "skip_missed"


def test_derive_routines_cadence_keywords() -> None:
    def cron(slot: str) -> str:
        return derive_routines([slot], {"a"}, ["p"])[0].cron

    assert cron("a: daily standup") == "0 9 * * *"
    assert cron("a: monthly report") == "0 9 1 * *"
    assert cron("a: something custom") == "0 9 * * 1"  # weekly fallback


def test_derive_routines_empty_without_project_or_unknown_agent() -> None:
    assert derive_routines(["ceo: weekly review"], {"ceo"}, []) == []  # no project to anchor
    assert derive_routines(["ghost: weekly"], {"ceo"}, ["p"]) == []  # unknown agent


def test_derive_routines_dedupes_slugs() -> None:
    specs = derive_routines(["ceo: review", "ceo: review"], {"ceo"}, ["p"])
    assert [s.slug for s in specs] == ["ceo-review", "ceo-review-2"]


def test_routine_task_files_carry_required_frontmatter() -> None:
    specs = derive_routines(["ceo: weekly review"], {"ceo"}, ["launch-v1"])
    files = routine_task_files(specs)
    task = files["tasks/ceo-weekly-review/TASK.md"]
    assert "recurring: true" in task
    assert "assignee: ceo" in task
    assert "project: launch-v1" in task
    assert "schema: agentcompanies/v1" in task


def test_routines_block_and_recurring_task_emitted_in_full_bundle() -> None:
    files = render_files(CompanyConfig(**_full_config_kwargs()))
    y = files[".paperclip.yaml"]
    assert "routines:" in y
    assert "ceo-weekly-review:" in y
    assert 'cronExpression: "0 9 * * 1"' in y
    assert "tasks/ceo-weekly-review/TASK.md" in files


def test_single_agent_bundle_has_no_routines() -> None:
    from test_templates import _config

    files = render_files(_config())  # single-agent: no operations → no routines
    assert "routines:" not in files[".paperclip.yaml"]
    assert not any(p.startswith("tasks/") for p in files)
