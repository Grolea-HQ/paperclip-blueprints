"""Reasoned goal hierarchy (ADR-025) — model invariants + the reasoning generator.

Covers the north-star → sub-goals tree: exactly one root, resolvable parents, per-agent
owners reasoned from mandates, cross-cutting goals kept company-level, single-agent
degradation, and the deterministic fallback that a flaky/absent LLM never yields an orphan
or a second root.
"""

from __future__ import annotations

from typing import Any

import pytest

from paperclip_blueprints.generators.client import GenerationError, LLMClient
from paperclip_blueprints.generators.goal_hierarchy import generate_goal_hierarchy
from paperclip_blueprints.models.agent import AgentDefinition
from paperclip_blueprints.models.company import CompanyDefinition
from paperclip_blueprints.models.goal import GoalDefinition, GoalHierarchy, GoalLevel
from paperclip_blueprints.models.input import CompanyBrief
from test_models import _agent_kwargs, _brief_kwargs, _company_kwargs

# --- GoalHierarchy model invariants ------------------------------------------


def _goal(slug: str, parent: str | None, owner: str, level: GoalLevel = "agent") -> GoalDefinition:
    return GoalDefinition(
        slug=slug,
        title=slug,
        description=f"{slug} outcome",
        level=level,
        parent=parent,
        owner=owner,
    )


def test_hierarchy_accepts_one_root_with_resolvable_parents() -> None:
    h = GoalHierarchy(
        goals=[
            _goal("north-star", None, "ceo", "company"),
            _goal("rating", "north-star", "qa"),
        ]
    )
    assert h.root.slug == "north-star"


def test_hierarchy_rejects_two_roots() -> None:
    with pytest.raises(ValueError, match="exactly one root"):
        GoalHierarchy(
            goals=[
                _goal("north-star", None, "ceo", "company"),
                _goal("other-root", None, "ceo", "company"),
            ]
        )


def test_hierarchy_rejects_dangling_parent() -> None:
    with pytest.raises(ValueError, match="unknown parent"):
        GoalHierarchy(
            goals=[_goal("north-star", None, "ceo", "company"), _goal("x", "missing", "qa")]
        )


def test_hierarchy_rejects_duplicate_slugs() -> None:
    with pytest.raises(ValueError, match="duplicate goal slug"):
        GoalHierarchy(
            goals=[
                _goal("north-star", None, "ceo", "company"),
                _goal("north-star", "north-star", "qa"),
            ]
        )


# --- generate_goal_hierarchy: multi-agent reasoning --------------------------


def _company(**overrides: Any) -> CompanyDefinition:
    return CompanyDefinition(**{**_company_kwargs(), **overrides})


def _brief() -> CompanyBrief:
    return CompanyBrief(**_brief_kwargs())


def _agents() -> list[AgentDefinition]:
    ceo = AgentDefinition(**_agent_kwargs(slug="ceo", name="CEO", title="CEO", reports_to=None))
    qa = AgentDefinition(
        **_agent_kwargs(
            slug="qa",
            name="QA Lead",
            title="QA Lead",
            reports_to="ceo",
            skills=["release-checklist"],
            mandate="Owns product quality and the store rating.",
        )
    )
    return [ceo, qa]


def _assign_transport(assignments: list[dict[str, str]]):
    import json

    def _t(**_: object) -> str:
        return "```json\n" + json.dumps({"assignments": assignments}) + "\n```"

    return _t


def test_north_star_is_the_root_owned_by_org_root() -> None:
    company = _company(
        goals=["Maintain a 4.6+ rating", "Keep refund rate below 3%"],
        north_star="$30k monthly net revenue within 12 months.",
    )
    h = generate_goal_hierarchy(
        company,
        _brief(),
        _agents(),
        LLMClient(_invoke=_assign_transport([{"owner": "qa", "level": "agent"}] * 2)),
    )
    assert h.root.parent is None
    assert h.root.owner == "ceo"  # org root
    assert company.north_star in h.root.description
    assert h.root.level == "company"


def test_each_goal_is_nested_and_owned_by_the_reasoned_agent() -> None:
    company = _company(goals=["Maintain a 4.6+ rating", "Keep refund rate below 3%"])
    h = generate_goal_hierarchy(
        company,
        _brief(),
        _agents(),
        LLMClient(
            _invoke=_assign_transport(
                [{"owner": "qa", "level": "agent"}, {"owner": "qa", "level": "agent"}]
            )
        ),
    )
    subs = [g for g in h.goals if g.parent is not None]
    assert len(subs) == 2
    for g in subs:
        assert g.parent == h.root.slug
        assert g.owner == "qa"
        assert g.level == "agent"


def test_cross_cutting_goal_stays_company_level_ceo_owned() -> None:
    company = _company(goals=["Maintain a 4.6+ rating", "Uphold the brand across all work"])
    h = generate_goal_hierarchy(
        company,
        _brief(),
        _agents(),
        LLMClient(
            _invoke=_assign_transport(
                [{"owner": "qa", "level": "agent"}, {"owner": "company", "level": "company"}]
            )
        ),
    )
    by_owner = {g.description: (g.owner, g.level) for g in h.goals if g.parent is not None}
    assert by_owner["Uphold the brand across all work"] == ("ceo", "company")


def test_unknown_owner_is_coerced_to_ceo_company_level() -> None:
    company = _company(goals=["Maintain a 4.6+ rating"])
    h = generate_goal_hierarchy(
        company,
        _brief(),
        _agents(),
        LLMClient(_invoke=_assign_transport([{"owner": "ghost", "level": "agent"}])),
    )
    sub = next(g for g in h.goals if g.parent is not None)
    assert sub.owner == "ceo" and sub.level == "company"


# --- single-agent degradation + fallback -------------------------------------


def _solo_agent() -> list[AgentDefinition]:
    return [AgentDefinition(**_agent_kwargs(slug="ceo", name="CEO", title="CEO", reports_to=None))]


def test_single_agent_company_degrades_to_lone_root_no_orphan() -> None:
    calls = {"n": 0}

    def _boom(**_: object) -> str:
        calls["n"] += 1
        raise AssertionError("no LLM call should be made for a single-agent company")

    company = _company(goals=["Maintain a 4.6+ rating", "Keep refund rate below 3%"])
    h = generate_goal_hierarchy(company, _brief(), _solo_agent(), LLMClient(_invoke=_boom))
    assert calls["n"] == 0  # deterministic: no owner reasoning needed
    assert h.root.owner == "ceo"
    for g in h.goals:
        assert g.owner == "ceo"
        if g.parent is not None:
            assert g.parent == h.root.slug  # nested, not orphaned


def test_fallback_when_llm_fails_yields_single_root_all_ceo() -> None:
    def _fail(**_: object) -> str:
        raise GenerationError("model unavailable")

    company = _company(goals=["Maintain a 4.6+ rating", "Keep refund rate below 3%"])
    h = generate_goal_hierarchy(company, _brief(), _agents(), LLMClient(_invoke=_fail))
    assert len([g for g in h.goals if g.parent is None]) == 1  # exactly one root
    assert all(g.owner == "ceo" for g in h.goals)  # every goal owned by the CEO/root
    assert all(g.level == "company" for g in h.goals)


# --- CompanyConfig owner-closure + backward-compat ---------------------------


def test_company_config_accepts_a_valid_goal_hierarchy() -> None:
    from paperclip_blueprints.models.output import CompanyConfig
    from test_models import _full_config_kwargs

    kwargs = _full_config_kwargs()  # agents: ceo, cto
    kwargs["goal_hierarchy"] = GoalHierarchy(
        goals=[
            _goal("north-star", None, "ceo", "company"),
            _goal("arch", "north-star", "cto", "agent"),
        ]
    )
    config = CompanyConfig(**kwargs)
    assert config.goal_hierarchy is not None


def test_company_config_rejects_goal_owner_not_in_org() -> None:
    from paperclip_blueprints.models.output import CompanyConfig
    from test_models import _full_config_kwargs

    kwargs = _full_config_kwargs()
    kwargs["goal_hierarchy"] = GoalHierarchy(
        goals=[
            _goal("north-star", None, "ceo", "company"),
            _goal("arch", "north-star", "ghost", "agent"),  # unknown owner
        ]
    )
    with pytest.raises(ValueError, match="owner"):
        CompanyConfig(**kwargs)


def test_backward_compat_flat_only_bundle_still_validates() -> None:
    from paperclip_blueprints.models.output import CompanyConfig
    from test_models import _full_config_kwargs

    config = CompanyConfig(**_full_config_kwargs())  # no goal_hierarchy at all
    assert config.goal_hierarchy is None  # the flat goals: list remains the carrier


# --- carrier: COMPANY.md frontmatter metadata.paperclip.goalHierarchy --------


def test_company_md_carries_structured_hierarchy_and_keeps_flat_goals() -> None:
    from ruamel.yaml import YAML

    from paperclip_blueprints.renderers.render import render_company_md

    company = _company(goals=["Maintain a 4.6+ rating"], north_star="$30k MRR in 12 months.")
    hierarchy = GoalHierarchy(
        goals=[
            _goal("north-star", None, "ceo", "company"),
            _goal("rating", "north-star", "qa", "agent"),
        ]
    )
    out = render_company_md(company, hierarchy)
    fm = YAML(typ="safe").load(out.split("---\n", 2)[1])
    # flat goals: preserved for backward-compat
    assert fm["goals"] == ["Maintain a 4.6+ rating"]
    # structured hierarchy is additive under metadata.paperclip
    gh = fm["metadata"]["paperclip"]["goalHierarchy"]
    assert [g["slug"] for g in gh] == ["north-star", "rating"]
    rating = next(g for g in gh if g["slug"] == "rating")
    assert rating["owner"] == "qa"
    assert rating["parent"] == "north-star"
    assert rating["level"] == "agent"
    root = next(g for g in gh if g["slug"] == "north-star")
    assert root["parent"] is None


def test_company_md_omits_hierarchy_when_absent() -> None:
    from ruamel.yaml import YAML

    from paperclip_blueprints.renderers.render import render_company_md

    out = render_company_md(_company())  # no hierarchy (e.g. `preview`)
    fm = YAML(typ="safe").load(out.split("---\n", 2)[1])
    assert "goalHierarchy" not in fm["metadata"]["paperclip"]
    assert "goals" in fm  # flat list still present


# --- bundle validator (hard failure) -----------------------------------------


def _full_config_with_hierarchy(goals: list[GoalDefinition]):
    from paperclip_blueprints.models.output import CompanyConfig
    from test_models import _full_config_kwargs

    kwargs = _full_config_kwargs()
    kwargs["goal_hierarchy"] = GoalHierarchy(goals=goals)
    return CompanyConfig(**kwargs)


def test_bundle_validator_clean_on_a_valid_hierarchy() -> None:
    from paperclip_blueprints.renderers.render import render_files
    from paperclip_blueprints.validators.integrity import check_integrity

    config = _full_config_with_hierarchy(
        [_goal("north-star", None, "ceo", "company"), _goal("arch", "north-star", "cto", "agent")]
    )
    files = render_files(config)
    assert not [v for v in check_integrity(config, files) if v.startswith("I14")]


def test_bundle_validator_flags_goal_owner_not_in_org() -> None:
    from paperclip_blueprints.renderers.render import render_files
    from paperclip_blueprints.validators.integrity import check_integrity

    # Bypass the CompanyConfig owner-closure to reach the validator: build a valid config,
    # then mutate a goal owner to an unknown slug on the already-constructed object.
    config = _full_config_with_hierarchy(
        [_goal("north-star", None, "ceo", "company"), _goal("arch", "north-star", "cto", "agent")]
    )
    assert config.goal_hierarchy is not None
    config.goal_hierarchy.goals[1].owner = "ghost"
    files = render_files(config)
    assert any(v.startswith("I14") and "ghost" in v for v in check_integrity(config, files))


# --- ADR-046 Class B: I14's other two sites, unreached by any existing test --------
#
# `GoalHierarchy` itself rejects two roots / a dangling parent at construction (see the model
# invariant tests above), so the validator's own I14 root/parent checks can only be reached by
# mutating an already-constructed hierarchy — exactly as the owner-closure test above does.


def test_bundle_validator_flags_goal_hierarchy_with_two_roots() -> None:
    from paperclip_blueprints.renderers.render import render_files
    from paperclip_blueprints.validators.integrity import check_integrity

    config = _full_config_with_hierarchy(
        [_goal("north-star", None, "ceo", "company"), _goal("arch", "north-star", "cto", "agent")]
    )
    assert config.goal_hierarchy is not None
    config.goal_hierarchy.goals.append(_goal("other-root", None, "cto", "company"))
    files = render_files(config)
    violations = [v for v in check_integrity(config, files) if v.startswith("I14")]
    assert any("exactly one root" in v and "other-root" in v for v in violations)


def test_bundle_validator_flags_goal_with_unknown_parent() -> None:
    from paperclip_blueprints.renderers.render import render_files
    from paperclip_blueprints.validators.integrity import check_integrity

    config = _full_config_with_hierarchy(
        [_goal("north-star", None, "ceo", "company"), _goal("arch", "north-star", "cto", "agent")]
    )
    assert config.goal_hierarchy is not None
    config.goal_hierarchy.goals[1].parent = "ghost-parent"
    files = render_files(config)
    violations = [v for v in check_integrity(config, files) if v.startswith("I14")]
    assert any("unknown parent" in v and "ghost-parent" in v for v in violations)
