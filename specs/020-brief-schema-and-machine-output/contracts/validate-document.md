# Contract — the `validate` machine-readable document

Postconditions asserted by `tests/test_serialisation.py` and `tests/test_cli.py`.

## Invocation

**V1.1** `blueprints validate --input <brief>` emits human output exactly as it does today; nothing
about the default mode changes (FR-021).

**V1.2** `blueprints validate --input <brief> --json` emits one JSON document on stdout and no
human-oriented text on stdout (FR-020).

**V1.3** Exit status is 0 when the brief is valid and 1 when it is not, whichever failure class
applies. The class is read from the document, not from the status.

## Shape

```json
{
  "schema": "blueprints.validate/1",
  "valid": false,
  "failureClass": "structural",
  "fieldsChecked": false,
  "structuralFindings": [
    {
      "kind": "heading_mismatch",
      "ordinal": 11,
      "found": "Adapter preferences (optional)",
      "expected": "Operating canon"
    }
  ],
  "fieldMessages": [],
  "advisories": [
    { "kind": "undeclared_section", "ordinal": 13, "message": "…" }
  ]
}
```

On a valid brief:

```json
{
  "schema": "blueprints.validate/1",
  "valid": true,
  "failureClass": null,
  "fieldsChecked": true,
  "structuralFindings": [],
  "fieldMessages": [],
  "advisories": [],
  "brief": { "name": "…", "slug": "…" }
}
```

## Field rules

**V2.1** `schema` is present and versioned (FR-022).

**V2.2** `failureClass` is one of `"structural"`, `"field"`, `null` — a declared vocabulary, never a
message string and never an exception name (FR-023).

**V2.3** `kind` on every finding and advisory is from its declared vocabulary (FR-023).

**V2.4** `fieldsChecked` is `false` whenever `structuralFindings` is non-empty, and `fieldMessages`
is empty in that case (FR-016).

**V2.5** `brief` carries `name` and `slug` and nothing else, and is present only when `valid` is true
(FR-028).

**V2.6** `brief` states the same name and slug as the human line `brief OK: {name} ({slug})`,
asserted by comparing the two modes rather than each separately (SC-012).

**V2.7** No key holds an absolute path (FR-027).

## Determinism

**V3.1** Two runs on the same input produce byte-identical stdout (INV-001).

**V3.2** Key order is fixed by construction and does not vary with input content.

**V3.3** Findings and advisories are ordered by ordinal then by a fixed kind order, never by
discovery order.

**V3.4** The document ends with exactly one newline and is written as UTF-8.
