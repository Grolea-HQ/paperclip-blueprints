"""content-operations — blog / newsletter / publication operations (community guide)."""

from __future__ import annotations

from .base import OrgSeed

SEED = OrgSeed(
    slug="content-operations",
    suggested_roles=[
        ("Founder / CEO", None),
        ("Content Strategist", "Founder / CEO"),
        ("Writer", "Founder / CEO"),
        ("Editor", "Founder / CEO"),
    ],
    suggested_skills=["editorial-calendar", "brand-voice-capture", "copy-edit-checklist"],
    suggested_projects=["Establish the editorial calendar", "Ship the first content series"],
)
