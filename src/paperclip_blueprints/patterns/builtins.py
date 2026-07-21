"""Built-in Paperclip skills attached to agents by role (ADR-023).

Every Paperclip instance ships a catalog of built-in skills that a company already
has — they are resolved by slug against the instance catalog, NOT synthesized into
the bundle. So a generated agent must *declare* the role-appropriate built-ins in its
skill list (they surface in the agent's ``skills:`` frontmatter and, once skill
attachment is wired, in ``.paperclip.yaml`` ``desiredSkills``), but the generator must
NOT emit a ``skills/<slug>/SKILL.md`` for them and the closure check must treat their
slugs as resolvable without one.

Role rule (ADR-023):

* **All agents** — ``paperclip`` (control plane: tasks, coordination, governance) and
  ``para-memory-files`` (durable cross-wake memory).
* **CEO + any lead** (an agent with ≥1 direct report) — also
  ``paperclip-converting-plans-to-tasks``.
* **CEO only** (org root / ``role: ceo``) — also ``paperclip-create-agent``.
* **Never auto-attached** — ``paperclip-board`` (the human board member's skill) and
  ``paperclip-dev`` (operator / instance ops). They are still recognized as built-ins
  (so a hand-authored reference resolves without a SKILL.md), just never added here.

This module is the single source of truth for both the catalog and the rule; it is a
leaf (no runtime imports from the package) so ``models`` may import ``BUILTIN_SKILLS``
without a cycle.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # type-only; never executed, so no import cycle with models.org_plan
    from ..models.org_plan import AgentStub

# Built-in slugs attached to every agent.
BUILTIN_ALL: tuple[str, ...] = ("paperclip", "para-memory-files")

# Added for the CEO and any lead (an agent with at least one direct report).
BUILTIN_LEAD: tuple[str, ...] = ("paperclip-converting-plans-to-tasks",)

# Added for the CEO (org root) only.
BUILTIN_CEO: tuple[str, ...] = ("paperclip-create-agent",)

# Recognized built-ins the generator never auto-attaches: the human board member's
# skill and operator/instance-ops skill.
BUILTIN_NEVER: frozenset[str] = frozenset({"paperclip-board", "paperclip-dev"})

# Every built-in slug the generator recognizes as instance-provided. A slug in this set
# resolves against the instance catalog, so it is valid in an agent's skill list WITHOUT
# a bundle ``skills/<slug>/SKILL.md``, and must be excluded from SKILL.md generation.
BUILTIN_SKILLS: frozenset[str] = frozenset(
    {*BUILTIN_ALL, *BUILTIN_LEAD, *BUILTIN_CEO, *BUILTIN_NEVER}
)


# --- Built-in Paperclip AGENTS (reserved name space) -------------------------
#
# SOURCE: ``server/src/services/built-in-agents.ts`` → the ``DEFINITIONS`` array
#         (``const DEFINITIONS = validateBuiltInAgentDefinitions([...])``, line 302)
#         in ``paperclipai/paperclip``.
# READ AT: Paperclip **v2026.720.0** (tag), on 2026-07-21.
#
# WHY THIS IS RESERVED, and why it is a hardcoded platform fact:
#   Built-in agents are ordinary rows in the ``agents`` table carrying immutable
#   ``metadata.paperclipBuiltInAgent``. That table has **no ``slug`` column and no
#   unique constraint on ``(company_id, name)``** — Paperclip derives an agent's key at
#   runtime with ``normalizeAgentUrlKey(name)``, i.e. from the DISPLAY NAME. The two
#   ``bundle`` definitions (``reflection-coach``, ``summarizer``) are auto-provisioned
#   into EVERY company by ``companies.create`` → ``autoProvisionBundledAgents``, and
#   re-reconciled on every server boot. So a generated agent whose name normalizes onto
#   one of these keys lands in an occupied namespace: on a ``new_company`` import the
#   collision check never runs at all (it is gated on ``existing_company``), yielding two
#   same-named agents and NO error; on ``existing_company`` + ``replace`` it instead hits
#   ``built_in_agent_marker_readonly``. Built-ins are also undeletable, so an import can
#   never clean up after itself. The failure is therefore silent or unrecoverable, never
#   a clean rejection — which is why this is enforced at generation time.
#
#   NOTE: the ``enableBuiltInAgents`` experimental setting gates the built-in agent
#   ROUTES only, not ``autoProvisionBundledAgents``. Turning the feature off leaves the
#   rows — and this collision surface — in place. Do not treat it as a mitigation.
#
# MAINTENANCE — this list WILL go stale; Paperclip's registry is designed to grow, and
# its keys are permanent once released ("Do not rename keys after release",
# ``docs/built-in-agents.md``). On a new Paperclip release, re-read the ``DEFINITIONS``
# array above and add any new entry's *derived slug* here, then bump READ AT.
#
# The reserved values below are the ``slugify_agent_name(displayName)`` of each
# definition — the actual collision surface. Registry ``key`` is recorded alongside for
# traceability, and deliberately NOT reserved where it differs from the derived slug
# (``briefs``/``learning``), since reserving those would block legitimate agent names
# like "Learning Designer" for a collision that cannot occur.
#
#   registry key      | displayName        | derived slug (reserved)
#   ------------------|--------------------|------------------------
#   briefs            | "Briefs Agent"     | briefs-agent
#   learning          | "Learning Agent"   | learning-agent
#   reflection-coach  | "Reflection Coach" | reflection-coach   (auto-provisioned)
#   summarizer        | "Summarizer"       | summarizer         (auto-provisioned)
BUILTIN_AGENT_SLUGS: frozenset[str] = frozenset(
    {"briefs-agent", "learning-agent", "reflection-coach", "summarizer"}
)


def builtin_skills_for(*, is_ceo: bool, is_lead: bool) -> list[str]:
    """Return the built-in skill slugs a role should declare, in canonical order.

    Args:
        is_ceo: The agent is the org root / ``role: ceo``.
        is_lead: The agent has at least one direct report.

    Returns:
        The ordered built-in slugs for the role (``BUILTIN_ALL`` for everyone, plus the
        lead/CEO tiers as they apply). Never includes a ``BUILTIN_NEVER`` slug.
    """
    slugs: list[str] = [*BUILTIN_ALL]
    if is_ceo or is_lead:
        slugs += BUILTIN_LEAD
    if is_ceo:
        slugs += BUILTIN_CEO
    return slugs


def attach_builtin_skills(agents: list[AgentStub]) -> list[AgentStub]:
    """Append each agent's role-appropriate built-in skills to its skill list, de-duped.

    Pure over the planned org: the CEO is the single root (``reports_to is None``); a
    lead is any agent that some other agent reports to. Built-ins are appended AFTER the
    agent's existing (custom) skills so ``skills[0]`` stays the primary custom skill, and
    a built-in already present (e.g. listed by the org planner) is not added twice.

    Mutates each stub's ``skills`` in place and returns the same list for chaining.
    """
    lead_slugs = {a.reports_to for a in agents if a.reports_to is not None}
    for agent in agents:
        additions = builtin_skills_for(
            is_ceo=agent.reports_to is None,
            is_lead=agent.slug in lead_slugs,
        )
        existing = set(agent.skills)
        agent.skills = [*agent.skills, *(s for s in additions if s not in existing)]
    return agents
