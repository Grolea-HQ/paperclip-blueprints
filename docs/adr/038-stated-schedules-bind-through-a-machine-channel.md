# ADR-038: Stated schedules bind through a machine channel; the company timezone binds first

## Status

Accepted

## Date

2026-08-06

## Context

A regenerated 13-agent bundle was checked against a brief whose section 7 states its schedule
explicitly, in prose: eight cadences, each naming an agent, a day and a local time in
Europe/Helsinki, with the stagger justified in the same paragraph — three routines consume
another's output and must follow it, and every agent shares one adapter subscription.

Almost none of that reached the bundle. The precedent scan landed on Monday against a stated
Tuesday. Both quarterlies landed on the 1st against a stated 5th and 8th. The timezone was UTC.
The daily recap — a morning liveness heartbeat — landed at 14:20 UTC, 17:20 in Helsinki. And the
ordering inverted: `portfolio-assembly` at `15 14 1 * *` runs an hour *before* the
`register-monthly-refresh` it consumes, on the same day. That is the same dependency inversion the
previous bundle had, now wearing a staggered schedule, which is harder to spot than when
everything sat at 09:00.

### What the verification found

The working hypothesis was a channel gap of the kind ADR-037 had just repaired: `use_case_notes`
is threaded to `org_planner` and nowhere else, so the generators that emit schedules never see the
prose. The first half is true — `use_case_notes` has exactly four references in `src/`, and none
of them is downstream of org planning.

**The hypothesis was nonetheless wrong about where the boundary is, and the difference decided the
design.** Routine emission is not an LLM generator. `renderers/routines.py` is pure code reading
exactly one input, `TaskDefinition.recurrence`, a `str | None` documented as *"a normalized token
(`daily`/`weekly`/`monthly`/`quarterly`) or a comma-separated lowercase weekday list."* That type
has no slot for a clock time, no slot for a day-of-month, and no slot for a timezone. `org_planner`
— which *does* see the full prose, times included — is instructed to normalise onto exactly that
vocabulary. The times are destroyed one step before the boundary the hypothesis named.

Four specific findings:

1. **No 015 regression.** `git show 53912e6 -- routines.py` preserves the weekday branch
   character-for-character; only the `0 9 ` prefix moves out. `weekly` mapped to day-of-week 1
   before and after; `quarterly` to day-of-month 1 before and after. Monday-instead-of-Tuesday and
   the-1st-instead-of-the-5th both predate feature 015 and go back to `ee7ed48`.

   The sharper correction is to an earlier assessment, not to 015. `tue` **is** reachable —
   `day_pattern_for` maps the token to day-of-week 2 — so weekly-Tuesday binding was never a
   mechanism, only an LLM normalisation that had previously come up heads. The assessment credited
   a binding that was luck. The 5th and the 8th were never reachable at all: no branch in
   `day_pattern_for` can emit any day-of-month except `1` or `*`. That is a hard expressiveness
   ceiling, and no hand-editing at the brief level reaches past it.

2. **The FR-008 ordering check was silenced by its textual-reference gate.** Both routines are
   monthly, so the day-pattern gate passes; assembly at hour 14 against refresh at hour 15 means
   the ordering comparison would have fired. `_references_task` is the sole reason it did not — it
   requires the consumer's objective to contain the producer's slug or name on a word boundary, and
   an LLM writes the dependency as prose.

3. **The timezone was never dropped — there is no channel for it.** `RoutineSpec.timezone` defaults
   to `"UTC"` and is never assigned. `CompanyBrief` has no timezone field and the input template
   never mentions one. ADR-036 shipped knowing this; `routines.py` says so in its own source: the
   6–17 window is justified by *human working hours* but applied in UTC, and "those coincide only
   for a UTC-ish operator." For a Helsinki operator in summer the real window is 09:00–20:00 local,
   so a morning heartbeat can legitimately land at 20:00. The window's stated rationale is not
   merely unmet; without a timezone it is unmeetable.

4. **The 015 commit's premise was verified against the wrong thing.** It asserts "the brief format
   collects no clock times, so no stated time was ignored." True of the field set. False of the
   artifact — section 7 is free prose and the operator put times in it.

## Decision

### 1. Stated schedule values bind through one machine-readable channel; prose carries the reasoning

The operator expresses ordering by sequencing the times and saying why. A second channel for
re-declaring dependencies is rejected: two machine-read encodings of one fact can disagree, and no
tiebreak between them is principled. If stated times bind, correct ordering follows for free.

The obvious objection is that a structured schedule channel is the same redundancy — the operator
states the schedule twice, once as reasoning and once as values. It is not, and the reason is an
asymmetry in how the two failures degrade:

- **Two machine channels drifting** produces a contradiction with no principled winner. The
  generator must choose arbitrarily, and the bundle is wrong in a way nothing can adjudicate.
- **One machine channel plus prose drifting** produces a determinate schedule and stale
  documentation. Worse for the reader, ordinary, and visible on read.

The case that would break this — prose asserting that ordering matters while edited values violate
it — does not, because the ordering check operates on values and catches the violation independently
of what the prose claims. Prose is not a channel here; nothing reads it. So a structured schedule
channel is the *first* machine-readable encoding of a fact currently encoded only in prose, not a
second encoding of a fact already bound. This is the shape section 12 already has: prose explains
why you would cap turns, `parse_run_policy_line` reads the numbers, and nobody calls section 12
redundant.

### 2. The company timezone binds now, and only that (spec 017)

One optional company-level IANA zone name in the brief, flowing to every emitted routine's schedule
trigger. Absent means the current default, and a brief that states nothing must produce
byte-identical output. An unrecognised zone aborts the run before any generation call — falling
back to the default would move an entire company several hours with no signal in the bundle, which
is the operator being ignored rather than corrected.

This is deliberately the narrow half. It repairs the 6–17 window's stated rationale, making the
existing spread defensible instead of documented-as-broken in its own source, and it discharges
feature 015's explicit deferral of the timezone default. It does not touch `recurrence`, the
spread, or any advisory check.

**Zone resolution is host-independent, and the residual variance is a loud failure rather than a
silent one.** Resolving a zone name by filesystem lookup takes the host's case sensitivity with it:
`europe/helsinki` resolves on macOS and not on case-sensitive Linux, and resolves to whatever casing
it was handed rather than to the canonical spelling. The same brief would then emit two different
bundles on two machines — the salted-`hash()` failure of ADR-036 in different clothes, equally
silent and equally invisible on the machine you develop on. Resolution therefore goes through the
enumerated zone set, which has no filesystem semantics, and canonicalisation returns the set's own
member — never a string transformation, since real entries like `Etc/GMT-3` and `US/Eastern` are not
title-case and any capitalisation rule breaks them while appearing to work on `europe/helsinki`.

This does not make resolution fully deterministic across machines, and claiming so would be an
overclaim. The installed zone database still varies by vintage and by source, so a zone present on
one machine can be absent on another. **What changes is the failure mode, and that is the property
worth having**: divergence now surfaces as a rejection naming the value, not as a bundle that
differs in a spelling nobody reads. Residual variance converted into a visible failure is the
achievable goal; eliminated variance is not.

The field goes in the brief's existing operator-working-pattern section rather than a new one,
because the brief parser keys on section *numbers*: a new section inserted mid-document would
renumber adapter preferences, canon and run-policy overrides underneath every brief written to
date. That is a correctness constraint wearing a placement costume. The same property is preserved
by appending future sections after the last one — which is where the schedule grammar's section
will go.

### 3. The cheap fix is dead, and the reason generalises

The proposed small fix was to thread section 7 to the task generator, reusing ADR-037's machinery.
It is dead. `cron_for` reads `t.recurrence` and nothing else, and `recurrence` cannot hold a clock
time, a day-of-month or a zone. Pipe section 7 into every generator in the tree and the emitted
cron is byte-identical. There is no middle option between doing nothing and changing the model.

**The generalisable lesson: check whether the destination can hold the value before assuming the
pipe is the problem.** The diagnosis reached for a threading gap because the last four defects were
threading gaps — a shape that had been correct often enough to stop being examined. A data-model
check is cheap and answers the question the channel check cannot.

### 4. The schedule grammar is next, and this ADR records conclusions only

The grammar is justified: the day-of-month ceiling means the tool structurally cannot express "the
5th of the month," and that is not reachable by hand-editing a brief. It is a full spec comparable
to feature 014, so 017 ships as the timezone alone and the grammar follows immediately as its own
spec and its own ADR.

Settled conclusions, carried here as insurance against slippage:

- A strict line grammar shaped like section 12's run-policy overrides — values in lines, reasoning
  in the surrounding prose.
- Its own section, appended after the current last section to preserve the numbering property above.
  Not folded into section 7, which is documented as free prose about org shape; a strict grammar
  inside a free-prose section invites the parse ambiguity the grammar exists to remove.
- The cadence representation must change on every path. `TaskDefinition.recurrence` cannot hold a
  trigger regardless of how it is populated, so this is not a design question.
- Scope is the full trigger — day-of-month, day-of-week, time-of-day — not only clock times.
- A stated schedule bypasses `org_planner` for the trigger. Association is keyed on the **agent** the
  schedule line names, since org_planner must materialise that agent anyway, with a warning when a
  line matches no recurring task.
- The blake2b spread is demoted to the per-line fallback for schedules that state no time — which is
  what it should always have been.
- The FR-008 reference gate is left as-is, not loosened. With times binding, the primary mechanism no
  longer depends on it, and loosening would trade a silent miss for noisy false positives.

**The full argument is deliberately not repeated here.** The grammar is next, not deferred, so its
own ADR will carry the reasoning while it is fresh and cite this one for the finding. Recording
conclusions twice is insurance; recording the whole argument twice makes the later ADR authoritative
and this one a decoy.

### 5. Two instances recorded against ADR-036

Both are instances of classes ADR-036 already names. Per that ADR's own boundary — *four members is
a family; a fifth means consolidating around the shared principle rather than extending the
enumeration* — neither is filed as a new class.

**An instance of the third class (a fixture that agrees with the implementation).**
`tests/test_routines.py:276` builds the FR-008 positive case as
`f"Summarise the output of the {producer_slug} task from today."` — it *interpolates the producer
slug*, so `_references_task` is guaranteed to pass. The negative case at :316 tests word-boundary
precision ("scandal") rather than realism. Nothing exercises an objective phrased the way an LLM
phrases one. The check was verified against its own gate rather than against the phenomenon, and it
then went silent on the exact instance it was built for.

What makes this worth recording rather than quietly repairing: the docstring at
`render.py:249-253` argues at length that the check was corrected from trigger-equality to ordering
*specifically so it would not go silent once the spread separated the pair*. It went silent anyway,
through the other gate. Both design choices were individually defensible; the composition failed.
The class recurs — that is the finding.

**The same shared principle, one level up: verified against the schema, never against the channel
the schema was summarising.** The 015 premise "the brief format collects no clock times" was checked
against `CompanyBrief`'s fields, which is where it is true, and never against section 7, which is
where the operator wrote the times. This is not a test agreeing with an implementation but an audit
agreeing with a model, and it is the most compact statement of how all of this happened: *green
means the artefact you checked agreed with you, not that you checked the right artefact.*

## Consequences

### Positive consequences

- A generated schedule can be expressed in the operator's own hours, so the spread window means what
  its rationale says.
- The 015 deferral of the timezone default is discharged rather than carried forward.
- The channel principle is written down before the grammar is built, so the grammar's spec argues
  mechanism rather than re-arguing whether redundancy is acceptable.
- The day-of-month ceiling is now documented as a structural limit rather than being rediscovered as
  a generation defect on the next bundle.

### Negative consequences

- The brief gains a field, and a brief can now be rejected for a reason it could not be rejected for
  before. This is intended, but it is new friction.
- Between 017 and the grammar, a brief may state a timezone and still have its stated times, days
  and ordering ignored — a partial repair that could read as a complete one. The grammar following
  immediately is the mitigation; a long gap here would be the failure mode.
- Prose and values can drift once the grammar lands, leaving stale documentation. Accepted knowingly
  under the asymmetry above.

### Neutral consequences

- Feature 017 changes no existing bundle: every brief written to date omits the field and produces
  byte-identical output.
- The trigger format and the platform's handling of a declared zone remain provisional pending live
  import, exactly as before. This changes which zone is declared, not the contract for a trigger.

## Alternatives considered

- **Thread section 7 to the task and routine generators (the cheap fix).** Rejected: the destination
  cannot hold the value. `cron_for` reads `recurrence` and nothing else. See Decision 3.
- **LLM extraction of times into a structured field.** Rejected: it reintroduces nondeterminism into
  schedule emission, and the experiment has already been run — the day-of-week loss diagnosed here
  *is* an LLM extraction failure, in production, in `org_planner`. It produced Monday.
- **A separate dependency-declaration channel.** Rejected: ordering is already fully determined by
  the times. Two machine channels for one fact can contradict each other with no principled winner,
  and a brief could contradict itself.
- **Fold the schedule grammar into section 7.** Rejected: a strict grammar inside a section
  documented as free prose invites parse ambiguity. Its own appended section costs nothing and
  preserves the numbering property.
- **Loosen the FR-008 textual-reference gate.** Rejected: it trades a silent miss for noisy false
  positives on a check the primary mechanism will no longer depend on. Recorded rather than repaired.
- **Widen feature 017 to include the grammar.** Rejected: expanding a validated spec is worse than
  shipping it and starting the next one.
- **Per-agent or per-routine timezones.** Rejected for now: one company is scheduled for one
  operator's attention. Widening later is additive.

## References

- `specs/017-routine-timezone/spec.md` — the timezone feature
- ADR-036 — routine scheduling defaults and collision detection; the hazard classes and the
  four-member boundary this ADR respects
- ADR-037 — brief canon threading; the channel-gap repair whose shape did not apply here
- ADR-034 / feature 014 — section 12's run-policy override grammar, the precedent for a strict line
  grammar beside explanatory prose
- ADR-022 — the Paperclip object model; routines as the delivery carrier for scheduled work
- `src/paperclip_blueprints/renderers/routines.py` — cadence→cron translation, the spread, and the
  hardcoded timezone
- `src/paperclip_blueprints/renderers/render.py` — the three advisory routine checks
- `53912e6` — feature 015's commit, whose premise is recorded above
