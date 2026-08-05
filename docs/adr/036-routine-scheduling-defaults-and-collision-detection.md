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

## The pattern across this batch: fixes that would have shipped green

Three separate changes in this review batch would each have passed the full suite while being
wrong. They are worth naming together, because the common shape is not a coding mistake — it is
a class of test that cannot see the defect.

1. **The noun/verb gap** (ADR-027 amendment). Narrowing the poller signal from mandate prose to
   the title was correct, but `_POLLER_RE` held only verb forms (`poll`, `polling`) and no agent
   nouns (`poller`, `watcher`). Titles use nouns. The narrowed heuristic would have matched
   almost nothing — the check would have been present, passing, and silently never firing.
   *Caught by reasoning, before the change landed.*

2. **The FR-008 self-cancellation** (this ADR, decision 4). The dependency check keyed on a
   shared trigger, while the time-of-day spread in the same feature exists to eliminate shared
   triggers. Shipping both would have made the check dead on arrival, and left the underlying
   defect worse than before. *Caught by reasoning, during planning.*

3. **The cadence smell going inert** (this ADR, decision 3). `_routine_cadence_smells` grouped on
   the full cron; once the cron carried a per-task time, two tasks on one cadence stopped
   grouping and the check stopped firing. *Caught by an existing test* — the only one of the
   three that any automated check would have found.

Two of three were caught by thinking about it. That is not a repeatable safeguard.

**The implication for how checks are tested here.** A test asserting that a check *passes on
clean input* is nearly worthless on its own: a check that never fires passes every clean-input
test ever written. Every advisory check in this codebase should have at least one test asserting
it **still fires on input that should trip it** — a positive-detection test, kept alongside the
negative one. `_routine_cadence_smells` survived case 3 precisely because
`test_same_cadence_same_assignee_routines_warn` asserted a firing, not an absence.

This applies to `_routine_trigger_collisions`, `_routine_dependency_order`,
`_routine_skill_incoherence`, `peer_turn_asymmetry`, and any check added later. When a check's
inputs change shape — as they did here — the positive test is what tells you the check followed.

### Audit result, 2026-08-05: all advisory paths bite

Every advisory path reaching `render_files`' `warn` sink was audited by **mutation**, not by
reading tests: each check was replaced with a function returning nothing, and the suite was run
to see whether anything failed. Reading a test and judging it "looks like it asserts a firing"
is the same class of reasoning that missed two of the three defects above.

| Check | Suppressed → first failing test |
|---|---|
| `_routine_trigger_collisions` | `test_collision_findings_are_stably_ordered_and_never_block_validation` |
| `_routine_dependency_order` | `test_consumer_scheduled_before_its_named_producer_warns` |
| `_routine_skill_incoherence` | `test_warning_is_surfaced_through_render_files_warn_sink` |
| `_routine_cadence_smells` | `test_both_checks_fire_on_a_pair_matching_both_conditions` |
| `peer_turn_asymmetry` | `test_peers_under_one_manager_with_different_turn_caps_are_warned` |
| budget pool-too-small warning | `test_pool_too_small_warns_via_sink` |
| unmatched run-policy / adapter reference | `test_render_emits_overrides_and_warns_unmatched` |

No inert check found. Worth noting *how* the audit nearly went wrong: an initial grep for each
check's source message strings found no test for two of the seven, because those tests assert on
a different fragment of the message than the one in the source. Grepping for coverage produces
false alarms and, more dangerously, false comfort. **Mutation is the method — suppress the check
and see if the suite objects.** It is cheap enough to repeat whenever a check's inputs change
shape.

Scope note: this covers *advisory* checks. Hard validators (`validators/integrity.py`,
`validators/schema_shape.py`) fail the build when they fire and so cannot silently go inert in
the same way, but the same mutation technique applies if one is ever suspected.

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
