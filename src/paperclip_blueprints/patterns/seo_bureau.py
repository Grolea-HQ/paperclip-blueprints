"""seo-bureau — derived from the seo-bureau reference (SEO-led service business)."""

from __future__ import annotations

from .base import OrgSeed

SEED = OrgSeed(
    slug="seo-bureau",
    suggested_roles=[
        ("Founder / CEO", None),
        ("Head of SEO", "Founder / CEO"),
        ("Technical SEO Specialist", "Head of SEO"),
        ("Content Lead", "Head of SEO"),
        ("Link Acquisition Lead", "Head of SEO"),
        ("Account Manager", "Founder / CEO"),
        ("Reporting Engineer", "Founder / CEO"),
    ],
    suggested_skills=[
        "technical-seo-audit",
        "content-brief-builder",
        "link-outreach-playbook",
        "client-reporting-pack",
    ],
    suggested_projects=["Run the first client SEO audit", "Stand up the monthly reporting pack"],
)
