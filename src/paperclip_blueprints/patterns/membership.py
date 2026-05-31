"""membership — derived from the membership-stack reference (subscription / community business)."""

from __future__ import annotations

from .base import OrgSeed

SEED = OrgSeed(
    slug="membership",
    suggested_roles=[
        ("Founder / CEO", None),
        ("Content Director", "Founder / CEO"),
        ("Community Manager", "Founder / CEO"),
        ("Member Success Lead", "Founder / CEO"),
        ("Retention Analyst", "Founder / CEO"),
        ("Billing Specialist", "Founder / CEO"),
        ("CMO", "Founder / CEO"),
        ("Paid Acquisition Lead", "CMO"),
    ],
    suggested_skills=[
        "churn-save-email-flow",
        "annual-vs-monthly-pricing-strategy",
        "member-onboarding-tour",
        "community-engagement-playbook",
    ],
    suggested_projects=["Launch the annual pricing flip", "Ship the member onboarding tour"],
)
