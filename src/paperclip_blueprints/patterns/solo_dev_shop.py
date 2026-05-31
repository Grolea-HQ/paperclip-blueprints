"""solo-dev-shop — single-developer product shop (Paperclip community guide)."""

from __future__ import annotations

from .base import OrgSeed

SEED = OrgSeed(
    slug="solo-dev-shop",
    suggested_roles=[
        ("Founder / CEO", None),
        ("CTO", "Founder / CEO"),
        ("Engineer", "CTO"),
    ],
    suggested_skills=["product-roadmap", "code-review", "release-management"],
    suggested_projects=["Ship v1 of the product", "Set up the release pipeline"],
)
