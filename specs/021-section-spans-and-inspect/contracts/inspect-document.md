# Contract — the `inspect` document

Postconditions asserted by `tests/test_serialisation.py`, `tests/test_api.py` and
`tests/test_cli.py`.

## Invocation

**I1.1** `blueprints inspect --input <brief>` emits human output; `--json` emits one document on
stdout with no human text beside it.

**I1.2** It is a **separate command**, never a flag on `validate`. One command emitting two
document shapes would force a consumer to branch on which it received.

**I1.3** Exit status is 0 when the brief is valid and 1 when it is not. The failure class is read
from the embedded validation document, not from the status.

## Shape

```json
{
  "schema": "blueprints.inspect/1",
  "validation": {
    "schema": "blueprints.validate/1",
    "valid": true,
    "failureClass": null,
    "fieldsChecked": true,
    "structuralFindings": [],
    "fieldMessages": [],
    "advisories": [],
    "brief": { "name": "…", "slug": "…" }
  },
  "sections": [
    { "ordinal": 1, "heading": "Company name and slug", "span": { "start": 120, "end": 388 } }
  ],
  "brief": { "name": "…", "slug": "…", "northStar": "…", "goals": ["…"], "…": "…" }
}
```

## Composition

**I2.1** `validation` is the **validate document verbatim**, produced by the same serialiser. One
definition of what a failure is.

**I2.2** A change to the validation document's shape appears here automatically. Asserted by
comparing this key against the `validate` command's own output for the same brief, rather than
against a fixture of what it used to look like.

**I2.3** The two `schema` versions are independent. A new brief field bumps `blueprints.inspect`,
never `blueprints.validate`.

## What appears when

**I3.1** `sections` is present **whenever the document is produced**, including for a brief that
fails structurally.

**I3.2** `brief` is present **only when parsing succeeded**, and is `null` otherwise.

**I3.3** The rule behind I3.1 and I3.2: spans are observations, values are interpretations. A
span says *this region is the section headed X at ordinal N*, which stays true even when N should
not be X. Interpreting misaligned text yields artifacts; observing where text sits yields none.

**I3.4** `sections` includes every scanned section — beyond-range ordinals, duplicated ordinals,
and sections carrying absorbed headings. Filtering to the declared twelve would turn an
observation into an interpretation.

**I3.5** The key set does not vary with outcome: `sections` and `brief` are present on every
document, `brief` as `null` when there are no values.

## The projection

**I4.1** Values reach the document through an **explicit projection**, one entry per field on the
brief model. Never a model dump: the wire contract has to be stable independently of the model.

**I4.2** Document keys follow the casing of the two shipped documents.

**I4.3** A test asserts the projection covers **every** field on the brief model. A new field
fails the suite until it is deliberately projected or deliberately excluded.

**I4.4** The projection fixture gives every field a value **obviously distinguishable** from
every other field's. The exhaustiveness test and the round-trip check both walk the projection's
own table and share its defects; only the fixture can expose a transposition.

## Determinism and hygiene

**I5.1** Two runs on the same brief, in **separate processes** with differing environments,
produce byte-identical output.

**I5.2** No key holds an absolute filesystem path.

**I5.3** The document ends with exactly one newline and is written as UTF-8.

## Non-regression

**I6.1** `validate` and `check-canon` produce byte-identical output to what they produce today,
in both human and machine modes.

**I6.2** The in-process entry point returns a typed result; the document is produced by a
separate serialiser, so the two cannot disagree. Asserted by serialising the typed result and
comparing it to the command's stdout.
