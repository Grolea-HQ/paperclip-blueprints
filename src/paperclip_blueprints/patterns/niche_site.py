"""niche-site — derived from the niche-site-empire reference (content + SEO + monetization)."""

from __future__ import annotations

from .base import OrgSeed

SEED = OrgSeed(
    slug="niche-site",
    suggested_roles=[
        ("Founder / CEO", None),
        ("Content Director", "Founder / CEO"),
        ("Content Writer", "Content Director"),
        ("Technical SEO Lead", "Founder / CEO"),
        ("Link Acquisition Lead", "Founder / CEO"),
        ("Monetization Lead", "Founder / CEO"),
        ("Analytics Lead", "Founder / CEO"),
    ],
    suggested_skills=[
        "keyword-research",
        "on-page-seo-checklist",
        "link-outreach-playbook",
        "affiliate-optimization",
    ],
    suggested_projects=["Publish the first content cluster", "Build the initial backlink campaign"],
)
