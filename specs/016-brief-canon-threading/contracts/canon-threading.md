# Contract: Operating-Canon Threading

Postconditions the test suite asserts for the threading path (FR-001 – FR-005, FR-017).

---

## C-T1 — The canon reaches all four procedure carriers

For a brief whose section 11 is non-empty, the rendered prompt for **every** skill, agent,
task and project generation contains the canon text.

*Asserted by*: a stubbed model client capturing each rendered prompt; the canon string is
present in every captured prompt for the four generator kinds.

## C-T2 — The canon is passed wholesale and unmodified

The canon string reaching each of the four generators is **byte-identical** to
`brief.free_text`. No component truncates, summarises, re-orders, filters or per-consumer
selects from it.

*Asserted by*: equality of the captured prompt substring against the source field, for all
four generator kinds, including a canon long enough that a truncating implementation would
be caught.

## C-T3 — Exactly one read site

`brief.free_text` is read in exactly one place in the orchestration path, and the same value
object is passed to all four generators.

*Rationale*: this is the structural guarantee behind C-T2. With one read there is exactly
one place a per-consumer transformation could be introduced, which makes the wholesale
property auditable rather than merely asserted.

*Asserted by*: a source-level test that `free_text` is referenced exactly once outside the
model definition and the two pre-existing consumers (identity, org planner).

## C-T4 — Every consuming prompt states the encode-don't-paraphrase contract

Each of the four prompt files contains an explicit instruction that the operating canon is
material to be **encoded into the artifact's procedure**, not background to paraphrase or
summarise.

*Asserted by*: a test over the four prompt files asserting the contract block is present in
each. This is what makes the deliberate duplication of the block safe against drift.

## C-T5 — Absent canon is a total no-op

For a brief with `free_text` absent or empty, every rendered prompt and every rendered
bundle file is **byte-identical** to the output produced before this feature.

*Asserted by*: prompt-level and file-map-level equality against a pre-change baseline, for a
brief with no section 11.

## C-T6 — The excluded generators are not threaded

The soul, operations and goal-hierarchy generators receive no canon, and their rendered
prompts do not contain it.

*Asserted by*: absence of the canon string in the captured prompts for those three
generator kinds, for a brief whose section 11 is non-empty.

**The two exclusions are of different kinds and are recorded separately:**

- **Souls — fitness. Permanent.** Procedure is the wrong content for a persona artifact
  whose value depends on staying short; past that length the material reads as debatable
  instructions rather than identity, and the same canon is already carried by the agent
  mandate and the skill.
- **Operations and goal hierarchy — delivery. Platform-dependent.** Their artifacts do not
  reach a running agent under current import behaviour (ADR-022, verified against platform
  v2026.626.0). **Revisit if that behaviour changes.** This is not a permanent property of
  these generators.

*Asserted by*: C-T6's absence check covers all three identically; the distinction is a
documentation invariant, carried here and in the spec, not a runtime one.

## C-T7 — Canon stated only in section 11 reaches a generated skill

Content present **only** in section 11 — appearing in no other brief field — appears in at
least one generated skill.

*Asserted by*: the direct regression test for the observed defect (FR-017). This is the
assertion that would have failed on the 13-agent bundle, where a scoring rubric and a
threshold table produced zero occurrences anywhere in the output.
