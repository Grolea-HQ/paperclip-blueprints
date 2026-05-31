"""Bundle validation (v0.1b, US3) — the Constitution-II pre-write gate.

Runs on the assembled ``CompanyConfig`` plus the rendered file map, before any
file is written. Schema-shape (S1–S9) and referential-integrity (I1–I10) checks
each return violations; ``validate_bundle`` aggregates them and raises a single
``BundleValidationError`` listing every problem, so a failed bundle never reaches
disk (Constitution II, FR-016/017). Implemented in-stack against the reference
shape — no jsonschema dependency (ADR-009).
"""

from __future__ import annotations

from ..models.output import CompanyConfig
from .integrity import check_integrity
from .schema_shape import check_schema_shape

__all__ = ["BundleValidationError", "validate_bundle"]


class BundleValidationError(Exception):
    """Raised when an assembled bundle fails validation. Carries all violations."""

    def __init__(self, violations: list[str]) -> None:
        self.violations = violations
        super().__init__("bundle validation failed:\n" + "\n".join(f"  - {x}" for x in violations))


def validate_bundle(config: CompanyConfig, files: dict[str, str]) -> None:
    """Validate the assembled bundle; raise with every violation, or return cleanly."""
    violations = check_schema_shape(config, files) + check_integrity(config, files)
    if violations:
        raise BundleValidationError(violations)
