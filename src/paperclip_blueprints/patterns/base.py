"""OrgSeed — a use-case pattern's suggested org shape (v0.1b, US2 / R-006).

A seed is plain data fed to the org_planner prompt as *suggestions* to customize
against the brief, never a template to copy verbatim (Principle IV). It is rendered
to a short text block that the prompt embeds.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class OrgSeed:
    """A suggested starting org for a use-case pattern."""

    slug: str
    suggested_roles: list[tuple[str, str | None]] = field(default_factory=list)
    """(title, reports-to-title) pairs; reports-to is None for the root owner."""
    suggested_skills: list[str] = field(default_factory=list)
    suggested_projects: list[str] = field(default_factory=list)

    def render(self) -> str:
        """Render the seed as prompt context the org_planner can customize."""
        lines = ["Suggested roles:"]
        for title, reports_to in self.suggested_roles:
            if reports_to is None:
                lines.append(f"- {title} (root / owner)")
            else:
                lines.append(f"- {title} → reports to {reports_to}")
        if self.suggested_skills:
            lines.append("Suggested skills: " + ", ".join(self.suggested_skills))
        if self.suggested_projects:
            lines.append("Suggested starter projects: " + ", ".join(self.suggested_projects))
        return "\n".join(lines)
