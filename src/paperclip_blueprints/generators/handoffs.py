"""Handoff targets are drawn from a closed set known before the call (ADR-043).

The set of agent slugs is fixed by the org plan before any per-agent call is made, so a
handoff target is a choice from a closed set rather than a string to be authored. Every
other agent-slug field in this package already works that way — a project's ``owner`` and a
task's ``assignee`` come from the planner stub. Handoffs were the one place a known-set
value was written as free text, and the one place an invalid slug has ever come from.

**Two mechanisms, and neither is redundant. Do not collapse them.**

:func:`handoff_schema` makes an invalid target *unavailable to the model*, which is the
only thing that prevents the failure rather than detecting it. But it binds only when the
model accepts a constrained-output request, and when it does not,
:func:`~.client.LLMClient.complete_json` drops the schema and retries unconstrained
(ADR-014). That drop is silent by design, so a guarantee resting on the schema alone would
disappear without any signal — on a model change nobody made deliberately — and runs would
go back to failing at validator I8 after every call had been paid for.

:func:`parse_handoffs` is therefore checked on every response regardless of whether the
schema was sent, accepted, or dropped. Removing either is a real loss: without the schema
there is only detection; without the check there is no guarantee whenever the schema does
not bind.

Nothing here repairs a near-miss. See :func:`parse_handoffs`.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from .client import GenerationError

__all__ = ["handoff_schema", "legal_targets", "parse_handoffs"]


def legal_targets(slugs: Iterable[str], *, exclude: str) -> list[str]:
    """Return the agent slugs a given agent may name in a handoff.

    Every agent in the company except the one being generated — deliberately the same
    population validator I8 checks against, so generation and validation cannot disagree
    about what is legal. The narrower "manager, direct reports and peers" set stays in the
    prompt as guidance but is not enforced: enforcing it here would reject a cross-branch
    handoff that passes every check downstream, which is the divergence this design exists
    to remove, pointed the other way (ADR-043).

    Args:
        slugs: every planned agent's slug, in plan order.
        exclude: the slug of the agent being generated.

    Returns:
        The legal targets in plan order, deduplicated. Empty for a single-agent company,
        which is why the fields are then not requested at all.
    """
    seen: dict[str, None] = {}
    for slug in slugs:
        if slug != exclude:
            seen.setdefault(slug, None)
    return list(seen)


def handoff_schema(targets: Sequence[str]) -> dict[str, Any]:
    """Return the structured-output fragment for one handoff field.

    The target is a property carrying an ``enum``; the prose describing what crosses the
    handoff is a separate, unconstrained string. That split is the precondition for any
    schema-level constraint: a joined ``"<slug> — what flows"`` string could only be
    constrained by ``pattern``, which the structured-output dialect does not support and
    :func:`~.client._strict_node` strips.

    Args:
        targets: the legal target set from :func:`legal_targets`. Must be non-empty —
            an empty ``enum`` has no satisfying value, so a caller with no legal target
            omits the field entirely instead.
    """
    return {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "agent": {"type": "string", "enum": list(targets)},
                "flow": {"type": "string"},
            },
            "required": ["agent", "flow"],
            "additionalProperties": False,
        },
    }


def _normalise(raw: str) -> str:
    """Strip formatting that cannot carry identity: whitespace and enclosing backticks.

    Nothing else. Case folding and punctuation substitution are excluded because they
    *can* map one agent onto another — slugs are lowercase-hyphenated, so a rule that
    folded case or collapsed punctuation could silently resolve two distinct planned
    agents onto one target. That is repair wearing normalisation's clothes.

    This matches ``validators.integrity._handoff_head``, so generation and validation
    agree on what a slug looks like, not merely on which slugs exist.
    """
    return raw.strip().strip("`").strip()


def parse_handoffs(
    entries: object,
    *,
    targets: Sequence[str],
    field: str,
    owner: str,
) -> list[str]:
    """Validate handoff entries against the closed set and join them for downstream.

    **A rejected target is never altered to a valid one.** Not by fuzzy matching, not by
    edit distance, not by nearest-match. ``qa-led`` is one character from ``qa-lead`` and
    closing that gap automatically is the single most tempting change to make here — it is
    prohibited (FR-008). A repaired near-miss is worse than the failure it replaces: the
    run succeeds, the operator sees nothing, and the bundle ships an agent handing work to
    whichever role the repair guessed. The current behaviour is right about the fact that
    something is wrong; only its timing was the defect, and that is what this module fixes.

    Args:
        entries: the raw value the model returned for this field.
        targets: the legal target set.
        field: the field name, for the error message.
        owner: the slug of the agent being generated, for the error message.

    Returns:
        Entries in the form downstream already consumes: ``"<slug> — <flow>"``, or
        ``"<slug>"`` when no prose was given. Both yield the slug from
        ``_handoff_head``.

    Raises:
        GenerationError: if any entry is not an object, or names a target outside the
            legal set — including an empty or absent one. The message names the agent,
            the field, the offending target and the legal set, so the re-sample it
            triggers has what it needs to succeed.
    """
    if entries is None:
        return []
    if not isinstance(entries, list):
        raise GenerationError(
            f"agent {owner!r} {field} must be a list of "
            f'{{"agent": ..., "flow": ...}} objects, got {type(entries).__name__}'
        )

    legal = ", ".join(targets) if targets else "(none — this company has one agent)"
    out: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise GenerationError(
                f"agent {owner!r} {field} entry must be an object with an 'agent' and a "
                f"'flow' field, got {type(entry).__name__}. The target must be a field of "
                f"its own, not written into a sentence. Legal targets: {legal}"
            )
        raw = entry.get("agent")
        target = _normalise(raw) if isinstance(raw, str) else ""
        if target not in targets:
            raise GenerationError(
                f"agent {owner!r} {field} names {target or raw!r}, which is not an agent "
                f"in this company. Legal targets: {legal}"
            )
        raw_flow = entry.get("flow")
        flow = raw_flow.strip() if isinstance(raw_flow, str) else ""
        out.append(f"{target} — {flow}" if flow else target)
    return out
