"""OperationsDefinition — the OPERATIONS.md operating-manual content.

Section set is fixed by the reference companies (identical across all five). The
anti-drift checks MUST reproduce every COMPANY.md constraint and "we are not"
negation (P-PAT-10, SC-006); that cross-file invariant is checked by the bundle
validator (US3), not here, since this model does not see the identity.
"""

from __future__ import annotations

from pydantic import BaseModel


class OperationsDefinition(BaseModel):
    """OPERATIONS.md content (no frontmatter; body-only file)."""

    phase_model: str
    idle_state_protocol: str
    reporting_cadence: str
    comm_conventions: str
    approval_merge_rules: str
    delegation_checklist: list[str]
    anti_drift_checks: list[str]
    duplicate_prevention: str
    routine_slots: list[str]
    critical_rules: list[str]
