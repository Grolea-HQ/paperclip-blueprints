"""Routine emission (ADR-022, US3) — PROVISIONAL, pending live-import confirmation.

Converts coarse routine slots ("agent-slug: cadence …") into importable Paperclip Routines.
A routine is two coordinated pieces (Paperclip importer source, ADR-007 tier-3):

1. a **recurring task** — ``tasks/<slug>/TASK.md`` with ``recurring: true`` + ``assignee`` +
   ``project`` (the project is MANDATORY; the importer rejects a routine without one);
2. a top-level ``.paperclip.yaml`` ``routines.<task-slug>`` block with a ``schedule`` trigger
   (``cronExpression`` + ``timezone``) and concurrency/catch-up policies (defaults
   ``coalesce_if_active`` / ``skip_missed``).

**PROVISIONAL** — the live import is the acceptance gate for: the ``routines.<slug>`` key
matching the recurring task's slug, cron validity, and assignee/project resolution. Kept in this
one module on purpose so a live correction is a contained, single-file change.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ..paperclip_slug import slugify_project_name
from .frontmatter import dump_frontmatter

# Provisional cron map: a coarse cadence keyword -> a 09:00 cron. The live import confirms cron
# validity; these are sensible defaults, not operator-authored schedules.
_CRON = {
    "daily": "0 9 * * *",
    "weekly": "0 9 * * 1",
    "biweekly": "0 9 * * 1",
    "monthly": "0 9 1 * *",
    "quarterly": "0 9 1 1,4,7,10 *",
    "yearly": "0 9 1 1 *",
    "annual": "0 9 1 1 *",
}
_DEFAULT_CRON = "0 9 * * 1"  # weekly fallback


@dataclass(frozen=True)
class RoutineSpec:
    """One routine: the recurring-task fields plus the ``.paperclip.yaml`` schedule trigger."""

    slug: str
    name: str
    assignee: str
    project: str
    cron: str
    timezone: str = "UTC"
    concurrency_policy: str = "coalesce_if_active"
    catch_up_policy: str = "skip_missed"
    description: str = ""


def _cron_for(cadence: str) -> str:
    low = cadence.lower()
    for key, cron in _CRON.items():
        if key in low:
            return cron
    return _DEFAULT_CRON


def derive_routines(
    routine_slots: Sequence[str], agent_slugs: set[str], project_slugs: Sequence[str]
) -> list[RoutineSpec]:
    """Map ``routine_slots`` ("agent-slug: cadence") to RoutineSpecs (PROVISIONAL).

    Returns ``[]`` when there is no project to anchor a routine (the importer requires one) or no
    recognizable agent. The project anchor is provisional — the first project — and the cron is
    derived from a coarse cadence keyword; both are exactly what a live import confirms.
    """
    if not project_slugs:
        return []
    project = project_slugs[0]
    specs: list[RoutineSpec] = []
    seen: set[str] = set()
    for slot in routine_slots:
        agent, sep, cadence = slot.partition(":")
        agent = agent.strip()
        cadence = (cadence.strip() if sep else "") or slot.strip()
        if agent not in agent_slugs:
            continue
        base = slugify_project_name(f"{agent}-{cadence}") or f"{agent}-routine"
        slug, n = base, 2
        while slug in seen:
            slug, n = f"{base}-{n}", n + 1
        seen.add(slug)
        specs.append(
            RoutineSpec(
                slug=slug,
                name=cadence[:80] or "Routine",
                assignee=agent,
                project=project,
                cron=_cron_for(cadence),
                description=f"Routine: {cadence}",
            )
        )
    return specs


def routine_task_files(routines: Sequence[RoutineSpec]) -> dict[str, str]:
    """The recurring ``TASK.md`` files (the task half of each routine)."""
    files: dict[str, str] = {}
    for r in routines:
        frontmatter = dump_frontmatter(
            {
                "schema": "agentcompanies/v1",
                "slug": r.slug,
                "name": r.name,
                "project": r.project,
                "assignee": r.assignee,
                "recurring": True,
            }
        )
        body = (
            f"# {r.name}\n\n{r.description}\n\n"
            f"This is a recurring (routine) task; its schedule lives in `.paperclip.yaml` "
            f"under `routines.{r.slug}`.\n"
        )
        files[f"tasks/{r.slug}/TASK.md"] = frontmatter + "\n" + body
    return files
