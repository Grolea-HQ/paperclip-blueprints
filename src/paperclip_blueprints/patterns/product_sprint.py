"""product-sprint — two-week sprint delegation against a backlog (community guide)."""

from __future__ import annotations

from .base import OrgSeed

SEED = OrgSeed(
    slug="product-sprint",
    suggested_roles=[
        ("Founder / CEO", None),
        ("CTO", "Founder / CEO"),
        ("QA Lead", "CTO"),
    ],
    suggested_skills=["sprint-planning", "code-review", "qa-pipeline"],
    suggested_projects=["Plan and run the first sprint", "Stand up the QA pipeline"],
)
