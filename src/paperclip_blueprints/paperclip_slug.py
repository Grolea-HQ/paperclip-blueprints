"""Replicate Paperclip's project URL-key derivation (ADR-013).

Paperclip creates a project with ``urlKey = slugify(name)`` and resolves a task's
``project:`` reference against that key, so Blueprints must emit project slugs that
equal the slugified name for tasks to attach on import. This mirrors the
deterministic ASCII path of ``packages/shared/src/project-url-key.ts``
(``normalizeProjectUrlKey``) and the ``uniqueSlug`` collision helper from
``server/src/services/company-portability.ts`` in ``paperclipai/paperclip``.

The non-ASCII branch of Paperclip's ``deriveProjectUrlKey`` appends a runtime UUID
suffix that cannot be predicted offline; it is intentionally NOT replicated. A name
that slugifies to the empty string (all non-ASCII) returns ``""`` so the caller can
fall back and warn.
"""

from __future__ import annotations

import re

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_TRIM_DASH_RE = re.compile(r"^-+|-+$")


def slugify_project_name(name: str) -> str:
    """Return the Paperclip ``urlKey`` for a project name (deterministic ASCII path).

    trim → lowercase → collapse ``[^a-z0-9]+`` runs to ``-`` → strip leading/trailing
    ``-``. Returns ``""`` for an empty or all-non-ASCII name.
    """
    lowered = name.strip().lower()
    dashed = _NON_ALNUM_RE.sub("-", lowered)
    return _TRIM_DASH_RE.sub("", dashed)


def slugify_agent_name(name: str) -> str:
    """Return the Paperclip agent URL key for a display name.

    Mirrors ``normalizeAgentUrlKey`` in ``packages/shared/src/agent-url-key.ts``
    (read at ``v2026.720.0``), which Paperclip uses to derive an agent's key from its
    display ``name`` — the ``agents`` table has no ``slug`` column. The algorithm is
    character-for-character the same as :func:`slugify_project_name`
    (trim → lowercase → collapse ``[^a-z0-9]+`` to ``-`` → strip edge ``-``); it is
    exposed under its own name so agent-side callers cite the agent source, and so the
    two stay independently updatable if Paperclip ever diverges them.

    Returns ``""`` where Paperclip returns ``null`` (empty or all-non-ASCII name).
    """
    return slugify_project_name(name)


def dedupe_slug(base: str, used: set[str]) -> str:
    """Return a unique slug for ``base``, mirroring Paperclip's ``uniqueSlug``.

    ``base`` if free, else the first available ``base-2``, ``base-3``, … The chosen
    slug is added to ``used``.
    """
    if base not in used:
        used.add(base)
        return base
    idx = 2
    while True:
        candidate = f"{base}-{idx}"
        if candidate not in used:
            used.add(candidate)
            return candidate
        idx += 1
