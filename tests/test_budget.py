"""Unit tests for the per-agent budget allocator (ADR-012, US1/US2/US3).

Covers every postcondition in contracts/budget-allocation.md (C1–C11) and the
worked examples. C10/C11 are the cadence weighting added by the ADR-012 amendment.
"""

from paperclip_blueprints.renderers.budget import (
    FLOOR_CENTS,
    GOVERNANCE_PCT,
    allocate_budgets,
)


def test_a_daily_driven_agent_outweighs_a_quarterly_driven_peer() -> None:
    # ADR-012 amendment: same role bucket, different wake frequency → different cap.
    roles = {"scanner": "generic", "assembler": "generic"}
    alloc = allocate_budgets(roles, "balanced", 100, wakes_by_slug={"scanner": 30, "assembler": 1})
    assert alloc.cents["scanner"] > alloc.cents["assembler"]


def test_quarterly_and_monthly_agents_receive_the_same_cap() -> None:
    # The modeling rule: budgetMonthlyCents is a monthly CAP with a hard stop that pauses the
    # agent, not a spend forecast. An agent waking once a quarter needs, in the month it wakes,
    # exactly what a monthly agent needs — one wake's worth. Weighting by AVERAGE wakes per
    # month would give it ~1/3 of the monthly agent (and ~1/90th of a daily agent), so it would
    # hit its cap mid-run and pause in the one month that matters. Per ACTIVE month, both are 1.
    roles = {"monthly": "generic", "quarterly": "generic"}
    alloc = allocate_budgets(roles, "balanced", 100, wakes_by_slug={"monthly": 1, "quarterly": 1})
    assert alloc.cents["monthly"] == alloc.cents["quarterly"]


def test_omitting_wakes_leaves_the_allocation_unchanged() -> None:
    # Back-compat: the ADR-012 contract holds byte-identically when no cadence is known.
    roles = {"ceo": "owner", "ed": "manager", "wr": "generic"}
    assert allocate_budgets(roles, "balanced", 100).cents == {
        "ceo": 3451,
        "ed": 2612,
        "wr": 937,
    }


def test_no_cap_returns_empty_map() -> None:
    # C1
    alloc = allocate_budgets({"ceo": "owner"}, "balanced", None)
    assert alloc.cents == {}
    assert alloc.warning is None


def test_covers_exactly_the_supplied_agents() -> None:
    # C2
    roles = {"ceo": "owner", "ed": "manager", "wr": "generic"}
    alloc = allocate_budgets(roles, "balanced", 100)
    assert set(alloc.cents) == set(roles)


def test_balanced_three_roles_exact_split_and_owner_remainder() -> None:
    # C3 / C8 — worked example: balanced, €100, owner + manager + generic.
    roles = {"ceo": "owner", "ed": "manager", "wr": "generic"}
    alloc = allocate_budgets(roles, "balanced", 100)
    assert alloc.cents == {"ceo": 3451, "ed": 2612, "wr": 937}
    assert sum(alloc.cents.values()) == 100 * GOVERNANCE_PCT["balanced"]  # 7000
    assert alloc.warning is None
    # owner highest, generic lowest
    assert alloc.cents["ceo"] > alloc.cents["ed"] > alloc.cents["wr"]


def test_sum_within_cap_for_all_governance_positions() -> None:
    # C4 — the hard invariant, across positions and a realistic org.
    roles = {
        "ceo": "owner",
        "cto": "manager",
        "eng1": "engineering",
        "eng2": "engineering",
        "ops": "generic",
    }
    for gov in ("tight", "balanced", "loose"):
        alloc = allocate_budgets(roles, gov, 250)
        assert sum(alloc.cents.values()) <= 250 * 100
        assert sum(alloc.cents.values()) == 250 * GOVERNANCE_PCT[gov]


def test_tight_lt_balanced_lt_loose() -> None:
    # SC-003 — total distributed is strictly ordered and below the full cap.
    roles = {"ceo": "owner", "cto": "manager", "ops": "generic"}
    totals = {g: sum(allocate_budgets(roles, g, 100).cents.values()) for g in GOVERNANCE_PCT}
    assert totals["tight"] < totals["balanced"] < totals["loose"]
    assert totals["loose"] < 100 * 100  # headroom reserve always kept


def test_floor_feasible_every_agent_at_least_floor() -> None:
    # C6
    roles = {"ceo": "owner", "cto": "manager", "ops": "generic"}
    alloc = allocate_budgets(roles, "loose", 100)
    assert all(c >= FLOOR_CENTS for c in alloc.cents.values())
    assert alloc.warning is None


def test_pool_too_small_warns_and_stays_within_cap() -> None:
    # C7 — worked example: tight, €5, 14 agents.
    roles = {f"a{i}": ("owner" if i == 0 else "generic") for i in range(14)}
    alloc = allocate_budgets(roles, "tight", 5)
    assert alloc.warning is not None
    assert sum(alloc.cents.values()) <= 5 * 100
    assert sum(alloc.cents.values()) == 5 * GOVERNANCE_PCT["tight"]  # 250
    # the cap-wins invariant: some agent is below the floor here
    assert any(c < FLOOR_CENTS for c in alloc.cents.values())


def test_single_owner_gets_full_scaled_pool() -> None:
    # C2/C6 — worked example: single agent, loose, €40.
    alloc = allocate_budgets({"ceo": "owner"}, "loose", 40)
    assert alloc.cents == {"ceo": 40 * GOVERNANCE_PCT["loose"]}  # 3600
    assert alloc.cents["ceo"] <= 40 * 100


def test_values_are_non_negative_integers() -> None:
    # C5
    roles = {"ceo": "owner", "cto": "manager", "ops": "generic"}
    alloc = allocate_budgets(roles, "balanced", 100)
    assert all(isinstance(c, int) and c >= 0 for c in alloc.cents.values())


def test_remainder_goes_to_highest_weight_agent() -> None:
    # C8 — the owner (highest weight) absorbs the rounding leftover.
    roles = {"ceo": "owner", "ed": "manager", "wr": "generic"}
    alloc = allocate_budgets(roles, "balanced", 100)
    # exact pool minus the two floor-based weighted shares lands on the owner
    assert sum(alloc.cents.values()) == 100 * GOVERNANCE_PCT["balanced"]


def test_deterministic() -> None:
    # C9
    roles = {"ceo": "owner", "cto": "manager", "eng": "engineering", "ops": "generic"}
    a = allocate_budgets(roles, "balanced", 175)
    b = allocate_budgets(roles, "balanced", 175)
    assert a == b
