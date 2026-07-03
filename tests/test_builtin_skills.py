"""Built-in-skills-by-role registry and attachment (ADR-023).

Covers the pure role rule (`builtin_skills_for` / `attach_builtin_skills`), the
`OrgPlan.skill_slugs` exclusion of built-ins, and an end-to-end assertion (mocked
pipeline) that built-ins reach agent skill lists, no `skills/<builtin>/SKILL.md` is
generated, a worker does not get the CEO-only built-in, and the bundle validates.
"""

from __future__ import annotations

from paperclip_blueprints.generators.client import LLMClient
from paperclip_blueprints.models.org_plan import AgentStub, OrgPlan
from paperclip_blueprints.patterns.builtins import (
    BUILTIN_SKILLS,
    attach_builtin_skills,
    builtin_skills_for,
)
from paperclip_blueprints.renderers.bundle import generate_bundle_full
from paperclip_blueprints.renderers.render import render_files
from paperclip_blueprints.validators import validate_bundle
from test_cli import _dispatch_full
from test_orchestration import _brief

# --- Pure role rule ----------------------------------------------------------


def test_every_agent_gets_paperclip_and_para_memory() -> None:
    for is_ceo in (True, False):
        for is_lead in (True, False):
            got = builtin_skills_for(is_ceo=is_ceo, is_lead=is_lead)
            assert "paperclip" in got
            assert "para-memory-files" in got


def test_lead_gets_converting_plans_to_tasks() -> None:
    assert "paperclip-converting-plans-to-tasks" in builtin_skills_for(is_ceo=False, is_lead=True)


def test_ceo_gets_converting_plans_and_create_agent() -> None:
    got = builtin_skills_for(is_ceo=True, is_lead=False)
    assert "paperclip-converting-plans-to-tasks" in got  # CEO is always a lead
    assert "paperclip-create-agent" in got


def test_worker_gets_neither_lead_nor_ceo_builtins() -> None:
    got = builtin_skills_for(is_ceo=False, is_lead=False)
    assert "paperclip-converting-plans-to-tasks" not in got
    assert "paperclip-create-agent" not in got


def test_board_and_dev_are_never_returned() -> None:
    for is_ceo in (True, False):
        for is_lead in (True, False):
            got = builtin_skills_for(is_ceo=is_ceo, is_lead=is_lead)
            assert "paperclip-board" not in got
            assert "paperclip-dev" not in got


# --- attach over a planned org -----------------------------------------------


def _stub(slug: str, reports_to: str | None, skills: list[str]) -> AgentStub:
    return AgentStub(slug=slug, name=slug.upper(), title=slug, reports_to=reports_to, skills=skills)


def test_attach_assigns_by_role_across_the_org() -> None:
    agents = [
        _stub("ceo", None, ["strategy"]),
        _stub("lead", "ceo", ["planning"]),  # has a report -> lead
        _stub("worker", "lead", ["coding"]),  # no reports -> worker
    ]
    attach_builtin_skills(agents)
    by_slug = {a.slug: a.skills for a in agents}

    # everyone
    for skills in by_slug.values():
        assert "paperclip" in skills
        assert "para-memory-files" in skills
    # lead tier
    assert "paperclip-converting-plans-to-tasks" in by_slug["ceo"]
    assert "paperclip-converting-plans-to-tasks" in by_slug["lead"]
    assert "paperclip-converting-plans-to-tasks" not in by_slug["worker"]
    # CEO only
    assert "paperclip-create-agent" in by_slug["ceo"]
    assert "paperclip-create-agent" not in by_slug["lead"]
    assert "paperclip-create-agent" not in by_slug["worker"]
    # never
    for skills in by_slug.values():
        assert "paperclip-board" not in skills
        assert "paperclip-dev" not in skills


def test_attach_keeps_custom_skill_first_and_dedupes() -> None:
    # The org planner already listed a built-in — it must not be doubled, and the
    # custom skill must stay at index 0 (the single-agent path reads skills[0]).
    agents = [_stub("ceo", None, ["strategy", "paperclip"])]
    attach_builtin_skills(agents)
    skills = agents[0].skills
    assert skills[0] == "strategy"
    assert skills.count("paperclip") == 1


def test_orgplan_skill_slugs_excludes_builtins() -> None:
    plan = OrgPlan(
        agents=[
            _stub("ceo", None, ["strategy", "paperclip"]),
            _stub("worker", "ceo", ["coding", "para-memory-files"]),
        ]
    )
    slugs = plan.skill_slugs
    assert slugs == ["strategy", "coding"]  # built-ins dropped, custom order preserved
    assert not (set(slugs) & BUILTIN_SKILLS)


# --- End-to-end through the mocked full pipeline -----------------------------


def test_full_bundle_attaches_builtins_without_generating_skill_md() -> None:
    config = generate_bundle_full(_brief(), LLMClient(_invoke=_dispatch_full))
    skills_by_slug = {a.slug: a.skills for a in config.agents}

    # ceo is root + lead (engineer reports to it); engineer is a worker.
    ceo = skills_by_slug["ceo"]
    engineer = skills_by_slug["engineer"]
    for who in (ceo, engineer):
        assert "paperclip" in who and "para-memory-files" in who
    assert "paperclip-converting-plans-to-tasks" in ceo
    assert "paperclip-create-agent" in ceo
    assert "paperclip-create-agent" not in engineer  # worker never gets create-agent

    # No SKILL.md is generated for any built-in; only custom skills get a file.
    files = render_files(config)
    for slug in BUILTIN_SKILLS:
        assert f"skills/{slug}/SKILL.md" not in files
    assert {s.slug for s in config.skills} == {"release-checklist"}

    # The closure/validation treats built-ins as valid even without a SKILL.md.
    validate_bundle(config, files)  # must not raise
