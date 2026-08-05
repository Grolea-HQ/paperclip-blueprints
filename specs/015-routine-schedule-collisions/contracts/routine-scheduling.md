# Contract: routine scheduling slots and collision findings

Postconditions the test suite asserts directly. IDs are cited from `tests/test_routines.py`.

## `slot_for(slug) -> (hour, minute)`

Derives a task's time-of-day from its slug alone.

### Inputs / preconditions

- `slug` is a non-empty task slug (lowercase-hyphenated).

### Postconditions

| ID | Guarantee |
|---|---|
| T1 | `START_HOUR ≤ hour ≤ END_HOUR`; `minute ∈ {0, 5, …, 55}`. |
| T2 | Deterministic **across processes**: the same slug yields the same slot in a fresh interpreter. This is the guarantee the builtin `hash()` cannot provide. |
| T3 | Depends on the slug only — not on the other tasks present, their count, or their order. |
| T4 | Distinct slugs are distributed across slots; the function does not concentrate on one value. |

## `cron_for(cadence, slug) -> str`

### Postconditions

| ID | Guarantee |
|---|---|
| T5 | The day-pattern fields (day-of-month, month, day-of-week) are exactly what the cadence states — unchanged from the pre-feature behaviour for every cadence, named or weekday-list. |
| T6 | The minute and hour fields come from `slot_for(slug)`. |
| T7 | Two tasks with the same cadence and different slugs may differ **only** in the minute and hour fields. |
| T8 | An unrecognised cadence still falls back to the weekly day-pattern, with a derived slot. |

## `shared_trigger_collisions(routines) -> list[str]`

### Postconditions

| ID | Guarantee |
|---|---|
| T9 | One finding per group of ≥2 routines sharing an identical trigger expression, naming every member and the expression. |
| T10 | Fires regardless of assignee — a shared trigger across two owners is reported. |
| T11 | Routines with distinct triggers produce no finding. |
| T12 | Findings are ordered stably; repeated runs produce identical output. |
| T13 | Advisory only: emitting a finding never changes the rendered bundle nor causes validation to fail. |
| T14 | Independent of the pre-existing `(cron, assignee)` split-activity check — on a pair matching both, both findings are emitted. |

## `dependency_order_warnings(tasks, routines) -> list[str]`

Fires when a task that appears to consume another's output is not scheduled after it.

### Postconditions

| ID | Guarantee |
|---|---|
| T15 | Fires when task A's objective references task B by slug or name, A and B share a day-pattern, and A's slot is **at or before** B's slot (FR-008). Covers both the equal-slot case and the A-earlier case. |
| T16 | Does not fire when A is scheduled strictly after B on the same day-pattern. |
| T17 | Does not fire when A and B have different day-patterns — cross-pattern ordering is deliberately out of scope (research R5). |
| T18 | Textual matching is word-boundary aware: an identifier occurring as a substring of an unrelated word does not fire. |
| T19 | Advisory only, same as T13. |
| T20 | Distinguishable from a plain shared-trigger finding: the message identifies the producer/consumer ordering problem specifically. |

## Invariants preserved from before this feature

| ID | Guarantee |
|---|---|
| T21 | A bundle with no recurring tasks emits no routines and no findings from this feature. |
| T22 | The routines↔recurring-task closure (validator S15) is unaffected. |
| T23 | The number of routines emitted is unchanged — this feature changes *when* they fire and *what is reported*, never *which* tasks recur. |
