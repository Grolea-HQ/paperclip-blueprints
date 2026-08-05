"""Per-agent run-policy caps (ADR-027).

The deployer previously set run-policy caps as hard-coded defaults
(``adapterConfig.maxTurnsPerRun = 30``; ``runtimeConfig.heartbeat.maxConcurrentRuns`` = 1
for the CEO / 2 for others). This module makes them **bundle-driven**: it reasons a
``RunPolicy`` per agent from role, so a company can tune caps per role instead of accepting
one global default. The values are emitted into ``.paperclip.yaml`` under each agent's
``runPolicy`` block; the deployer maps ``runPolicy.maxTurnsPerRun`` →
``adapterConfig.maxTurnsPerRun`` and ``runPolicy.maxConcurrentRuns`` →
``runtimeConfig.heartbeat.maxConcurrentRuns``.

Pure and deterministic (no LLM). The defaults match the deployer's current hard-coded
defaults, so behavior is unchanged for a role the reasoning does not tighten; the reasoning
only tightens where a role justifies it (a decision-maker/CEO gets tighter concurrency; a
bounded poller gets low turns).
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..paperclip_slug import slugify_project_name
from .adapter import _matched_ref

if TYPE_CHECKING:
    from ..models.agent import AgentDefinition
    from .adapter import _AgentRef

# Deployer-matching defaults: unchanged behavior unless a role tightens them.
DEFAULT_MAX_TURNS_PER_RUN = 30
CEO_MAX_CONCURRENT_RUNS = 1
DEFAULT_MAX_CONCURRENT_RUNS = 2

# A bounded poller does a quick, repeated, bounded check — it does not need the full turn
# budget, so cap it low to stop a runaway loop.
POLLER_MAX_TURNS_PER_RUN = 10

# Whole-word signals that a role is a bounded poller (→ low turns). Word-boundary matched to
# avoid tripping on unrelated substrings. Kept tight so an ordinary role keeps the default.
#
# Matched against the agent's TITLE ONLY, never the mandate prose. A mandate is a paragraph
# describing what an agent does, and any reviewer whose work involves watching a queue or
# sweeping a register will contain one of these words incidentally — which silently tripled
# a reviewer's turn cap downward. A title is the role's identity: "Signal Monitor" IS a
# poller; "Evidence Reviewer" that happens to monitor something is not.
#
# This is the conservative direction on an asymmetric failure. A too-tight cap fails
# SILENTLY — the agent exhausts its turns and returns a thin result rather than an error, so
# nobody learns the cap was wrong. A too-loose cap fails VISIBLY — it costs more and shows up
# in the budget. Where the signal is uncertain, resolve toward the looser cap.
# Because the match is now on the title, the AGENT-NOUN forms carry the signal ("Poller",
# "Watcher", "Sweeper") alongside the verb/gerund forms a title may still use ("Queue
# Monitoring"). The verb forms alone were enough while mandate prose was searched; they are
# not enough for titles.
_POLLER_RE = re.compile(
    r"\b(poll|polls|polling|poller|pollers|"
    r"monitor|monitors|monitoring|"
    r"watch|watches|watching|watcher|watchers|"
    r"sweep|sweeps|sweeping|sweeper|sweepers)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RunPolicy:
    """One agent's run-policy caps, emitted under ``.paperclip.yaml`` ``runPolicy``.

    ``heartbeat_enabled`` is a brief-only field (feature 014 / ADR-034) with no role
    heuristic: it is ``None`` (⇒ nothing emitted) unless a brief override sets it.
    """

    max_turns_per_run: int
    max_concurrent_runs: int
    heartbeat_enabled: bool | None = None


@dataclass(frozen=True)
class RunPolicyOverride:
    """Operator-stated run-policy values for one agent, parsed from a brief line (ADR-034).

    Every field is optional; a ``None`` field means the brief did not state it, so the
    role-derived base value is kept for that field (``heartbeat_enabled`` has no base — it
    stays ``None`` and nothing is emitted).
    """

    max_turns_per_run: int | None = None
    max_concurrent_runs: int | None = None
    heartbeat_enabled: bool | None = None


def derive_run_policy(*, is_root: bool, title: str, mandate: str) -> RunPolicy:
    """Reason an agent's run-policy caps from its role.

    Args:
        is_root: The agent is the org root / CEO (``reports_to is None``).
        title: The agent's title — the sole source of the poller signal (see ``_POLLER_RE``).
        mandate: The agent's mandate prose. Accepted for interface stability and
            deliberately NOT consulted: matching poller words in prose mis-classified
            ordinary reviewers, and the tightening direction fails silently.

    Returns:
        A ``RunPolicy``: the CEO/root gets tighter concurrency (1 vs 2); a role whose *title*
        names it a bounded poller gets low turns (``POLLER_MAX_TURNS_PER_RUN``); otherwise
        the deployer-matching defaults (30 turns) apply.
    """
    _ = mandate  # see Args: intentionally unread
    max_concurrent = CEO_MAX_CONCURRENT_RUNS if is_root else DEFAULT_MAX_CONCURRENT_RUNS
    is_poller = bool(_POLLER_RE.search(title))
    max_turns = POLLER_MAX_TURNS_PER_RUN if is_poller else DEFAULT_MAX_TURNS_PER_RUN
    return RunPolicy(max_turns_per_run=max_turns, max_concurrent_runs=max_concurrent)


def assign_run_policies(
    agents: list[AgentDefinition],
    overrides: dict[str, RunPolicyOverride] | None = None,
) -> dict[str, RunPolicy]:
    """Return each agent's ``RunPolicy``, keyed by slug: the role-derived base (ADR-027)
    with any brief overrides overlaid per field (feature 014 / ADR-034).

    Args:
        agents: the generated agents.
        overrides: slug -> :class:`RunPolicyOverride` from the brief (see
            :func:`parse_run_policy_preferences`). ``None``/empty ⇒ output identical to the
            pure role rule, so a bundle with no run-policy values is byte-identical to today.

    Returns:
        slug -> :class:`RunPolicy`. For an agent with an override, each **set** field replaces
        the role-derived value; an unset field keeps the base. ``heartbeat_enabled`` comes only
        from the override (the base is ``None``).
    """
    ov_map = overrides or {}
    result: dict[str, RunPolicy] = {}
    for a in agents:
        base = derive_run_policy(is_root=a.reports_to is None, title=a.title, mandate=a.mandate)
        ov = ov_map.get(a.slug)
        if ov is None:
            result[a.slug] = base
        else:
            result[a.slug] = RunPolicy(
                max_turns_per_run=(
                    ov.max_turns_per_run
                    if ov.max_turns_per_run is not None
                    else base.max_turns_per_run
                ),
                max_concurrent_runs=(
                    ov.max_concurrent_runs
                    if ov.max_concurrent_runs is not None
                    else base.max_concurrent_runs
                ),
                heartbeat_enabled=ov.heartbeat_enabled,
            )
    return result


def peer_turn_asymmetry(
    agents: Sequence[AgentDefinition],
    policies: dict[str, RunPolicy],
    overrides: dict[str, RunPolicyOverride] | None = None,
) -> list[str]:
    """Report sibling agents that share a manager but received different turn caps.

    Advisory only — surfaced via the ``warn`` sink, NEVER a validation error and NEVER an
    override. Normalizing the caps would be the wrong fix: the majority value wins under
    normalization, so a group where most peers tripped the poller heuristic would drag a
    correct 30 down to 10 — precisely the silent-failure direction (see ``_POLLER_RE``).
    The operator judges; asymmetry between peers doing the same job on different axes is
    usually a misfire, but occasionally deliberate.

    An agent whose turn cap the brief stated explicitly (ADR-034) is excluded: that is an
    authority statement, not an accidental divergence, and warning on it would be noise.

    Args:
        agents: the generated agents (only non-root agents can have peers).
        policies: slug -> :class:`RunPolicy`, as returned by :func:`assign_run_policies`.
        overrides: the brief's per-slug overrides, to suppress operator-stated caps.

    Returns:
        One warning per manager whose remaining (non-overridden) reports disagree on
        ``max_turns_per_run``, in stable agent order.
    """
    stated = {slug for slug, ov in (overrides or {}).items() if ov.max_turns_per_run is not None}
    groups: dict[str, list[str]] = {}
    for a in agents:
        if a.reports_to is None or a.slug in stated:
            continue
        groups.setdefault(a.reports_to, []).append(a.slug)

    warnings: list[str] = []
    for manager, slugs in groups.items():
        by_cap: dict[int, list[str]] = {}
        for s in slugs:
            by_cap.setdefault(policies[s].max_turns_per_run, []).append(s)
        if len(by_cap) < 2:
            continue
        detail = "; ".join(
            f"{cap} turns: {', '.join(members)}" for cap, members in sorted(by_cap.items())
        )
        warnings.append(
            f"agents reporting to {manager!r} received different turn caps ({detail}) — peers at "
            "one level usually warrant the same cap; check the tighter ones, since exhausting a "
            "turn cap returns a thin result rather than an error and so fails silently"
        )
    return warnings


# --- brief-driven override layer (feature 014 / ADR-034) ---------------------
#
# A pure carrier: it transports operator-stated values and infers nothing. Clause keywords
# (with aliases), matched case-insensitively; turns/concurrency take a positive integer;
# heartbeat takes an on/off token.
_TURNS_RE = re.compile(r"^(?:max[\s-]*turns|turns)\s+(.+)$")
_CONCURRENT_RE = re.compile(r"^(?:max[\s-]*concurrent|concurrency|concurrent)\s+(.+)$")
_HEARTBEAT_RE = re.compile(r"^heartbeat\s+(.+)$")
_HEARTBEAT_ON = {"on", "enabled", "true"}
_HEARTBEAT_OFF = {"off", "disabled", "false"}


def _positive_int(raw: str, ref: str, label: str) -> int:
    s = raw.strip()
    if not re.fullmatch(r"\d+", s):
        raise ValueError(
            f"run-policy override for {ref!r} has a non-integer {label} value {raw.strip()!r}"
        )
    val = int(s)
    if val < 1:
        raise ValueError(
            f"run-policy override for {ref!r} {label} must be a positive integer, got {val}"
        )
    return val


def parse_run_policy_line(line: str) -> tuple[str, RunPolicyOverride]:
    """Parse one brief override line ``<agent reference>: <clause>[, <clause>]...``.

    Returns ``(reference, override)`` where ``reference`` is the raw text before the first
    colon (matched to agents later). Raises :class:`ValueError` on any malformed line — a
    missing colon or reference, no clause, a non-positive/non-integer turns/concurrency value,
    an unknown clause keyword, an unknown heartbeat token, or one field set twice with
    conflicting values in the same line. Does no agent matching (that needs the generated org).
    """
    if ":" not in line:
        raise ValueError(
            f"run-policy override {line!r} must name an agent before ':', e.g. 'ceo: max turns 8'"
        )
    ref, _, rest = line.partition(":")
    ref = ref.strip()
    if not ref:
        raise ValueError(f"run-policy override {line!r} is missing an agent name before ':'")
    clauses = [c.strip() for c in rest.split(",") if c.strip()]
    if not clauses:
        raise ValueError(f"run-policy override for {ref!r} states no value")

    max_turns: int | None = None
    max_concurrent: int | None = None
    heartbeat: bool | None = None
    for clause in clauses:
        cl = clause.lower()
        if m := _TURNS_RE.match(cl):
            val = _positive_int(m.group(1), ref, "max turns")
            if max_turns is not None and max_turns != val:
                raise ValueError(
                    f"run-policy override for {ref!r} sets 'max turns' twice with "
                    "conflicting values"
                )
            max_turns = val
        elif m := _CONCURRENT_RE.match(cl):
            val = _positive_int(m.group(1), ref, "max concurrent")
            if max_concurrent is not None and max_concurrent != val:
                raise ValueError(
                    f"run-policy override for {ref!r} sets 'max concurrent' twice with "
                    "conflicting values"
                )
            max_concurrent = val
        elif m := _HEARTBEAT_RE.match(cl):
            tok = m.group(1).strip()
            if tok in _HEARTBEAT_ON:
                hb = True
            elif tok in _HEARTBEAT_OFF:
                hb = False
            else:
                raise ValueError(
                    f"run-policy override for {ref!r} has an unrecognized heartbeat state "
                    f"{tok!r} (use on/off)"
                )
            if heartbeat is not None and heartbeat != hb:
                raise ValueError(
                    f"run-policy override for {ref!r} sets 'heartbeat' twice with "
                    "conflicting values"
                )
            heartbeat = hb
        else:
            raise ValueError(
                f"run-policy override for {ref!r} has an unrecognized clause {clause!r} "
                "(use 'max turns <n>', 'max concurrent <n>', or 'heartbeat on|off')"
            )
    return ref, RunPolicyOverride(
        max_turns_per_run=max_turns,
        max_concurrent_runs=max_concurrent,
        heartbeat_enabled=heartbeat,
    )


def _merge_override(a: RunPolicyOverride | None, b: RunPolicyOverride) -> RunPolicyOverride:
    """Field-wise merge of two overrides for one agent; ``b`` (later line) wins where set."""
    if a is None:
        return b
    return RunPolicyOverride(
        max_turns_per_run=(
            b.max_turns_per_run if b.max_turns_per_run is not None else a.max_turns_per_run
        ),
        max_concurrent_runs=(
            b.max_concurrent_runs if b.max_concurrent_runs is not None else a.max_concurrent_runs
        ),
        heartbeat_enabled=(
            b.heartbeat_enabled if b.heartbeat_enabled is not None else a.heartbeat_enabled
        ),
    )


def parse_run_policy_preferences(
    preferences: Sequence[str] | None,
    agents: Sequence[_AgentRef],
) -> tuple[dict[str, RunPolicyOverride], list[str]]:
    """Resolve the brief's run-policy override lines to per-slug overrides (ADR-034).

    Each line is parsed (assumed already syntactically valid — the brief validator checks that)
    and its reference matched boundary-safe to agents by slug / title-slug / name-slug, reusing
    the adapter matcher so operators name agents the same way as for model preferences. A
    reference matching several agents fans out; distinct lines matching one agent merge
    field-wise in line order (later wins).

    Returns ``(overrides, unmatched)`` — ``overrides`` maps slug -> :class:`RunPolicyOverride`;
    ``unmatched`` lists lines whose reference matched no agent (the caller warns).
    """
    if not preferences:
        return {}, []
    overrides: dict[str, RunPolicyOverride] = {}
    unmatched: list[str] = []
    for line in preferences:
        ref, ov = parse_run_policy_line(line)
        line_slug = slugify_project_name(ref)
        matched = [a.slug for a in agents if _matched_ref(a, line_slug)]
        if not matched:
            unmatched.append(line)
            continue
        for slug in matched:
            overrides[slug] = _merge_override(overrides.get(slug), ov)
    return overrides, unmatched
