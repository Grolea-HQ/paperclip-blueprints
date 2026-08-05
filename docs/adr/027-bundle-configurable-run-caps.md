# ADR-027: Emit bundle-configurable per-agent run-policy caps

## Status

Accepted

## Date

2026-07-05

## Context

The deployer sets run-policy caps as hard-coded defaults: `adapterConfig.maxTurnsPerRun = 30`
for every agent, and `runtimeConfig.heartbeat.maxConcurrentRuns` = 1 for the CEO / 2 for
others. Those are one-size defaults — a company cannot tune them per role. But roles differ:
a decision-maker (CEO) wants tighter concurrency so it does not fan out parallel runs against
itself; a bounded poller does a quick, repeated check and does not need the full turn budget
(and capping its turns low guards against a runaway loop). Generation knows each agent's role
and mandate, so it is the place to reason these caps and emit them into the bundle for the
deployer to consume.

## Decision

Add `renderers/run_policy.py` — a pure, deterministic (no LLM) reasoning step that produces a
`RunPolicy(max_turns_per_run, max_concurrent_runs)` per agent from its role:

- **`maxConcurrentRuns`**: the CEO/org-root gets `1` (tighter); every other agent gets `2`.
- **`maxTurnsPerRun`**: a **bounded poller** — a role whose title/mandate signals a repeated
  bounded check (whole-word `poll`/`monitor`/`watch`/`sweep`, boundary-matched so `watchdog`
  or `sweepstakes` do not trip it) — gets `10`; every other agent gets `30`.

The defaults (`30`; CEO `1` / others `2`) **match the deployer's current hard-coded defaults**,
so behavior is unchanged for any role the reasoning does not tighten; the reasoning only
tightens where a role justifies it. The caps are emitted per agent in `.paperclip.yaml` under a
`runPolicy` block:

```yaml
agents:
  ceo:
    runPolicy:
      maxTurnsPerRun: 30
      maxConcurrentRuns: 1
```

The deployer maps `runPolicy.maxTurnsPerRun → adapterConfig.maxTurnsPerRun` and
`runPolicy.maxConcurrentRuns → runtimeConfig.heartbeat.maxConcurrentRuns`. The block is emitted
for every agent, so the bundle is the single source of truth for the caps (a bundle that
reproduces the defaults yields unchanged behavior; a bundle that tightens a role overrides).

This is the emit side only — the deployer consumer (reading `runPolicy` instead of hard-coding)
lives in the private repo.

## Consequences

### Positive consequences
- Run caps are bundle-driven and per-role: a company tunes them by regenerating, without
  editing the deployer.
- Defaults match today's deployer behavior, so adopting this changes nothing until a bundle
  actually differs.
- Deterministic and auditable — the caps are a role rule, not model output, and are visible in
  `.paperclip.yaml`.

### Negative consequences
- The role→cap mapping (and the poller signal set) is hard-coded; new heuristics need a code
  edit.
- Operator-brief-level caps are not wired yet (see below), so tuning today is via the role
  reasoning, not a per-company brief knob.

### Neutral consequences
- Every agent now carries a `runPolicy` block in `.paperclip.yaml` — explicit and consistent
  for the deployer, at a few extra lines per agent.
- Only two caps are emitted today; the `RunPolicy` shape is open for more.

## Alternatives considered

- **Keep the caps hard-coded in the deployer.** Rejected: that is the status quo F5 removes —
  a company cannot tune per role.
- **Reason the caps with an LLM.** Rejected: caps are a bounded operational knob with a clear
  role rule; a deterministic mapping is auditable and cheap, and there is no judgment an LLM
  adds here.
- **Emit `maxTurnsPerRun` under `adapter.config` and `maxConcurrentRuns` under a separate
  `runtimeConfig` block (mirroring the deployer's exact nesting).** Rejected for now: it splits
  one per-agent concern across two blocks and couples `maxTurnsPerRun` to the presence of an
  `adapter` block. A single `runPolicy` block is cleaner and maps unambiguously; the deployer
  does the two-field split.
- **Add per-company/per-role caps to the operator brief.** Deferred: it touches the input
  template and brief parsing (ADR-003). The role reasoning covers the concrete need now; a brief
  knob can layer on top later (as ADR-017 layered explicit model preferences over role defaults).

## Amendment — 2026-08-05: the poller signal reads the title, never the mandate prose

`derive_run_policy` matched `_POLLER_RE` against `f"{title} {mandate}"`. A mandate is a
paragraph describing what an agent does, so any reviewer whose work involves watching a queue
or sweeping a register contained a poller word *incidentally* — and one such word cut its turn
cap from 30 to 10. Observed on a real bundle: two reviewers with the same manager and the same
job shape on different axes received 30 and 10, and the tighter cap landed on the role with the
wider search surface.

The signal now comes from the **title alone**. A title is the role's identity: a "Signal
Monitor" *is* a poller; an "Evidence Reviewer" that happens to monitor something is not.
`_POLLER_RE` gained the agent-noun forms (`poller`, `watcher`, `sweeper`) that titles actually
use — the verb/gerund forms alone sufficed while prose was searched and do not suffice for
titles. `mandate` stays in the signature for interface stability, documented as deliberately
unread.

**The rationale is the failure asymmetry, and it generalizes.** A too-tight cap fails
*silently*: the agent exhausts its turns and returns a thin result rather than an error, so
nobody learns the cap was wrong. A too-loose cap fails *visibly*: it costs more and shows up in
the budget. Where a heuristic is uncertain, it must resolve toward the looser cap. (ADR-012's
2026-08-05 amendment applies the same principle to the budget cap.)

A new `peer_turn_asymmetry` reports, through the render `warn` sink, sibling agents under one
manager that received different turn caps. It is **advisory only and never normalizes**:
normalization propagates the majority value, so a group where most peers tripped the heuristic
would drag a correct 30 down to 10 — the silent-failure direction. An agent whose cap the brief
stated explicitly (ADR-034) is excluded; that is an authority statement, not a divergence.

## References

- `src/paperclip_blueprints/renderers/run_policy.py` — the reasoning + `RunPolicy`
- `src/paperclip_blueprints/renderers/render.py`, `templates/paperclip_yaml.j2` — the carrier
- ADR-012 (per-agent `budgetMonthlyCents`) and ADR-017 (per-agent adapter/model) — the
  analogous per-agent `.paperclip.yaml` derivations this follows
