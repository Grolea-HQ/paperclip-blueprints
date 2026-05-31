"""open-source-maintenance — OSS project maintenance (community guide)."""

from __future__ import annotations

from .base import OrgSeed

SEED = OrgSeed(
    slug="open-source-maintenance",
    suggested_roles=[
        ("Maintainer / Lead", None),
        ("Triage Engineer", "Maintainer / Lead"),
        ("PR Reviewer", "Maintainer / Lead"),
        ("Docs Steward", "Maintainer / Lead"),
    ],
    suggested_skills=["issue-triage", "pr-review-checklist", "doc-drift-audit"],
    suggested_projects=["Clear the issue triage backlog", "Audit and fix documentation drift"],
)
