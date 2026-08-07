"""Does org_planner emit a stated schedule day now that a field exists to hold it?

Feature 018 widened the planner's task stub so a stated weekday, day-of-month and month list
have somewhere to go, and instructed the planner to record them. Widening the field is
checkable by the test suite; **whether the planner then populates it is not** — no unit test can
prove a model follows an instruction. This probe answers that, and its result is the decision
artifact for spec 019 (the brief-side schedule grammar).

**Plan-only, by design.** It runs identity + org planning and stops. Rendering a bundle would
add the whole per-agent fan-out and answer nothing extra, because the question is whether the
*plan object* carries the stated day. Two model calls against a deliberately small brief.

**Run it more than once.** A single sample cannot distinguish *compliant* from *sometimes
compliant*, and those two outcomes point opposite ways on 019.

Not part of the test suite: ``pyproject.toml`` sets ``testpaths = ["tests"]``, so nothing here
is collected by pytest and no run of ``pytest`` can make a billed call through this file.

Usage:
    uv run python scripts/probe_cadence_fidelity.py --runs 5
"""

from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from paperclip_blueprints.generators.client import LLMClient  # noqa: E402
from paperclip_blueprints.generators.identity import generate_identity  # noqa: E402
from paperclip_blueprints.generators.org import generate_org_plan  # noqa: E402
from paperclip_blueprints.models.cadence import DOW, MONTHS  # noqa: E402
from paperclip_blueprints.models.input import parse_brief  # noqa: E402
from paperclip_blueprints.models.org_plan import OrgPlan  # noqa: E402

BRIEF_PATH = pathlib.Path(__file__).resolve().parent / "probe_brief.md"


def _weekday_kept(plan: OrgPlan) -> bool:
    return any(
        t.recurrence is not None
        and t.recurrence.frequency == "weekly"
        and t.recurrence.days_of_week == [DOW["tue"]]
        for t in plan.tasks
    )


def _day_of_month_kept(plan: OrgPlan) -> bool:
    return any(
        t.recurrence is not None
        and t.recurrence.frequency == "monthly"
        and t.recurrence.day_of_month == 5
        for t in plan.tasks
    )


def _quarterly_kept(plan: OrgPlan) -> bool:
    want = sorted(MONTHS[m] for m in ("jan", "apr", "jul", "oct"))
    return any(
        t.recurrence is not None
        and t.recurrence.frequency == "quarterly"
        and t.recurrence.day_of_month == 8
        and sorted(t.recurrence.months or []) == want
        for t in plan.tasks
    )


def _dependency_kept(plan: OrgPlan) -> bool:
    return any(t.depends_on for t in plan.tasks)


CHECKS: list[tuple[str, str, object]] = [
    ("weekday", "weekly, Tuesdays", _weekday_kept),
    ("day-of-month", "monthly, the 5th", _day_of_month_kept),
    ("quarterly", "the 8th of Jan/Apr/Jul/Oct", _quarterly_kept),
    ("dependency", "reconciliation consumes the sweep", _dependency_kept),
]


def run_once(client: LLMClient) -> tuple[dict[str, bool], OrgPlan | None, str | None]:
    """One identity + org-planning pass. Returns (results, plan, error)."""
    brief = parse_brief(BRIEF_PATH.read_text(encoding="utf-8"))
    try:
        company = generate_identity(brief, client)
        plan = generate_org_plan(brief, company, client)
    except Exception as exc:  # noqa: BLE001 - a failed plan is a result, not a crash
        return ({name: False for name, _, _ in CHECKS}, None, f"{type(exc).__name__}: {exc}")
    return ({name: fn(plan) for name, _, fn in CHECKS}, plan, None)  # type: ignore[operator]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=3, help="how many planning passes (default 3)")
    args = parser.parse_args()

    client = LLMClient()
    tallies = {name: 0 for name, _, _ in CHECKS}
    failures: list[str] = []

    for i in range(1, args.runs + 1):
        results, plan, error = run_once(client)
        if error:
            failures.append(f"run {i}: {error}")
        for name, kept in results.items():
            tallies[name] += int(kept)
        marks = "  ".join(f"{name}={'OK' if kept else 'LOST'}" for name, kept in results.items())
        print(f"run {i}/{args.runs}  {marks}")
        if plan is not None:
            for t in plan.tasks:
                if t.recurrence is not None:
                    print(f"    {t.slug}: {t.recurrence.model_dump(exclude_none=True)}")
                if t.depends_on:
                    print(f"    {t.slug}: depends_on={t.depends_on}")

    print("\nsummary")
    for name, stated, _ in CHECKS:
        n = tallies[name]
        print(f"  {name:14} {n}/{args.runs} kept   (brief states: {stated})")
    for f in failures:
        print(f"  ERROR {f}")

    total = sum(tallies.values())
    possible = len(CHECKS) * args.runs
    print(f"\n{total}/{possible} stated values kept across {args.runs} runs.")
    print(
        "\nRead against the interpretation fixed before the run:\n"
        "  all kept, every run  -> 018 recovers the stated values; spec 019's case narrows to\n"
        "                          determinism and to never hand-adjusting.\n"
        "  inconsistent         -> 019's case strengthens; model-mediated capture is not\n"
        "                          dependable, which is what a deterministic channel fixes.\n"
        "  none kept, every run -> the field was not the constraint; rethink the prompt before\n"
        "                          019 is argued at all."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
