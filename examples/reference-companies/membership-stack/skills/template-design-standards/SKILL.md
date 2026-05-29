---
schema: agentcompanies/v1
slug: template-design-standards
name: template-design-standards
description: 'The visual, file-format, and instruction standards every template in the Membership Stack library follows so members can use a template within minutes of opening it — driving asset library growth that compounds rather than clutters.'
---

# template-design-standards

*A template a member can't immediately use is a template that didn't ship.*

## When to load this skill

- The Template/Asset Designer is starting a new template (week-1 Monday slot).
- A returning template is bumping a MAJOR version and the contract changes need a fresh design pass.
- The Product Manager is QA-checking a template before it enters the library.
- A support thread reveals members are confused by a specific template — design needs review.
- An export-format check is failing (Google Sheets to .xlsx, Google Docs to .docx/PDF, etc.).

## Inputs

- The job-to-be-done the template solves (one sentence, drawn from a quarterly survey wish-list or release plan).
- The stated experience level of the target member (solo operator, agency lead, creator).
- A list of editable input fields the template will accept.
- The expected fill-in time (used to set the cover-sheet estimate and the QA timing check).

## Mandatory elements per template

1. **Cover sheet / first page.** Title, version (`vMAJOR.MINOR`), intended use, time-to-fill estimate.
2. **Example pre-filled version.** Same file — a duplicate tab in a sheet, a `_example` copy in a doc, an example slide deck variant. Members must see a worked example, not just an empty form.
3. **Inline instructions.** In the file itself, not in a separate README or guide. Members do not read separate docs.
4. **Editable fields clearly marked.** Color highlight, cell shading, or `[fill here]` placeholder convention.
5. **Branded footer.** Library version + retrieval URL so a forwarded copy can find its way home.

## File-format matrix

| Primary format | Required exports | Owner check |
|---|---|---|
| Google Sheets | .xlsx | Template/Asset Designer |
| Google Docs | .docx + PDF | Template/Asset Designer |
| Google Slides | .pptx | Template/Asset Designer |
| Other | requires Product Manager approval before build | Product Manager |

## QA checklist before a template enters the library

- Open in incognito with a fresh account — works without the designer's session.
- Read the instructions cold — a member at the stated experience level understands them.
- Time the fill-in — actual time matches the cover-sheet estimate within 25%.
- `INDEX.md` and tags match the approved taxonomy.
- No formulas reference the designer's personal account or external data.
- Export formats render correctly in their target apps — not "mostly fine".

## Procedure

1. Scope against the job-to-be-done and target experience level.
2. Build the cover sheet first — title, version, intended use, fill-in time estimate.
3. Add the editable structure, mark fields, write inline instructions as you go.
4. Build the example pre-filled version in the same file.
5. Run the QA checklist. Fix anything that fails — no "we'll catch it in v1.1".
6. Hand to the Product Manager. PM approves the release; CEO approves the slot.

## Outputs

- `library/templates/<category>/<asset-slug>/` containing the template file(s), `INDEX.md`, and `release-notes.md`.
- An export-format verification note recorded in the release notes ("`.xlsx` verified in Excel 365 on macOS 14, retained formula behavior").
- A line in the weekly cohort report under "content velocity" and "library count".

## Anti-patterns

- Shipping a template without an example pre-filled version — the example IS the documentation.
- Templates that require a paid third-party tool the member may not own (Notion Pro features, paid Airtable extensions) — every template must work on the member's likely-free stack.
- Templates with formulas referencing the designer's personal account, file ID, or external sheet — they break on first copy.
- "Frameworks to think about" templates — every template solves a concrete task end-to-end, not a thinking exercise.
- Instructions in a separate doc — members do not read separate docs. Instructions are inline or they don't exist.
- Skipping the export-format check because "the Google version works" — half our members open via .xlsx / .docx / PDF.

## Reference

Pair this skill with:
- `asset-library-architecture` for the folder layout and `INDEX.md` schema.
- `tool-build-process` for the parallel standards applied to tool-type assets.
