"""agency — client-services / retainer agency (creative, accounts, media, SEO, ops)."""

from __future__ import annotations

from .base import OrgSeed

SEED = OrgSeed(
    slug="agency",
    suggested_roles=[
        ("Founder / CEO", None),
        ("Head of Accounts", "Founder / CEO"),
        ("Account Manager", "Head of Accounts"),
        ("Creative Director", "Founder / CEO"),
        ("Copywriter", "Creative Director"),
        ("Director of Operations", "Founder / CEO"),
        ("Paid Media Lead", "Founder / CEO"),
        ("Finance Controller", "Founder / CEO"),
    ],
    suggested_skills=[
        "discovery-call-playbook",
        "retainer-pitch-authoring",
        "creative-qa-pipeline",
        "client-reporting-pack",
    ],
    suggested_projects=["Onboard the first client", "Build the retainer pitch engine"],
)
