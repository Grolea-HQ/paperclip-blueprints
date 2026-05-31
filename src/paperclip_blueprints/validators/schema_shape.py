"""Schema-shape checks (S1–S9) — contracts/bundle-validation.md.

Asserts each file looks like the reference-company shape (schema strings,
frontmatter keys, body headings, anti-drift echo). Returns violation strings; the
caller aggregates. The reference companies are the oracle (ADR-007 / ADR-009).
"""

from __future__ import annotations

from ..models.output import CompanyConfig

# Body-only files carry no `schema:` frontmatter (S9).
_BODY_ONLY_SUFFIXES = ("SOUL.md", "HEARTBEAT.md", "TOOLS.md")
_BODY_ONLY_TOP = ("README.md", "OPERATIONS.md", "PROJECT-INVENTORY.md", "LICENSE.txt")

_OPERATIONS_HEADINGS = (
    "## Phase model",
    "## Idle-state protocol",
    "## Reporting cadence",
    "## Communication conventions",
    "## Approval and merge rules",
    "## Delegation quality checklist",
    "## Anti-drift checks",
    "## Duplicate prevention",
    "## Routine slots",
    "## Critical rules summary",
)


def _norm(s: str) -> str:
    return " ".join(s.lower().split()).rstrip(".")


def check_schema_shape(config: CompanyConfig, files: dict[str, str]) -> list[str]:
    """Return every schema-shape violation (S1–S9)."""
    v: list[str] = []

    # S1: paperclip/v1 runtime config.
    if "schema: paperclip/v1" not in files.get(".paperclip.yaml", ""):
        v.append("S1: .paperclip.yaml is missing 'schema: paperclip/v1'")

    # S2: agentcompanies/v1 on every content file.
    for rel, text in files.items():
        if rel == "COMPANY.md" or rel.endswith(("AGENTS.md", "SKILL.md", "PROJECT.md", "TASK.md")):
            if "schema: agentcompanies/v1" not in text:
                v.append(f"S2: {rel} is missing 'schema: agentcompanies/v1'")

    # S3: representative required frontmatter keys.
    for rel, text in files.items():
        if rel.endswith("AGENTS.md"):
            for key in ("slug:", "reportsTo:", "skills:"):
                if key not in text:
                    v.append(f"S3: {rel} frontmatter missing {key!r}")
        elif rel.endswith("TASK.md"):
            for key in ("project:", "assignee:"):
                if key not in text:
                    v.append(f"S3: {rel} frontmatter missing {key!r}")
        elif rel.endswith("PROJECT.md") and "owner:" not in text:
            v.append(f"S3: {rel} frontmatter missing 'owner:'")

    # S4: representative body headings.
    for rel, text in files.items():
        if rel.endswith("AGENTS.md"):
            for h in ("## Mandate", "## Decision rights", "## Escalation"):
                if h not in text:
                    v.append(f"S4: {rel} is missing section {h!r}")
        elif rel.endswith("SOUL.md") and "## What I believe in" not in text:
            v.append(f"S4: {rel} is missing section '## What I believe in'")

    # S5: COMPANY.md keeps ≥2 we-are-not and ≥2 constraints.
    if len(config.company.we_are_not) < 2:
        v.append("S5: COMPANY.md must keep at least 2 'we are not' entries")
    if len(config.company.constraints) < 2:
        v.append("S5: COMPANY.md must keep at least 2 constraints")

    # S6: every SOUL.md includes an idle-state belief.
    for rel, text in files.items():
        if rel.endswith("SOUL.md") and "idle" not in text.lower():
            v.append(f"S6: {rel} must include an idle-state belief")

    # S7 + S8: full-bundle-only checks.
    if config.operations is not None:
        v += _check_operations(config, files.get("OPERATIONS.md", ""))
        v += _check_inventory(config, files.get("PROJECT-INVENTORY.md", ""))

    # S9: body-only files carry no schema frontmatter.
    for rel, text in files.items():
        if rel.endswith(_BODY_ONLY_SUFFIXES) or rel in _BODY_ONLY_TOP:
            if "schema: agentcompanies/v1" in text or "schema: paperclip/v1" in text:
                v.append(f"S9: body-only file {rel} must not carry a schema frontmatter")

    return v


def _check_operations(config: CompanyConfig, ops: str) -> list[str]:
    v: list[str] = []
    for h in _OPERATIONS_HEADINGS:
        if h not in ops:
            v.append(f"S7: OPERATIONS.md is missing section {h!r}")
    # Anti-drift echo: every constraint and 'we are not' must be reproduced.
    assert config.operations is not None
    haystack = _norm(" ".join(config.operations.anti_drift_checks))
    for item in (*config.company.constraints, *config.company.we_are_not):
        if _norm(item) not in haystack:
            v.append(f"S7: OPERATIONS.md anti-drift checks do not reproduce {item!r}")
    return v


def _check_inventory(config: CompanyConfig, inv: str) -> list[str]:
    v: list[str] = []
    starter_blocks = inv.count("### ")
    if starter_blocks != len(config.projects):
        v.append(
            f"S8: PROJECT-INVENTORY.md has {starter_blocks} starter blocks, "
            f"expected {len(config.projects)}"
        )
    # The completed/in-flight tables must be empty at generation (header + separator
    # only — no data rows starting with '|').
    for section in ("Completed deliverables", "In-flight deliverables"):
        if section in inv:
            body = inv.split(section, 1)[1].split("##", 1)[0]
            rows = [ln for ln in body.splitlines() if ln.strip().startswith("|")]
            if len(rows) > 2:  # header + separator only
                v.append(f"S8: PROJECT-INVENTORY.md '{section}' table must be empty at generation")
    return v
