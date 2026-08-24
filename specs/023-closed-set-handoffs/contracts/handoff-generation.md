# Contract: handoff generation against a closed set

Postconditions asserted by the test suite. Cites FR/SC ids from [spec.md](../spec.md).

## C1 — the request states the legal set

**C1.1** (FR-001, FR-003) For a multi-agent company, the schema sent with the mandate request types
`receives_from` and `hands_to` as arrays of objects with an `agent` property and a `flow` property —
not arrays of strings.

**C1.2** (FR-001, FR-002) That `agent` property carries an `enum` whose members are exactly the
slugs of every agent in the plan except the one being generated. Neither more (no self) nor fewer
(no restriction to manager/reports/peers).

**C1.3** (R1) The `enum` survives schema projection: `strict_json_schema` and `_strict_node` do not
strip it, and the objects it sits in carry `additionalProperties: false`.

**C1.4** (FR-001) The rendered prompt lists the same legal slugs it constrains, so the instruction
and the constraint cannot disagree.

**C1.5** (FR-009, R6) For a single-agent company, neither `receives_from` nor `hands_to` appears in
the schema's `properties` or its `required` list, and the prompt asks for neither.

## C2 — an out-of-set target is rejected, at that call

**C2.1** (FR-004) A returned target that is not in the legal set raises rather than being carried
into `AgentDefinition`.

**C2.2** (FR-006) The raised message names the agent being generated, the field, the offending
target, and the legal set.

**C2.3** (FR-005, SC-001) The rejection re-samples that single call within the existing attempt
budget. A transport that returns a bad target once and a good one next yields a valid
`AgentDefinition`, having made exactly two calls.

**C2.4** (FR-005, R5) The re-sample's prompt carries the check's own message. It does not tell the
model its reply was not valid JSON — the reply was valid JSON.

**C2.5** (FR-006, SC-002) A transport that returns a bad target on every attempt fails at that
agent, and the failure names the offending target. No further agent's mandate is requested as a
consequence.

**C2.6** (FR-013) An entry whose target is empty, whitespace-only, or absent is rejected under C2.1,
not skipped.

**C2.7** (R4) An entry that is a joined string rather than an object is rejected under C2.1.

## C3 — the guarantee does not rest on the schema binding

**C3.1** (FR-007, SC-004) With the output constraint never applied — a transport that ignores the
schema entirely, and a transport that rejects it so `complete_json` drops it — an out-of-set target
is still rejected.

**C3.2** (FR-007) No branch in the check consults whether the schema was sent, accepted, or dropped.

## C4 — nothing is repaired

**C4.1** (FR-008, SC-003) A target one character from a real slug (`qa-led` against `qa-lead`) is
rejected. No emitted file contains `qa-lead` as a consequence of that entry.

**C4.2** (FR-008, SC-003) The repository contains no similarity, edit-distance, `difflib`, or
nearest-match comparison over agent slugs. Asserted by inspection as well as by test — a behavioural
assertion alone would be satisfied by a repair that guessed correctly on the sampled case.

**C4.3** (FR-011) Normalisation before the membership test strips surrounding whitespace and
enclosing backticks only. `` `qa-lead` `` is accepted; `QA-Lead` and `qa_lead` are rejected, because
a rule that accepted them could map two distinct planned agents onto one target.

## C5 — the bundle is unchanged

**C5.1** (FR-010) Handoff entries reaching `AgentDefinition` have the form `"<slug> — <flow>"`, and
`_handoff_head` returns `<slug>` for them.

**C5.2** (FR-010, SC-005) For a fixture run whose responses are all valid, every generated file is
byte-identical to the pre-change output. Asserted against a baseline captured before any edit.

**C5.3** (FR-012) `validators/integrity.py` is unchanged: I8 still runs, still checks the same
population, and its tests are untouched.

**C5.4** The four other `complete_json` call sites are unaffected — the check parameter is optional
and absent for them.

## C6 — the reasoning survives

**C6.1** (FR-007) The prohibition on collapsing the two mechanisms is recorded where an implementer
will meet it: in the code that carries the check, not only in the spec.

**C6.2** (FR-008) The prohibition on repair is recorded at the point where a near-miss is rejected,
which is where the temptation to fix it arises.

**C6.3** ADR-043 records the closed-set decision, why both mechanisms exist, and the adjacent-set
alternative as rejected with its true cost.
