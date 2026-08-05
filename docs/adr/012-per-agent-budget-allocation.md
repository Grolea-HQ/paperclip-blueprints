# ADR-012: Derive per-agent budgets from the company capital cap

## Status

Accepted

## Date

2026-06-13

## Context

Generated `.paperclip.yaml` bundles ship with **no per-agent budgets**, so every
generated company has zero cost guardrails until the operator sets them by hand.
This is a gap, not a deliberate choice: `examples/input-template.md` collects a
monthly capital cap, `MASTER_PROMPTS.md` calls for "per-agent budget caps", and
`docs/deployment-gaps.md` lists governance-scaled per-agent caps as a pattern to
encode. But `templates/paperclip_yaml.j2` emits only schema, sidebar, agents
(slug + role), and projects.

The input model (`models/input.py`) captures `capital_monthly_eur` — a
**company-level** cap — but no per-agent amounts, and no agent model carries a
budget. The tool must therefore *derive* per-agent caps from the single company
number.

**Verified format facts** (per ADR-007 source-of-truth hierarchy):

- Paperclip's export format carries budgets as a per-agent integer field
  `budgetMonthlyCents` on each agent in `.paperclip.yaml`. Confirmed in the
  official `company-portability.ts` export/import service
  (`YAML_KEY_PRIORITY` includes `budgetMonthlyCents`; the exporter writes it only
  when `> 0`) and the official docs (`how-to/set-monthly-budget.md`,
  `guides/power/export-import.md`).
- **There is no company-level budget key in `.paperclip.yaml`.** The company cap
  is set via a separate API call (`PATCH /api/companies/{id}/budgets`), not the
  bundle. Our scope is purely per-agent caps that *sum within*
  `capital_monthly_eur`.
- The exporter **omits** `budgetMonthlyCents` when it is 0/absent. "No cap given
  → emit nothing" matches Paperclip's own behavior.
- Paperclip imports agents with heartbeats **disabled** so the operator can set
  budgets first. Our generated caps are explicitly *conservative starting
  caps to review*, not final values.

ADR-011 removed the local reference companies, so there is no in-repo oracle that
shows a budgets section; the format above comes from tier-1 (official docs) and
tier-3 (source repo) per ADR-007. v0.1 has no adapter information (adapter
assignment is a v0.2 deliverable), so cost-tier weighting cannot key off the
adapter yet.

## Decision

Emit per-agent `budgetMonthlyCents` in `.paperclip.yaml`, derived from
`capital_monthly_eur` by a pure, deterministic allocation:

1. **Pool.** `scaled_pool = floor(capital_monthly_eur × 100 × gov_fraction)` cents,
   where `gov_fraction` scales by governance position (P-PAT-4): `tight = 0.50`,
   `balanced = 0.70`, `loose = 0.90`. Never 100% — the reserve absorbs
   first-month surprises so spend stays inside stated capital.

2. **Weights.** Each agent's weight comes from the existing `_role_bucket()`
   classification (no new data, phase-pure): `owner = 4`, `manager = 3`,
   `engineering = 2`, `generic = 1`. An owner/CEO reasons over the whole company
   and typically runs a pricier adapter; generic workers are cheapest. v0.2's
   adapter assigner can refine this once real adapter tiers exist.

3. **Floor-base + weighted-surplus allocation.** With `N` agents, total weight
   `W`, and a per-agent floor of `100` cents (€1):
   - If `100 × N > scaled_pool` the floor is infeasible: do a pure weighted
     floor-split (`share_i = floor(scaled_pool × w_i / W)`), assign the leftover
     cents to the highest-weight agent, and **warn** that the pool is too small
     for the org size (some agents fall below €1).
   - Otherwise: give every agent the `100`-cent floor, distribute the surplus
     `scaled_pool − 100N` by weight (`extra_i = floor(surplus × w_i / W)`), and
     assign the leftover cents to the highest-weight agent. Every agent gets
     ≥ €1 and the sum equals `scaled_pool` exactly.

4. **Missing cap.** When `capital_monthly_eur` is absent, emit **no**
   `budgetMonthlyCents` keys (matching the exporter) and have OPERATIONS.md
   instruct the operator to set per-agent budgets before enabling heartbeats.

5. **Single-agent path.** `--single-agent` uses the same logic; the lone owner
   receives the full scaled pool. No special-casing.

6. **Hard invariant.** `sum(budgetMonthlyCents) ≤ capital_monthly_eur × 100`
   always holds. When floor and cap conflict, the cap wins.

**Code location.** A new pure function in `renderers/budget.py` builds a
`slug → cents` map from the agent list, governance position, and cap. It is called
from `render_files()` and passed into the `paperclip_yaml.j2` context.
`AgentDefinition` stays free of derived data.

## Consequences

### Positive consequences
- Every generated company ships with cost guardrails by default; no agent is
  left uncapped when a cap is known.
- Allocation is a pure, deterministic, independently unit-testable function.
- Matches the verified Paperclip format exactly, so bundles import cleanly and
  the budgets land on the right agents.
- Governance scaling and the headroom reserve make the defaults conservative, as
  Paperclip's model intends.

### Negative consequences
- Role-bucket weighting is a proxy for adapter cost until v0.2 supplies real
  adapter tiers; an owner on a cheap adapter is over-weighted in the interim.
- A very small cap relative to org size produces sub-€1 caps and a warning rather
  than a clean allocation — an inherent consequence of the cap-wins invariant.

### Neutral consequences
- The chosen numbers (50/70/90, 4/3/2/1, €1 floor) are starting defaults the
  operator is told to review; they are policy, not physics, and can be retuned
  without changing the algorithm.

## Alternatives considered

- **Add adapter cost-tier to v0.1's agent model.** Rejected: adapter assignment
  is a v0.2 deliverable (`adapter_assigner.py`); pulling it forward breaks phase
  discipline for marginal accuracy. Role buckets already exist and approximate it.
- **Flat equal split (cap ÷ N).** Rejected: ignores that an owner/CEO typically
  costs several times a routine worker.
- **Invent a default pool when the cap is absent.** Rejected: fabricates a number
  the operator never stated; omitting (with an OPERATIONS.md note) matches the
  exporter and is honest.
- **Make `capital_monthly_eur` required.** Rejected: breaks existing briefs that
  omit it; the field is optional by ADR-003.
- **Floor wins over cap.** Rejected: violates the `sum ≤ cap` acceptance
  criterion; budgets exceeding stated capital defeat the guardrail's purpose.
- **Field on `AgentDefinition`.** Rejected: couples a derived value into the
  model; a pure renderer-side function is easier to test and keeps the model
  describing authored content only.

## Amendment — 2026-08-05: cadence weighting (role alone was not enough)

Role bucket alone produced **identical** `budgetMonthlyCents` for every agent that fell in the
same bucket. On a real 13-agent bundle, nine non-lead agents all classified `generic` and all
received the same figure — including one driven by a daily routine (~30 wakes a month) and one
driven by a quarterly routine (one wake, four times a year). Workload differing by an order of
magnitude produced no difference in the cap.

`allocate_budgets` now takes an optional `wakes_by_slug`, and the per-agent weight becomes
`ROLE_WEIGHT × wake_weight(...)`. Omitting the argument reproduces the pre-amendment allocation
exactly, so a bundle whose tasks carry no cadence is unchanged; every invariant in Decision
(§sum-within-cap, the `FLOOR_CENTS` floor, integer cents, determinism) is untouched.

Two modeling rules govern the weight, both following from what the field *is* — a monthly
**cap** whose hard stop pauses the agent, not a spend forecast:

1. **Count wakes per ACTIVE month, never the calendar average.** A quarterly agent, in the
   month it wakes, needs exactly what a monthly agent needs: one wake's worth. Averaging would
   give it ~1/3 of a monthly agent's cap and ~1/90th of a daily agent's, so it would hit the
   cap mid-run and pause — silently, in the one month that matters. Monthly, quarterly and
   yearly therefore all weight identically.
2. **Compress the top of the scale (3, not 30).** The error directions are asymmetric in the
   same way as ADR-027's turn cap: too tight pauses the agent mid-run, too loose merely
   reserves headroom that is never spent. A literal 30× spread would starve low-cadence agents
   to buy headroom the daily agent may not use. Where the signal is uncertain, err loose — an
   agent with no recurring task at all is on-demand, its wake count unbounded and unknowable at
   generation time, so it takes the *highest* weight rather than a punitive default.

An agent driven by several routines is funded for its **busiest**: the cap must cover the
heaviest month, not an average across them.

### The thresholds are policy, not physics

Stated explicitly so that retuning them is a decision with a rationale to argue against, rather
than a rediscovery. `wake_weight` maps wakes-per-active-month to weight:

| Wakes per active month | Weight | Cadences that land here | Why the boundary sits there |
|---|---|---|---|
| `> 8` | 3 | daily, most weekdays | Well clear of weekly work; the top of a deliberately compressed scale (see rule 2 above). |
| `> 1` | 2 | weekly, biweekly, a few days a week | Genuinely repeated within the month, but not daily. |
| `≤ 1` | 1 | monthly, quarterly, yearly | Rule 1: one wake in an active month. This band is the load-bearing one — it is what stops a quarterly agent being funded below a monthly one. |
| `None` | 3 | no recurring task (on-demand) | Unbounded, unknowable wake count; err loose (see rule 2). |

The `> 8` boundary is the arbitrary one: it groups "daily" with "most weekdays" and puts
"twice weekly" a tier down. It was chosen to keep the `≤ 1` band cleanly isolated, which is the
rule that carries the correctness weight; the exact placement of the upper boundary is not
load-bearing and a company whose cadences cluster near it can move the constant. What must
**not** change without revisiting this amendment: that monthly-or-rarer cadences share one
weight, that the scale stays compressed rather than proportional to raw wake counts, and that
`None` errs high. Those three are the decision; the numbers are its current expression.

`GOVERNANCE_PCT` is **unchanged** and deliberately so. That a `tight` company distributes 50%
of its stated cap is the specified dial, not conservatism to be corrected; the remainder is the
documented headroom reserve. The cadence question and the reserve question are independent.

The cadence vocabulary stays in `renderers/routines.py` (`wakes_per_active_month`), shared with
`cron_for`. Two parsers of the same operator-written cadence strings would drift, and a silent
divergence between what gets *scheduled* and what gets *budgeted* is precisely the class of
defect this amendment exists to close.

## References

- ADR-002 (output bundle format), ADR-003 (optional input fields),
  ADR-004 (prompt architecture / deterministic rendering),
  ADR-007 (source-of-truth hierarchy), ADR-011 (reference companies removed)
- `docs/deployment-gaps.md` P-PAT-4 (governance-scaled per-agent caps)
- Paperclip official docs: `how-to/set-monthly-budget.md`,
  `guides/power/export-import.md`
- `paperclipai/paperclip` `server/src/services/company-portability.ts`
  (`budgetMonthlyCents` export shape, omit-when-zero)
