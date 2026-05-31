"""newsletter — derived from the newsletter-press reference (editorial + growth + monetization)."""

from __future__ import annotations

from .base import OrgSeed

SEED = OrgSeed(
    slug="newsletter",
    suggested_roles=[
        ("Founder / CEO", None),
        ("Editor-in-Chief", "Founder / CEO"),
        ("Staff Writer", "Editor-in-Chief"),
        ("Growth Lead", "Founder / CEO"),
        ("Audience / Lifecycle Lead", "Growth Lead"),
        ("Monetization Lead", "Founder / CEO"),
        ("Analytics Lead", "Founder / CEO"),
    ],
    suggested_skills=[
        "editorial-calendar",
        "brand-voice-capture",
        "subscriber-growth-playbook",
        "sponsorship-pipeline",
    ],
    suggested_projects=["Ship the launch issue series", "Stand up the sponsorship pipeline"],
)
