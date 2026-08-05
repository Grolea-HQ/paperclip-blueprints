# ADR-036: Routine scheduling defaults and collision detection

## Status

Accepted

## Date

2026-08-05

## Context

`renderers/routines.py` pinned every routine to 09:00: each entry in the named-cadence table,
the weekday-list branch, and the unrecognized-cadence fallback all emitted `0 9 …`. A brief
stating eight cadences with days but no clock times produced eight routines firing at the same
minute of the same day.

**This was not a binding failure.** The brief format does not collect clock times, so no stated
time was ever ignored. Cadence frequency and named days bound correctly — daily, weekly-Monday,
weekly-Tuesday, monthly and quarterly all came out right. It was a poor default, and nothing
detected its consequences.

Observed on a real 13-agent bundle:

- a daily recap whose entire purpose is to summarise a daily scan, scheduled at the same minute
  as that scan;
- a monthly portfolio assembly scheduled at the same minute and day as the register refresh it
  consumes;
- four routines firing simultaneously on the first of each quarter month — self-inflicted
  contention on a shared subscription.

The first two are correctness bugs, not cosmetics: a consumer that runs no later than its
producer reports stale work every time it runs, and never errors.

A collision check already existed — `render._routine_cadence_smells` — but keyed on
`(cron, assignee)`, with a docstring explicitly rejecting cron alone because "two owners can
share a cadence without a smell". Both of the correctness bugs above involve *different*
assignees, so it stayed silent.

## Decision

### 1. Distribute time-of-day deterministically from the task slug

`slot_for(slug)` derives `(hour, minute)` from `hashlib.blake2b(slug.encode("utf-8"),
digest_size=8)`. `cron_for` now takes the slug and composes the expression from that slot plus
the cadence's day pattern.

**`hashlib`, never the builtin `hash()`.** Builtin string hashing is salted per interpreter
process, so it would emit a different schedule on every run of the same brief. Critically, **no
test in this suite would have caught that**: a single test process shares one salt, so the
implementation would agree with itself throughout the suite and still be non-reproducible in
production. `tests/test_routines.py` therefore asserts determinism through a `subprocess` in a
fresh interpreter — the subprocess is the point of the test, not incidental setup.

**Cadence binding is untouched.** Only the previously-unstated time-of-day is defaulted;
frequency and named days bind exactly as before.

### 2. Slot geometry, and the honesty about what it does not guarantee

144 slots: hours 6–17 inclusive (12) × five-minute steps (12).

**Hour-only spreading would not have worked.** Eight routines distributed independently over 12
hourly slots collide with probability **≈95%** (birthday problem). The feature would have
shipped, looked correct, and still collided on nearly every bundle. Over 144 slots the same
eight collide with probability **≈19%**, and three-way collisions become rare.

**≈19% is not zero, and this ADR does not pretend otherwise.** Hashing is probabilistic; a
spread that implied a guarantee would be dishonest. The guarantee comes from decision 3 — the
collision check reports whatever residue remains. Distribution lowers the incidence; detection
closes the gap. **Neither half is sufficient alone**, which is the argument for building both.

Rejected: full-minute granularity (720 slots, ≈4%) — five-minute boundaries keep schedules
human-legible and the difference is absorbed by detection. Rejected: hash-then-probe for a
guaranteed-free slot — buys a guarantee by making each task's time depend on which other tasks
exist, losing the per-task stability that makes regeneration predictable.

#### The window bounds are policy, not physics

`START_HOUR = 6`, `END_HOUR = 17`, `MINUTE_STEP = 5`.

The rationale for a *working-day* window rather than all 24 hours: output an operator is expected
to supervise should land during a working day, and an agent that wakes overnight into an approval
gate stalls until morning regardless — so the small hours buy separation the company cannot
actually use. Giving up half the slot space is the price, and it is worth paying.

**A known imprecision, recorded rather than left to be rediscovered:** the window is applied in
the routine's timezone, which is UTC, while the rationale above is about *human* working hours.
Those coincide only for a UTC-ish operator. An operator in a distant timezone gets a window that
is technically valid and rationally misaligned. Fixing it properly means timezone selection,
which is out of scope here; anyone adding timezone support should revisit these bounds at the
same time.

What is the decision: that time-of-day is distributed at all, deterministically, from a
cross-process-stable digest of the slug alone. What is its current expression: the specific
bounds and step. Retuning the numbers is fine; doing so without an argument is how scheduling
policy drifts.

### 3. Two collision checks, deliberately keyed differently

`_routine_trigger_collisions` groups by trigger expression alone and reports simultaneous
routines regardless of owner. It sits **beside** `_routine_cadence_smells`, which keeps its
`(day pattern, assignee)` key.

**The existing check's reasoning was right for its question, not wrong.** It asks *"was one
activity split into two tasks?"* — and two different owners sharing a cadence is no evidence of
that, so excluding cross-owner pairs is correct for it. The new check asks *"will these fire at
the same moment and contend?"* — for which the owner is irrelevant, because two agents on one
subscription contend precisely *because* they are different agents.

Two questions, two keys, two checks. Widening the original would have silently destroyed the
detection it was built for. A pair matching both conditions correctly produces both findings.
**Do not "simplify" these back together.**

#### A regression this feature caused and the suite caught

Distributing time-of-day broke `_routine_cadence_smells`: it grouped on the full cron, which now
carries a per-task time, so two tasks on one cadence with one assignee no longer grouped and the
check silently stopped firing. Its key is now the **day pattern**, which is what "same cadence"
always meant. Logged here because it is the same failure family as everything else in this batch
— a change that leaves a check present, passing, and inert.

### 4. The dependency check compares order, not equality

`_routine_dependency_order` fires when task A's objective references task B by slug or name
(word-boundary matched), A and B share a day pattern, and A is scheduled **at or before** B.

The original design keyed on a *shared trigger*. That would have been dead on arrival: decision
1 exists to stop routines sharing triggers, so the recap and its scan would separate, the check
would fall silent, and the defect would be **worse** — the recap landing hours *earlier* than
the scan rather than alongside it. Every test written against the narrow rule would still have
passed. Equality is the special case where the gap is zero.

**Recall is deliberately sacrificed.** The check fires only when one task names another, and only
within a shared day pattern — across differing patterns (a daily consumer of a weekly producer)
there is no well-defined "before" without expanding both schedules. A finding that is right when
it fires beats a comprehensive one that cries wolf.

Rejected: automatically reordering consumers after producers. That infers a dependency graph
from prose and then silently acts on it. Every other soft check here reports and lets the
operator judge; this one should too.

### 5. Everything stays advisory

All findings route through the existing `warn` sink. None fails validation or blocks generation
(constitution Principle II is unaffected — bundle validity is untouched).

## Consequences

### Positive consequences
- Bundles no longer schedule every routine at one minute; contention is a choice, not a default.
- Collisions and ordering problems are surfaced before import rather than discovered in
  production.
- Schedules are reproducible across processes and machines, guarded by a test that a
  single-process suite could not otherwise provide.
- The two-check structure is documented, so the next reader does not merge them.

### Negative consequences
- ≈19% of eight-routine bundles still contain a collision, reported rather than prevented.
- The UTC/working-hours mismatch above is real for non-UTC operators.
- The dependency check misses dependencies not expressed by naming the upstream task — by
  design, but it does mean absence of a finding is not evidence of correct ordering.
- Regenerating a brief after renaming a task changes that task's schedule, since the slug is the
  input. Acceptable: a renamed task is a changed task.

### Neutral consequences
- The cron expression shape remains PROVISIONAL pending live-import confirmation, as before.
  This changes which expression is emitted, not the contract for what one is.

## Alternatives considered

- **Assign slots by position in a sorted slug list.** Rejected: guarantees a perfect spread but
  makes every task's schedule depend on the set of tasks, so adding one routine reshuffles
  unrelated ones.
- **Collect clock times in the brief.** Rejected for this feature: a brief-format change is a
  separate decision, and the default must be sensible regardless.
- **Make collisions a validation error.** Rejected: a legitimately simultaneous pair exists (two
  independent routines that genuinely may run together), and blocking generation over a
  judgement call contradicts every other soft check in this codebase.

## References

- `src/paperclip_blueprints/renderers/routines.py` — `slot_for`, `day_pattern_for`, `cron_for`
- `src/paperclip_blueprints/renderers/render.py` — `_routine_trigger_collisions`,
  `_routine_dependency_order`, `_routine_cadence_smells`
- `specs/015-routine-schedule-collisions/` — spec (FR-008/008a/008b), contracts T1–T23
- ADR-022 (routines emission, PROVISIONAL cron), ADR-024 (routine/skill coherence)
- ADR-027 amendment and ADR-012 amendment (2026-08-05) — the same silent-failure family:
  a heuristic that fails green
