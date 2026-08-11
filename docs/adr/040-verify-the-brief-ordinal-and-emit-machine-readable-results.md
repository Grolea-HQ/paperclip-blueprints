# ADR-040: Verify the brief's section ordinal, and emit machine-readable results

## Status

Accepted

## Date

2026-08-11

## Context

The brief parser keys every field on a section number and nothing checked that the section
carrying a number was the section that number names. A document renumbered by one inserted
section parsed successfully with a field silently absent: enum fields fail loudly, but
optional free text — the operating canon above all — simply loses its anchor and falls out
of the payload. Two adjacent defects shared the root: a repeated ordinal silently kept one
body, and a heading the splitter did not recognise had its body absorbed into the section
above. Separately, the canon check's excluded-field set existed twice in the codebase,
character for character.

## Decision

The ordinal remains the identity key; a declared schema verifies it. `models/brief_sections.py`
declares each ordinal's canonical heading, its genuine historical aliases, and whether the
section is required, and `parse_brief` asserts that before reading any field. Comparison is
normalised, so the alias set carries renames rather than spelling.

Four faults are reported, each independently asserted: heading mismatch, duplicate ordinal,
missing required section, and an absorbed heading. Structure gates fields — on any finding,
no field is examined and the result says so. A beyond-range ordinal is advisory, and names a
likely mistyped ordinal when a declared section is also absent.

One definition of a heading serves both the absorption check and the section splitter, and it
skips fenced code blocks.

`canon_exclusions` becomes the single definition of the excluded-field set, replacing two
identical copies. `api.py` owns the analysis and returns typed results; `serialisation.py`
turns them into documents; both commands are callers. `validate` and `check-canon` gain
`--json`, emitting a versioned document whose every state is readable from a declared
vocabulary field.

**Scope.** v0.1b named parser correctness but not a programmatic surface; this feature adds
one. Ratified against Principle V on the deduplication first — that is code health standing
on its own, in code that exists today — with the stable entry point following from it as the
place the single definition lives, and the documents following from having one analysis to
serialise.

## Consequences

- A renumbered brief is an error naming each displaced section, where it previously parsed
  clean without its canon.
- The shipped template's two unnumbered trailing sections moved above section 1. They had
  been contributing twenty checklist and closing-guidance lines as run-policy overrides.
- Field errors are no longer reported for a structurally broken brief. Clearing both classes
  can take two runs, which is honest: until the structure is right, the field errors describe
  the wrong text.
- The template's headings and the schema now fail together. Editing either alone breaks one
  test, in both directions.
- Section reordering remains impossible. An explicit machine key is an additive upgrade if it
  ever becomes a requirement.
- `check-canon` stays advisory: exit 0 for any completed scan, unreachable from the bundle
  validators, both asserted structurally.
- Extending the brief with a new section means updating the declaration as well as the
  template. That is the intended cost.

## Alternatives considered

- **Heading text as the identity key:** rejected because section 11 was headed "Anything
  else" before "Operating canon" while its anchor never moved — this would have dropped the
  canon from every brief predating the rename.
- **An explicit machine key (HTML comment or front-matter manifest):** rejected for now
  because it changes a hand-written format, needs a second parsing path for unkeyed briefs,
  and needs a rule for partially keyed ones.
- **Reporting field errors alongside structural ones:** rejected because they are artifacts
  of parsing the wrong text; reporting them presents guesses as results.
- **Rejecting a beyond-range ordinal:** rejected because it would make a brief written
  against a newer template a hard failure against an older tool.
- **Exempting everything after the last declared section:** rejected as exemption by
  accident — it would exist only because the template happened to be shaped that way, and
  would silently cover a real absorption later.
- **Echoing the full parsed brief in the `validate` document:** rejected because it
  duplicates the brief model into a versioned wire contract, so every future brief field
  would pay a synchronisation cost.

## References

- `specs/020-brief-schema-and-machine-output/` — spec and contracts
- ADR-037 — the operating canon channel this protects
- ADR-038 — established append-only section placement as a correctness property
- `tests/fixtures/brief_baseline_020/` — frozen pre-change parse results
