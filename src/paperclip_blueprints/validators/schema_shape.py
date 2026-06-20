"""Schema-shape checks (S1–S9) — contracts/bundle-validation.md.

Asserts each file looks like the reference-company shape (schema strings,
frontmatter keys, body headings, anti-drift echo). Returns violation strings; the
caller aggregates. The reference companies are the oracle (ADR-007 / ADR-009).
"""

from __future__ import annotations

import re

from ruamel.yaml import YAML

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
    "## Budget review",
)


def _norm(s: str) -> str:
    return " ".join(s.lower().split()).rstrip(".")


# Common ≥5-letter words that aren't distinctive enough to anchor an anti-drift
# check on their own (they would let a dropped item pass on a coincidental match).
_STOP = {
    "every",
    "their",
    "there",
    "these",
    "those",
    "which",
    "while",
    "where",
    "about",
    "after",
    "before",
    "would",
    "could",
    "should",
    "shall",
    "might",
    "always",
    "never",
    "often",
    "other",
    "others",
    "thing",
    "things",
    "without",
    "within",
    "across",
    "around",
    "being",
    "doing",
    "having",
    "because",
    "between",
    "during",
    "against",
    "through",
    "under",
    "still",
    "confirm",
    "ensure",
    "avoid",
    "company",
    "agent",
    "agents",
    "operational",
}


def _key_terms(item: str) -> list[str]:
    """Distinctive terms (≥5 letters, not stopwords) an anti-drift check should keep.

    A simple, robust signal: a faithful operational check preserves the distinctive
    vocabulary of the constraint/negation it covers (e.g. ``hot-takes``, ``primary``,
    ``sponsorships``), even when it rewords the surrounding sentence. We deliberately
    do NOT try to extract THE lead noun phrase (that needs NLP); we just require that
    at least one distinctive term survives — enough to catch a dropped item without
    dictating the model's phrasing.
    """
    return [w for w in re.findall(r"[a-z0-9][a-z0-9-]{4,}", item.lower()) if w not in _STOP]


def check_schema_shape(config: CompanyConfig, files: dict[str, str]) -> list[str]:
    """Return every schema-shape violation (S1–S9)."""
    v: list[str] = []

    # S1: paperclip/v1 runtime config.
    if "schema: paperclip/v1" not in files.get(".paperclip.yaml", ""):
        v.append("S1: .paperclip.yaml is missing 'schema: paperclip/v1'")

    # S10: any per-agent budgetMonthlyCents must be a non-negative integer (ADR-012,
    # INV-2). Paperclip parses it as an integer count of cents; a float or negative
    # would be rejected at import.
    v += _check_budget_fields(files.get(".paperclip.yaml", ""))

    # S12: per-agent adapter preference is import-safe (ADR-017) — type in the
    # env-free allowlist and NO adapter.config.env (provider routing / base URLs /
    # credentials stay operator-environment).
    v += _check_adapter_fields(files.get(".paperclip.yaml", ""))

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

    # S7 + S8 + S11: full-bundle-only checks.
    if config.operations is not None:
        v += _check_operations(config, files.get("OPERATIONS.md", ""))
        v += _check_inventory(config, files.get("PROJECT-INVENTORY.md", ""))
        v += _check_board_authority(files.get("OPERATIONS.md", ""))

    # S9: body-only files carry no schema frontmatter.
    for rel, text in files.items():
        if rel.endswith(_BODY_ONLY_SUFFIXES) or rel in _BODY_ONLY_TOP:
            if "schema: agentcompanies/v1" in text or "schema: paperclip/v1" in text:
                v.append(f"S9: body-only file {rel} must not carry a schema frontmatter")

    return v


# Board-authority cues OPERATIONS.md must carry (ADR-016): the human Board is the
# sole approver and agents escalate rather than self-approve. Presence check in the
# style of S7's anti-drift coverage — prose correctness is prompt-encoded.
_BOARD_AUTHORITY_CUES = ("sole approver", "ready for Board review", "Board approv")


def _check_board_authority(ops: str) -> list[str]:
    """S11: OPERATIONS.md states the human Board is the sole approver (ADR-016)."""
    if "Board" in ops and any(cue in ops for cue in _BOARD_AUTHORITY_CUES):
        return []
    return [
        "S11: OPERATIONS.md must state the human Board is the sole approver of "
        "board-gated decisions and that agents escalate (ready for Board review) "
        "rather than self-approving"
    ]


def _check_adapter_fields(yaml_text: str) -> list[str]:
    """S12: per-agent adapter is import-safe — allowlisted type, no ``env`` (ADR-017)."""
    if not yaml_text or "adapter" not in yaml_text:
        return []
    from ..config import PORTABLE_ADAPTER_TYPES

    try:
        data = YAML(typ="safe").load(yaml_text)
    except Exception:  # noqa: BLE001 - I9 reports unparseable YAML; don't double-fault
        return []
    v: list[str] = []
    for slug, agent in (data.get("agents") or {}).items():
        if not isinstance(agent, dict) or not isinstance(agent.get("adapter"), dict):
            continue
        adapter = agent["adapter"]
        atype = adapter.get("type")
        if atype not in PORTABLE_ADAPTER_TYPES:
            v.append(
                f"S12: agent {slug!r} adapter.type {atype!r} is not an import-safe "
                f"worker kind {sorted(PORTABLE_ADAPTER_TYPES)}"
            )
        config = adapter.get("config")
        if isinstance(config, dict) and "env" in config:
            v.append(
                f"S12: agent {slug!r} adapter.config.env must not be emitted "
                f"(provider routing/base URLs/credentials stay operator-environment)"
            )
    return v


def _check_budget_fields(yaml_text: str) -> list[str]:
    """S10: every emitted ``budgetMonthlyCents`` is a non-negative integer (INV-2)."""
    if not yaml_text or "budgetMonthlyCents" not in yaml_text:
        return []
    try:
        data = YAML(typ="safe").load(yaml_text)
    except Exception:  # noqa: BLE001 - I9 reports unparseable YAML; don't double-fault
        return []
    v: list[str] = []
    for slug, agent in (data.get("agents") or {}).items():
        if not isinstance(agent, dict) or "budgetMonthlyCents" not in agent:
            continue
        budget = agent["budgetMonthlyCents"]
        # bool is an int subclass; reject it explicitly so `true` can't slip through.
        if isinstance(budget, bool) or not isinstance(budget, int) or budget < 0:
            v.append(
                f"S10: agent {slug!r} budgetMonthlyCents must be a non-negative "
                f"integer, got {budget!r}"
            )
    return v


def _check_operations(config: CompanyConfig, ops: str) -> list[str]:
    v: list[str] = []
    for h in _OPERATIONS_HEADINGS:
        if h not in ops:
            v.append(f"S7: OPERATIONS.md is missing section {h!r}")
    # Anti-drift coverage: every constraint and 'we are not' negation must be covered
    # by an operational check that keeps its distinctive terms (key-phrase presence,
    # not verbatim — the operational check is expected to reword; see ADR-009 / R-003).
    assert config.operations is not None
    haystack = _norm(" ".join(config.operations.anti_drift_checks))
    for item in (*config.company.constraints, *config.company.we_are_not):
        terms = _key_terms(item)
        if terms and not any(t in haystack for t in terms):
            v.append(f"S7: OPERATIONS.md anti-drift checks do not cover {item!r}")
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
