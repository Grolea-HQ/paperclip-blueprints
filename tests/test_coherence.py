"""Routine-task ↔ skill coherence warning (ADR-024).

A recurring task drives work an attached skill governs; at runtime the task is the wake
instruction and wins over the skill, so a task that restates the skill's format/storage
diverges from it. `_routine_skill_incoherence` is an advisory heuristic (surfaced via the
`warn` sink, never a validation error) that flags a recurring task whose text restates
concrete format/storage tokens a co-attached skill also defines.
"""

from __future__ import annotations

from typing import Any

from paperclip_blueprints.models.output import CompanyConfig
from paperclip_blueprints.renderers.render import _routine_skill_incoherence, render_files
from test_models import _full_config_kwargs


def _config(*, task: dict[str, Any], skill_outputs: list[str]) -> CompanyConfig:
    """A full config whose sole skill (`architecture`, attached to `cto`) defines some
    outputs, and whose sole task is assigned to `cto` with the given fields."""
    kwargs = _full_config_kwargs()
    # cto owns the 'architecture' skill; give that skill concrete output/storage language.
    for s in kwargs["skills"]:
        if s.slug == "architecture":
            s.outputs = skill_outputs
    from paperclip_blueprints.models.task import TaskDefinition

    base = {"slug": "review", "name": "Review", "project": "launch-v1", "assignee": "cto"}
    kwargs["tasks"] = [TaskDefinition(**{**base, **task})]
    return CompanyConfig(**kwargs)


def test_warns_when_recurring_task_restates_skill_protocol() -> None:
    config = _config(
        task={
            "objective": "Every week, write the review as a markdown note under the docs/ "
            "directory with the standard headings.",
            "completion_criteria": ["A markdown file exists in the directory."],
            "recurrence": "weekly",
        },
        skill_outputs=["a markdown note stored in the docs/ directory with headings"],
    )
    warnings = _routine_skill_incoherence(config)
    assert len(warnings) == 1
    w = warnings[0]
    assert "review" in w and "architecture" in w  # names the task and the governing skill
    assert "markdown" in w  # names a restated token


def test_no_warning_when_task_defers_to_the_skill() -> None:
    config = _config(
        task={
            "objective": "Every week, perform the architecture review per the `architecture` "
            "skill and produce its prescribed output.",
            "completion_criteria": ["The review is done per the skill."],
            "recurrence": "weekly",
        },
        skill_outputs=["a markdown note stored in the docs/ directory with headings"],
    )
    assert _routine_skill_incoherence(config) == []


def test_no_warning_for_a_non_recurring_task_even_if_it_restates() -> None:
    config = _config(
        task={
            "objective": "Write the review as a markdown note under the docs/ directory.",
            "completion_criteria": ["A markdown file exists."],
            "recurrence": None,
        },
        skill_outputs=["a markdown note stored in the docs/ directory with headings"],
    )
    assert _routine_skill_incoherence(config) == []


def test_warning_is_surfaced_through_render_files_warn_sink() -> None:
    config = _config(
        task={
            "objective": "Every week, write the review as a markdown note under the docs/ "
            "directory with headings.",
            "completion_criteria": ["A markdown file exists in the directory."],
            "recurrence": "weekly",
        },
        skill_outputs=["a markdown note stored in the docs/ directory with headings"],
    )
    captured: list[str] = []
    render_files(config, warn=captured.append)
    assert any("architecture" in m and "review" in m for m in captured)
