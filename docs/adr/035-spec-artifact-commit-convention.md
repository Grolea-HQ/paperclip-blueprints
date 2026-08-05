# ADR-035: Which spec-kit artifacts are committed

## Status

Accepted

## Date

2026-08-05

## Context

`.gitignore` ignores `/specs/` wholesale, but individual spec artifacts have been force-added
case by case. The result is inconsistent: feature 014 force-added its **entire** spec directory
(`spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `quickstart.md`,
`contracts/`, `checklists/`), while features 001–013 have nothing tracked at all. ADRs, which
live in `docs/adr/` and are not ignored, are always committed.

There was no rule — only "whatever the last session did" — so every session that produced a
spec artifact had to re-decide, and the decision was invisible to the next one.

The cost is not merely tidiness. Some spec artifacts define behaviour the test suite
**enforces**, and when those live only in an untracked file they can drift from the tests with
nobody noticing:

- `specs/003-per-agent-budgets/contracts/budget-allocation.md` states postconditions C1–C9;
  `tests/test_budget.py` asserts them and cites the IDs in comments. The contract was untracked
  until this ADR.
- `tests/test_budget.py` also cites `SC-003`, a success-criterion ID that exists only in an
  untracked `spec.md`. A reader of the test suite cannot resolve the identifier the test claims
  conformance to.

This is the same silent-divergence shape as the generation defects that prompted the ADR-012
and ADR-027 amendments: an artifact that looks authoritative, is referenced as authoritative,
and is not actually checked against anything.

Working against committing everything: `/specs/` is ignored deliberately. This is a **public,
pre-release** repo, and per CLAUDE.md internal development tracking — WIP, roadmap, in-progress
decisions — stays local. Plans and task breakdowns are exactly that: they record what was
considered and in what order, they go stale the moment implementation diverges, and a stale
plan in a public repo misinforms.

## Decision

**Commit what is enforced. Keep local what is in progress.**

| Artifact | Committed? | Rationale |
|---|---|---|
| `docs/adr/*.md` | **Yes** (already, not ignored) | The decision of record. |
| `specs/<feature>/spec.md` | **Yes** (force-add) | Carries the `FR-*` / `SC-*` identifiers that contracts and tests cite by name. |
| `specs/<feature>/contracts/*.md` | **Yes** (force-add) | States postconditions the test suite asserts directly. |
| `specs/<feature>/plan.md` | No | Implementation route; stale once the code lands. |
| `specs/<feature>/tasks.md` | No | WIP tracking — explicitly local per CLAUDE.md. |
| `specs/<feature>/research.md` | No | Working notes; may cite private gap IDs (`G-*`). |
| `specs/<feature>/data-model.md` | No | Duplicates the Pydantic models, which are the real source. |
| `specs/<feature>/quickstart.md` | No | Superseded by README/`SETUP.md` once shipped. |
| `specs/<feature>/checklists/*.md` | No | Requirement-quality gates for the authoring session. |

**The test.** Commit a spec artifact when code or a test cites it by identifier, or when it
states an invariant the suite enforces. Otherwise it is working material and stays local.

`/specs/` stays in `.gitignore`; committed artifacts are added with `git add -f`. The ignore
rule is the correct default — the exceptions are deliberate and few.

**Feature 014 is grandfathered.** Its already-committed `plan.md` / `tasks.md` / `research.md` /
`data-model.md` / `quickstart.md` / `checklists/` stay tracked. Removing them would be churn
against no risk; the rule governs new work.

**Before force-adding, confirm the artifact carries nothing internal** — no private gap IDs
(`G-*`), no reference to the operator's production deployment, no competitor/third-party tool
names, per the CLAUDE.md public-artifact rules. A contract stating arithmetic postconditions is
safe; a research note weighing upstream internals may not be.

## Consequences

### Positive consequences
- Contracts the tests enforce are reviewable in the repo, so contract-vs-test drift is visible.
- Identifiers cited in tests (`C7`, `SC-003`) resolve to something a reader can open.
- No per-session re-litigation; the convention is written down and points at its own rationale.

### Negative consequences
- Two-step commit for spec work (`git add -f` for the two committed artifact kinds); easy to
  forget, and a forgotten one is silent. Mitigated by naming it in CLAUDE.md's session flow.
- A committed `spec.md` can itself go stale if a feature's requirements change late without the
  spec being updated. It is now a maintained artifact, not a snapshot.

### Neutral consequences
- The split runs along the "enforced vs in-progress" line rather than the spec-kit command that
  produced the file, so a future spec-kit template change does not invalidate the rule.

## Alternatives considered

- **Commit the whole `specs/` tree (un-ignore it).** Rejected: publishes WIP plans, task
  breakdowns and research notes in a public pre-release repo, against the CLAUDE.md rule that
  internal tracking stays local. Also publishes stale plans, which misinform.
- **Commit nothing under `specs/`; move enforced contracts into `docs/`.** Rejected as more
  disruptive for the same result — it would relocate 014's committed contract and break the
  spec-kit layout the workflow depends on. Force-adding two files per feature is cheaper.
- **Contracts only, not `spec.md`** (the initial instinct). Rejected on evidence: tests cite
  `SC-*` IDs that live in `spec.md`, so contracts alone leave the drift open.
- **Keep deciding case by case.** Rejected: that is the status quo, and it produced one fully
  public spec and thirteen invisible ones.

## References

- `.gitignore` (`/specs/`, `/CLAUDE.md`, `/docs/agents/` — the local-only set)
- ADR-012 amendment (2026-08-05) and ADR-027 amendment (2026-08-05) — the silent-divergence
  failure family this convention guards against
- `specs/003-per-agent-budgets/contracts/budget-allocation.md` — the contract force-added under
  this rule
- CLAUDE.md — "Issue tracker" (internal tracking stays local) and "Commercial boundary"
