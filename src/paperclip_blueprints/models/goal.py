"""GoalDefinition + GoalHierarchy — the reasoned north-star → sub-goals tree (ADR-025).

A company's goals form a hierarchy, not a flat list: the brief's single north star is
the root, each brief goal is a sub-goal owned by the agent whose mandate makes it
accountable for that outcome, and a goal stays company-level/CEO-owned only where it is
genuinely cross-cutting (no single accountable agent) or the company is too small for role
separation. The field set (``title``/``description``/``level``/``parent``/``owner`` plus a
stable ``slug`` id) matches the deployer's native-Goal API (``title``/``description``/
``level``/``parentId``/``ownerAgentId``): ``slug`` → the Goal id, ``parent`` → ``parentId``
(the parent goal's slug), ``owner`` → ``ownerAgentId`` (the owning agent's slug).

Structural invariants (exactly one root, resolvable/acyclic parents, unique slugs) are
enforced here on ``GoalHierarchy``; owner-resolves-to-a-real-agent needs the org and is
enforced by ``CompanyConfig`` and the bundle validator.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator

GoalLevel = Literal["company", "team", "agent"]

_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class GoalDefinition(BaseModel):
    """One goal in the hierarchy, shaped for the deployer's native-Goal fields."""

    slug: str
    """Stable goal id (maps to the deployer's Goal id; referenced by children's ``parent``)."""
    title: str
    description: str
    level: GoalLevel
    parent: str | None
    """Parent goal's ``slug`` (maps to ``parentId``); ``None`` for the single root goal."""
    owner: str
    """Owning agent's ``slug`` (maps to ``ownerAgentId``)."""

    @field_validator("slug")
    @classmethod
    def _slug_shape(cls, v: str) -> str:
        if not _SLUG_RE.match(v):
            raise ValueError(f"goal slug must be lowercase-hyphenated: {v!r}")
        return v

    @field_validator("title", "description", "owner")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must not be empty")
        return v.strip()


class GoalHierarchy(BaseModel):
    """The full north-star → sub-goals tree for a company.

    Enforces the tree invariants that do not need the org graph: exactly one root
    (``parent is None``), unique slugs, every ``parent`` resolving to a goal in the set,
    and acyclicity. Owner-resolves-to-a-real-agent is enforced where the agents are known
    (``CompanyConfig`` / the bundle validator), not here.
    """

    goals: list[GoalDefinition]

    @model_validator(mode="after")
    def _check_tree(self) -> GoalHierarchy:
        if not self.goals:
            raise ValueError("a goal hierarchy must contain at least the root goal")

        slugs = [g.slug for g in self.goals]
        dupes = {s for s in slugs if slugs.count(s) > 1}
        if dupes:
            raise ValueError(f"duplicate goal slug(s): {sorted(dupes)}")
        slug_set = set(slugs)

        roots = [g.slug for g in self.goals if g.parent is None]
        if len(roots) != 1:
            raise ValueError(f"goal hierarchy must have exactly one root goal; found {roots}")

        for g in self.goals:
            if g.parent is not None and g.parent not in slug_set:
                raise ValueError(f"goal {g.slug!r} has unknown parent {g.parent!r}")

        parent = {g.slug: g.parent for g in self.goals}
        for start in parent:
            seen = {start}
            cur = parent[start]
            while cur is not None:
                if cur in seen:
                    raise ValueError(f"goal hierarchy has a cycle through {cur!r}")
                seen.add(cur)
                cur = parent.get(cur)

        return self

    @property
    def root(self) -> GoalDefinition:
        """The single root goal (the north star)."""
        return next(g for g in self.goals if g.parent is None)
