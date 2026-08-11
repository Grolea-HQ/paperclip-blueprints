# Contract — the in-process entry point

Postconditions asserted by `tests/test_api.py`.

## Surface

`paperclip_blueprints.api` exposes:

| Callable | Returns | Raises |
|---|---|---|
| `validate_brief(markdown: str) -> BriefReport` | Typed report. Never raises for an invalid brief — invalidity is a value. | Nothing for brief content. |
| `parse_brief_strict(markdown: str) -> CompanyBrief` | The parsed brief. | `BriefStructureError` or `BriefValidationError`, both `BriefError`. |
| `check_canon(brief: CompanyBrief, files: Mapping[str, str]) -> CanonReport` | Typed report. | Nothing. |
| `canon_exclusions(brief: CompanyBrief) -> list[str]` | The brief fields excluded from canon extraction. | Nothing. |

`paperclip_blueprints.serialisation` exposes one function per document, each taking a report and
returning a JSON-ready structure. Serialisation performs no analysis.

## Rules

**E1.1** `validate_brief` returns rather than raises, so a caller need not use exceptions for control
flow. `parse_brief_strict` raises, for callers that want the brief or nothing.

**E1.2** `check_canon` takes an already-loaded path → content mapping. It performs no filesystem
access, which is what keeps it testable without a bundle on disk and keeps path resolution out of the
analysis layer.

**E1.3** `canon_exclusions` is the only definition of the excluded-field set in the codebase (FR-031).
Asserted by a test that greps the source for a second construction of that list.

**E1.4** `renderers/render.py` obtains its exclusions from `canon_exclusions`, replacing its current
inline copy. `cli.py` does the same, replacing its own. Before this change the list exists in two
places, character for character.

**E1.5** The CLI holds no analysis: both commands call the entry point and then either format for
humans or serialise (FR-032).

**E1.6** For the same inputs, the entry point's typed results and the CLI's machine-readable output
carry the same information — asserted by serialising the entry point's result and comparing it to
the command's stdout (FR-030).

**E1.7** Adding a field to the excluded-field set changes both the command's and an in-process
caller's results, demonstrated by one test that exercises both paths (SC-009).

## Stability

**E2.1** The names above are the supported surface. Anything else in these modules is internal.

**E2.2** A document's `schema` version changes when its shape changes incompatibly; the report types
may gain fields without a version change, since callers read fields by name.

**E2.3** The entry point performs no network access and reads no environment variable. Asserted by
the existing no-API-call test pattern: constructing a client would fail, and neither path constructs
one.
