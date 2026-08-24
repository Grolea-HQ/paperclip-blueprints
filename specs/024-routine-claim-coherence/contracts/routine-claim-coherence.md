# Contract: a bundle may not assert a rhythm it carries no routine for

Postconditions asserted by the test suite. Cites FR/SC ids from [spec.md](../spec.md).

## C1 — the generator can see whether a routine will exist

**C1.1** (FR-001) `generate_operations` accepts the agent slugs that own recurring work. An empty
collection means no routine will be emitted.

**C1.2** (FR-001, FR-003) `bundle.py` derives those owners from the generated tasks carrying
recurrence, deduplicated and in plan order, and passes them.

**C1.3** (FR-002) With no owners, the rendered prompt states that this bundle will carry no routine,
asks for an idle-state protocol that claims no schedule, and asks for empty routine slots.

**C1.4** (FR-003) With owners, the rendered prompt names them and asks for routine slots drawn from
them — not from the whole agent list.

**C1.5** (SC-004) With owners, the rendered prompt is otherwise unchanged from its pre-feature text,
so bundles that emit routines are unaffected.

## C2 — a zero-routine claim is rejected at the call

**C2.1** (FR-009) With no routine owners, a response whose idle-state protocol or routine slots
assert a schedule is rejected at the operations call.

**C2.2** (FR-009, SC-005) The rejection re-samples that call within the existing attempt budget; a
clean second response completes the run.

**C2.3** (FR-009) The rejection message names what was claimed, so the re-sample can land.

**C2.4** With routine owners present, no such rejection occurs whatever the prose says — the check is
scoped to the zero case, where falsity is unambiguous.

## C3 — I16: no carrier asserts a trigger the bundle does not have

**C3.1** (FR-004, FR-008) When the rendered `.paperclip.yaml` carries no `routines:` entries, a
mechanism term in `OPERATIONS.md` is a violation.

**C3.2** (FR-006, SC-003) The same term in `agents/<slug>/AGENTS.md` is a violation, reported per
agent file. This is the leading finding: the protocol is propagated to every agent.

**C3.3** (FR-005) Each violation names the file and the offending term.

**C3.4** (FR-007) With at least one `routines:` entry, I16 emits nothing, whatever any carrier says.

**C3.5** (FR-004) Cadence adjectives alone — "weekly", "daily", "each morning" — do not trigger I16.
An operator-driven rhythm needs no routine, and rejecting it would make the rule wrong in the case
the operator most likely wrote deliberately.

**C3.6** (FR-004) The reported instruction — *"on each scheduled run, audit that no gate is
unowned"* — is caught.

**C3.7** `--single-agent` bundles have no `OPERATIONS.md` and no `OperationsDefinition`; I16 emits
nothing for them.

## C4 — the design consequence is reported, not graded

**C4.1** (FR-011) A bundle emitting zero routines produces exactly one advisory through the `warn`
sink.

**C4.2** (FR-011) It states that no routine is emitted and that no agent has a trigger from this
bundle.

**C4.3** (FR-012) It does not say "inert", does not assert anything about heartbeats, and contains no
word grading the design or recommending a change.

**C4.4** (FR-011) It is never a validation error: a zero-routine bundle whose prose claims nothing
validates cleanly and is written to disk.

**C4.5** A bundle emitting at least one routine produces no such advisory.

## C5 — nothing regresses

**C5.1** (SC-002) A full bundle generated from a brief with no recurring tasks validates and is
written. This is the regression the validation rule would cause on its own, and it is the reason
US1 and US2 ship together.

**C5.2** (SC-004) For a bundle that emits routines, every generated file is byte-identical to the
pre-change output, asserted against a baseline captured before any edit.

**C5.3** (FR-013) V-idle still holds on the zero-routine protocol, and V-gov still finds the
idle-state protocol in every `AGENTS.md`.

**C5.4** (FR-010) No code path rewrites, strips or otherwise repairs generated prose to satisfy I16.
Asserted by inspection as well as behaviour.

**C5.5** ADR-044 records the rule, the mechanism/adjective line as a deliberate omission, and the
reversal of the no-new-inputs decision with the false premise that motivated it.
