# Contract — the `check-canon` machine-readable document

Postconditions asserted by `tests/test_serialisation.py`, `tests/test_cli.py` and
`tests/test_canon.py`.

This document serialises states the canon module already distinguishes. It introduces no new
semantics, and it reports reach, never quality.

## Invocation

**K1.1** `blueprints check-canon --input <brief> --bundle <dir>` emits human output exactly as it
does today (FR-021).

**K1.2** `--json` emits one JSON document on stdout and no human-oriented text on stdout (FR-020).

**K1.3** Exit status is 0 for any completed scan, whatever it finds — missing terms, thin terms, an
unmarked section 11, or nothing at all (INV-002).

**K1.4** Exit status is non-zero only for an operational failure: an unreadable brief, a `--bundle`
that is empty, not a directory, or carries no bundle marker, or a bundle with no readable text files.
The existing guards keep their behaviour.

## Shape

```json
{
  "schema": "blueprints.check-canon/1",
  "outcome": "scanned",
  "filesScanned": 84,
  "counts": { "carried": 9, "thin": 2, "missing": 1, "notSearchable": 1 },
  "terms": [
    {
      "text": "The maintenance-priority rubric",
      "block": null,
      "state": "thin",
      "carriers": ["skills/triage-intake/SKILL.md"]
    },
    {
      "text": "Access difficulty",
      "block": "The maintenance-priority rubric",
      "state": "missing",
      "carriers": []
    }
  ],
  "extractionFindings": [
    { "kind": "sentence_shaped_items", "message": "…" }
  ]
}
```

When the brief states no operating canon:

```json
{
  "schema": "blueprints.check-canon/1",
  "outcome": "no_canon_stated",
  "filesScanned": 0,
  "counts": { "carried": 0, "thin": 0, "missing": 0, "notSearchable": 0 },
  "terms": [],
  "extractionFindings": []
}
```

## Field rules

**K2.1** `outcome` distinguishes `"scanned"` from `"no_canon_stated"`, so a brief with no canon is
never indistinguishable from full coverage (FR-026).

**K2.2** `state` is one of `carried`, `thin`, `missing`, `not_searchable` — the four the module
already distinguishes (FR-024).

**K2.3** `not_searchable` corresponds to a term the module declines to probe, and such a term is
never reported as missing.

**K2.4** `carriers` are bundle-relative paths, sorted, and empty for `missing` and `not_searchable`.

**K2.5** `extractionFindings` are distinct from term states — extraction failing is a different
condition from a term not landing (FR-025).

**K2.6** `filesScanned` is a count. The bundle directory path appears nowhere in the document
(FR-027).

**K2.7** No message field is load-bearing: every state and finding kind is readable from a declared
vocabulary field alone (SC-007).

## Advisory invariant

**K3.1** Nothing in the canon path raises for a coverage finding.

**K3.2** `validators/` does not import the canon module, directly or transitively. Asserted as a
structural test, not by inspection (INV-002).

**K3.3** The document states reach only. No field expresses a judgement about whether canon was
encoded usefully.

## Determinism

**K4.1** Two runs on the same brief and bundle produce byte-identical stdout, on any machine
(INV-001, SC-006).

**K4.2** `terms` follow first-appearance order in the canon; `carriers` are sorted. Neither derives
from iterating an unordered collection.

**K4.3** No ordering or value depends on filesystem traversal order or case sensitivity.

**K4.4** The document ends with exactly one newline and is written as UTF-8.
