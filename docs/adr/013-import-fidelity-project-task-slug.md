# ADR-013: Match the Paperclip importer — project description, flat task association, slug = slugify(name)

## Status

Accepted

## Date

2026-06-13

## Context

A Blueprints-generated bundle was imported into a live Paperclip
(`paperclipai 2026.609.0`) via `companies.sh add`. Every entity was *created*, but
several relationships and metadata did not survive: projects showed an empty
description, and all 17 tasks landed **unprojected** even where the task's
`project:` slug matched the project's declared slug.

Root theme: **Paperclip's importer treats the manifest + frontmatter as the
structural source of truth and re-derives or ignores some fields. Blueprints output
must match the shape the importer actually consumes.** Per ADR-007, the decisions
below were verified against the real product, not inferred:

- the `agentcompanies/v1` spec (`paperclipai/paperclip/docs/companies/companies-spec.md`),
- the importer source (`server/src/services/company-portability.ts`), and
- a fresh export of a live company (an operator-provided live company export).

### What the importer source actually does

- **Project description** comes only from frontmatter:
  `description: asString(frontmatter.description)`
  (`company-portability.ts` project parse, ~line 2851). The Markdown **body is
  ignored** for the entity description. The live export confirms it: an
  imported-without-description project re-exports with only `name:` in its
  `PROJECT.md` and an empty body.
- **Task → project association** is the flat `project:` frontmatter field:
  `projectSlug: asString(frontmatter.project)` (task parse, ~line 2900). Tasks are
  discovered **only** under the `tasks/` path prefix (`classify`, line ~196), and
  the exporter writes them flat with the comment *"All tasks go in top-level
  tasks/ folder, never nested under projects/"* (~line 3654). At apply time a task
  resolves its project via
  `importedSlugToProjectId.get(projectSlug) ?? existingProjectSlugToId.get(projectSlug)`
  (~line 4828).
- **Project slug is `slugify(name)` on create.** `projects.create()` is called
  with **no slug** (~line 4759); the DB derives `urlKey` from the name via
  `deriveProjectUrlKey`. `existingProjectSlugToId` is keyed by that `urlKey`. So a
  task's `project:` value must equal `normalizeProjectUrlKey(name)` to resolve
  against a freshly created project, regardless of what slug the package declared.
  `normalizeProjectUrlKey`: trim → lowercase → replace `[^a-z0-9]+` runs with `-`
  → strip leading/trailing `-`; collisions get a `-2`, `-3`, … suffix
  (`uniqueSlug`).

Blueprints' org planner lets the model pick arbitrary lowercase-hyphenated project
slugs (`models/org_plan.py`), so a project named "SEO Content Foundation — First
Keyword Cluster" could carry slug `seo-foundation`, while Paperclip creates it as
`seo-content-foundation-first-keyword-cluster`. Tasks referencing the short slug
then do not resolve against the created project's `urlKey`.

## Decision

1. **Project description (issue #1).** Emit `description:` in `PROJECT.md`
   frontmatter, populated from the existing `ProjectDefinition.summary` (a short
   one/two-line summary, distinct from the rich body, which stays in the template).

2. **Task association stays FLAT (issue #2).** Keep emitting tasks at
   `tasks/<task-slug>/TASK.md` with a `project:` frontmatter field. **Reject the
   nesting hypothesis** (`projects/<slug>/tasks/<slug>/TASK.md`): the importer
   discovers tasks only under `tasks/` and associates by the `project:` field, so
   nesting would make tasks *undiscoverable*. This is the spec's and the live
   exporter's actual shape.

3. **Project slug = slugify(name) (issue #3).** At generation, normalize every
   project slug to `normalizeProjectUrlKey(project.name)` (replicated exactly from
   Paperclip's `project-url-key.ts`), de-duplicate collisions with the same `-2`
   suffix rule, and rewrite every `task.project` reference and the project folder
   name to the normalized slug. A validator asserts `project.slug ==
   normalizeProjectUrlKey(project.name)` and that every `task.project` resolves to
   an existing project slug.

4. **Idempotent output guardrail.** Generating into a non-empty output directory
   must refuse/clean/warn rather than silently union with a prior generation (a
   real two-generation merge produced `-2` collision-renamed agents downstream).
   Document in SETUP/README that re-imports use `companies.sh add --target new`,
   never an import over an existing company.

## Consequences

### Positive
- A freshly generated bundle imports with tasks associated to projects, projects
  showing a description, and no manual fixup.
- Slug derivation is replicated from Paperclip's own code, so generation and
  import agree by construction.

### Negative / limitations
- `normalizeProjectUrlKey` appends a runtime UUID suffix for **non-ASCII-only**
  names (one Blueprints cannot predict). Blueprints replicates only the
  deterministic ASCII path; a project named entirely in non-ASCII characters could
  diverge. Documented; Blueprints identity content is English-centric. A validator
  warns when a project name would force the UUID path.
- Belt-and-suspenders: we keep the `project:` field *and* make the slug match, so
  association is robust to either importer code path.

## Alternatives considered

- **Nest tasks under `projects/<slug>/tasks/` (the original issue #2 hypothesis).**
  Rejected after reading the resolver: tasks are discovered only under `tasks/`;
  nesting breaks discovery entirely. The unprojected-tasks symptom is caused by the
  slug mismatch, not by flat layout.
- **Keep arbitrary LLM-chosen project slugs and rely on the declared `slug:`
  field.** Rejected: the created project's `urlKey` is `slugify(name)`, and the
  observed live import did not resolve short declared slugs; matching `slugify(name)`
  is the only construction guaranteed to resolve.
- **Put the description in the body only.** Rejected: the importer ignores the body
  for the entity description.

## References

- ADR-007 (source-of-truth hierarchy), ADR-002 (bundle format),
  ADR-012 (per-agent budgets — the prerequisite feature; budgets are settled and
  out of scope here)
- `paperclipai/paperclip` `server/src/services/company-portability.ts`
  (parse ~2851/2900, classify ~196, apply ~4759/4828, `uniqueSlug` ~1442),
  `packages/shared/src/project-url-key.ts` (`normalizeProjectUrlKey`/`deriveProjectUrlKey`),
  `docs/companies/companies-spec.md` §4/§9/§10/§14/§21
- A live company export (operator-provided) — flat `tasks/<slug>/TASK.md` with
  `project:` field; `PROJECT.md` with `name:` only when no description was set.

## Out of scope (recorded so they are not chased as Blueprints bugs)

- **Per-project goals**: not a base-package field (spec §9 has none); company goals
  live in `COMPANY.md` §6. Do not add per-project goals.
- **Skill source pinning**: only relevant if Blueprints emits externally-sourced
  skills; today it emits local markdown. Optional validator guard (assert `commit`
  on any `sources[].kind: github-*`), no behavior change.
- **Task identifiers / descriptions stripped on Paperclip *export*** are Paperclip
  round-trip limitations, not Blueprints generation bugs.
