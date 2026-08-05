"""Per-agent budget allocation (ADR-012).

Derives a per-agent monthly budget in integer cents from the company-level
``capital_monthly_eur`` cap, scaled by governance position and weighted by role.
Pure and deterministic — no I/O, no floats in the result, no dependence on
iteration order beyond the (stable) order of the supplied ``role_by_slug``.

The emitted figure maps to Paperclip's per-agent ``budgetMonthlyCents`` field
(verified against the official docs and ``company-portability.ts`` per ADR-007).
There is no company-level budget key in the bundle; the company cap is set via
the Paperclip API, out of bundle scope.
"""

from __future__ import annotations

from dataclasses import dataclass

# Fraction of the cap distributed per governance position; the rest is held as a
# headroom reserve (never 100%). Expressed as integer percent so the cents pool
# is exact integer arithmetic: cap_eur * 100 cents * pct/100 == cap_eur * pct.
GOVERNANCE_PCT = {"tight": 50, "balanced": 70, "loose": 90}

# Relative share by role bucket (from ``render._role_bucket``): an owner/CEO
# reasons over the whole company and tends to run a pricier adapter; generic
# workers are cheapest.
ROLE_WEIGHT = {"owner": 4, "manager": 3, "engineering": 2, "generic": 1}

# Smallest useful per-agent budget (€1), honored when the pool is large enough.
FLOOR_CENTS = 100

# Cadence weighting (ADR-012 amendment). Keyed on an agent's wakes per ACTIVE month — the
# months in which it runs at all — never on its average wakes per calendar month.
#
# ``budgetMonthlyCents`` is a monthly CAP with a hard stop that pauses the agent, not a spend
# forecast. Averaging would give a quarterly agent ~1/3 of a monthly agent's cap and ~1/90th
# of a daily agent's, so in the one month it actually wakes it would hit the cap mid-run and
# pause — silently, in the month that matters. Per active month a quarterly agent needs
# exactly what a monthly agent needs: one wake's worth. So every cadence of monthly-or-rarer
# lands on the same weight, and the scale below never drops beneath a single wake's share.
#
# The top of the scale is deliberately compressed (3, not 30). A cap is a ceiling, so the
# error directions are asymmetric in the same way the run-policy turn cap is: too tight
# pauses the agent mid-run, too loose merely reserves headroom that is never spent. A literal
# 30x spread would starve the low-cadence agents to buy headroom the daily agent may not use.
WAKE_WEIGHT_HIGH = 3  # more than twice weekly (daily, most weekdays)
WAKE_WEIGHT_MEDIUM = 2  # roughly weekly to twice weekly
WAKE_WEIGHT_SINGLE = 1  # one wake in an active month (monthly, quarterly, yearly)

# An agent with no recurring task is handoff-/on-demand-driven: its wake count is unbounded
# and unknowable at generation time. Erring loose, it is weighted as if frequently woken —
# under-capping it would pause a live handoff mid-review, the silent failure again.
UNSCHEDULED_WAKE_WEIGHT = WAKE_WEIGHT_HIGH


def wake_weight(wakes_per_active_month: int | None) -> int:
    """Map an agent's wakes per active month to its cadence weight.

    ``None`` (no recurring task ⇒ on-demand) yields ``UNSCHEDULED_WAKE_WEIGHT``.
    """
    if wakes_per_active_month is None:
        return UNSCHEDULED_WAKE_WEIGHT
    if wakes_per_active_month > 8:
        return WAKE_WEIGHT_HIGH
    if wakes_per_active_month > 1:
        return WAKE_WEIGHT_MEDIUM
    return WAKE_WEIGHT_SINGLE


@dataclass(frozen=True)
class BudgetAllocation:
    """The result of an allocation.

    Attributes:
        cents: Map of agent slug to monthly budget in integer cents. Empty when
            no capital cap was stated.
        warning: A human-readable warning when the scaled pool was too small to
            honor the per-agent floor for every agent; ``None`` otherwise.
    """

    cents: dict[str, int]
    warning: str | None = None


def allocate_budgets(
    role_by_slug: dict[str, str],
    governance_position: str,
    capital_monthly_eur: int | None,
    wakes_by_slug: dict[str, int | None] | None = None,
) -> BudgetAllocation:
    """Derive a per-agent monthly budget (integer cents) from the company cap.

    Args:
        role_by_slug: Agent slug -> role bucket ("owner" | "manager" |
            "engineering" | "generic"), in a stable iteration order.
        governance_position: "tight" | "balanced" | "loose".
        capital_monthly_eur: The company monthly cap in euros, or ``None``.
        wakes_by_slug: Agent slug -> wakes per ACTIVE month (see :func:`wake_weight`), or
            ``None`` to weight by role alone. Omitting it reproduces the pre-amendment
            allocation exactly, so a bundle whose tasks carry no cadence is unchanged.

    Returns:
        A :class:`BudgetAllocation`. ``cents`` is empty when ``capital_monthly_eur``
        is ``None``; otherwise it covers exactly the agents in ``role_by_slug`` and
        sums to ``capital_monthly_eur * GOVERNANCE_PCT[governance_position]`` — always
        within ``capital_monthly_eur * 100`` (the hard cap invariant, ADR-012).
    """
    if capital_monthly_eur is None:
        return BudgetAllocation(cents={}, warning=None)

    slugs = list(role_by_slug)
    n = len(slugs)
    if n == 0:
        return BudgetAllocation(cents={}, warning=None)

    scaled_pool = capital_monthly_eur * GOVERNANCE_PCT[governance_position]
    if wakes_by_slug is None:
        weights = {s: ROLE_WEIGHT[role_by_slug[s]] for s in slugs}
    else:
        weights = {
            s: ROLE_WEIGHT[role_by_slug[s]] * wake_weight(wakes_by_slug.get(s)) for s in slugs
        }
    total_weight = sum(weights.values())
    # Highest-weight agent receives any rounding remainder; ``max`` keeps the
    # first slug on ties, so the tie-break is "earliest in the supplied order".
    top = max(slugs, key=lambda s: weights[s])

    cents: dict[str, int] = {}
    if FLOOR_CENTS * n > scaled_pool:
        # Floor infeasible: the cap is too small for this many agents. The
        # sum-within-cap invariant wins — split purely by weight and warn.
        for s in slugs:
            cents[s] = scaled_pool * weights[s] // total_weight
        cents[top] += scaled_pool - sum(cents.values())
        warning = (
            f"capital cap is too small for {n} agents: the governance-scaled "
            f"monthly pool of {scaled_pool} cents cannot give every agent the "
            f"{FLOOR_CENTS}-cent minimum; budgets are split by weight and some "
            f"agents fall below it — review the cap before enabling heartbeats"
        )
    else:
        # Every agent gets the floor; the surplus above the floors is split by
        # weight, with the rounding remainder going to the highest-weight agent.
        surplus = scaled_pool - FLOOR_CENTS * n
        for s in slugs:
            cents[s] = FLOOR_CENTS + surplus * weights[s] // total_weight
        cents[top] += surplus - sum(c - FLOOR_CENTS for c in cents.values())
        warning = None

    return BudgetAllocation(cents=cents, warning=warning)
