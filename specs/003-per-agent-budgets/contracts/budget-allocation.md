# Contract: Budget allocation + emitted format

## 1. Allocator function contract

```python
# src/paperclip_blueprints/renderers/budget.py

def allocate_budgets(
    role_by_slug: dict[str, str],
    governance_position: str,
    capital_monthly_eur: int | None,
) -> BudgetAllocation:
    """Derive a per-agent monthly budget (integer cents) from a company cap.

    Args:
        role_by_slug: agent slug -> role bucket
            ("owner" | "manager" | "engineering" | "generic"), in a stable
            (deterministic) iteration order.
        governance_position: "tight" | "balanced" | "loose".
        capital_monthly_eur: the company monthly cap in euros, or None.

    Returns:
        BudgetAllocation with `.cents` (slug -> integer cents; empty when
        capital_monthly_eur is None) and `.warning` (set when the scaled pool
        was too small to honor the per-agent floor, else None).
    """
```

### Inputs / preconditions

- `role_by_slug` keys are unique agent slugs; values are one of the four buckets.
- `governance_position ∈ {"tight","balanced","loose"}`.
- `capital_monthly_eur` is a non-negative int or `None` (negatives are rejected
  upstream by input validation and out of scope here).
- `wakes_by_slug`, when supplied, holds non-negative ints or `None` per agent; a slug absent
  from it is treated as `None` (on-demand). Values come from
  `renderers.routines.wakes_per_active_month`, which owns the cadence vocabulary.

### Postconditions / guarantees

| ID | Guarantee |
|---|---|
| C1 | `capital_monthly_eur is None` ⇒ `cents == {}` and `warning is None`. |
| C2 | `capital_monthly_eur is not None` ⇒ `set(cents) == set(role_by_slug)`. |
| C3 | `sum(cents.values()) == capital_monthly_eur * GOVERNANCE_PCT[gov]` (exact). |
| C4 | `sum(cents.values()) ≤ capital_monthly_eur * 100` (the hard cap invariant). |
| C5 | Every value is an `int ≥ 0`. |
| C6 | If `FLOOR_CENTS * N ≤ scaled_pool`: every value `≥ FLOOR_CENTS` and `warning is None`. |
| C7 | If `FLOOR_CENTS * N > scaled_pool`: `warning is not None`; values are a pure weighted split (may be `< FLOOR_CENTS`). |
| C8 | Owner ≥ manager ≥ engineering ≥ generic for agents compared at equal counts **and equal cadence weight** (weight monotonicity); the single highest-weight agent receives any rounding remainder. |
| C9 | Deterministic: identical inputs ⇒ identical output. |
| C10 | `wakes_by_slug is None` ⇒ output is identical to the pre-cadence allocation (role weight alone). |
| C11 | With `wakes_by_slug`: agents differing only in wakes-per-active-month are ordered by `wake_weight`, and every cadence of monthly-or-rarer (`wakes ≤ 1`) maps to the same weight — a quarterly agent is never funded below a monthly one. |

**Cadence weighting (ADR-012 amendment, 2026-08-05).** `allocate_budgets` takes an optional
fourth argument `wakes_by_slug: dict[str, int | None] | None`, mapping each agent to its wakes
per **active** month — the months in which it runs at all, never the calendar average. The
per-agent weight becomes `ROLE_WEIGHT[bucket] × wake_weight(wakes)`. `wake_weight` maps
`>8 → 3`, `>1 → 2`, `≤1 → 1`, and `None` (no recurring task ⇒ on-demand) → `3`, erring loose
because an unbounded wake count under-capped would pause a live handoff mid-run. C1–C7 and C9
are unaffected: the pool, the floor, the integer arithmetic and the determinism are unchanged.

### Worked examples (for tests)

- **Balanced, €100, 1 owner + 1 manager + 1 generic**:
  `scaled_pool = 100 × 70 = 7000` cents. Floor feasible (`300 ≤ 7000`).
  `surplus = 6700`; `W = 4+3+1 = 8`.
  extras = `6700×4//8=3350`, `6700×3//8=2512`, `6700×1//8=837`; sum extras = 6699;
  leftover `1` → owner. Budgets: owner `100+3350+1=3451`, manager `2612`,
  generic `937`. Sum `= 7000 = 100×70`. ✓ (≤ 10000)
- **Tight, €5, 14 agents**: `scaled_pool = 5 × 50 = 250` cents;
  `FLOOR_CENTS × 14 = 1400 > 250` ⇒ floor infeasible ⇒ pure weighted split,
  leftover to highest-weight agent, `warning` set. Sum `= 250 ≤ 500`. ✓
- **No cap**: `capital_monthly_eur = None` ⇒ `cents = {}`, `warning = None`. ✓
- **Single agent, loose, €40**: one owner ⇒ `scaled_pool = 40 × 90 = 3600`;
  `cents = {owner: 3600}`; `≤ 4000`. ✓

## 2. Emitted `.paperclip.yaml` format contract

When `cents` is non-empty, each agent block gains an integer
`budgetMonthlyCents`:

```yaml
schema: paperclip/v1
sidebar:
  agents: [ceo, editor, writer]
  projects: [launch]
agents:
  ceo:
    role: ceo
    budgetMonthlyCents: 3451
  editor:
    budgetMonthlyCents: 2612
  writer:
    budgetMonthlyCents: 937
projects:
  launch:
```

When `cents` is empty (no cap stated), **no** `budgetMonthlyCents` key appears on
any agent — the block is byte-for-byte what it is today.

Rules:
- Integer cents, no quotes, no units suffix, no decimal.
- No company-level budget key anywhere in the file.
- Field omitted (not `0`, not `null`) when there is no value for an agent.

## 3. Validator contract (pre-write, Constitution II)

- **schema_shape**: if any agent block has `budgetMonthlyCents`, it must parse as
  an integer `≥ 0` (INV-2).
- **integrity**: when `brief.capital_monthly_eur is not None`, the sum of all
  emitted `budgetMonthlyCents` must be `≤ capital_monthly_eur × 100` (INV-1).
  A violation raises `BundleValidationError` and the bundle is never written.

## 4. OPERATIONS.md note contract (full bundle only)

- Cap stated: OPERATIONS.md contains a "Budget review" instruction that the
  emitted budgets are conservative starting caps to review before enabling
  heartbeats (FR-009).
- No cap stated: OPERATIONS.md instructs the operator to set per-agent budgets
  before enabling heartbeats (FR-008).
