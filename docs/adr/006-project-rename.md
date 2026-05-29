# ADR-006 — Project Rename: Company Configurator → Paperclip Blueprints

**Status:** Accepted
**Date:** Pre-v0.1, before any code is written
**Supersedes:** Implicit naming choices in ADRs 001-005, which referred to the project as "Company Configurator" / `company-configurator` / `configurator`

---

## Context

The project was initially named "Company Configurator" with the repo slug `company-configurator` and the Python package/CLI both named `configurator`. The name was a description of the tool's behavior (it configures a company), not a memorable proper noun.

Before pushing the skeleton to GitHub or writing any code, the project needs a name fit for a repo URL and a CLI binary that the operator will type often. "Paperclip Blueprints" was proposed:

- "Paperclip" names the domain (the bundles are for Paperclip companies)
- "Blueprints" describes what the tool produces (importable bundles, not running deployments) more accurately than "Configurator" did
- The compound is memorable and short enough for a repo URL

The original name's only redeeming feature was that it was descriptive. The new name keeps that and gains memorability.

## Decision

Rename the project from "Company Configurator" to "Paperclip Blueprints" across all dimensions:

| Dimension | Before | After |
|---|---|---|
| Display name | Company Configurator | Paperclip Blueprints |
| GitHub repo slug | `company-configurator` | `paperclip-blueprints` |
| Top-level directory | `company-configurator/` | `paperclip-blueprints/` |
| Python module | `src/configurator/` | `src/paperclip_blueprints/` |
| PyPI distribution name (when published) | `company-configurator` | `paperclip-blueprints` |
| CLI binary | `configurator` | `blueprints` |
| Generic self-reference in docs | "the configurator" | "the tool" (lowercase) or "Blueprints" (proper noun sentence-initial) |

### Rationale for the CLI binary name

Three candidates were considered:

- `blueprints` — single word, short, easy to type. No common clash on a standard dev machine. Chosen.
- `paperclip-blueprints` — unambiguous but verbose. Would be the PyPI distribution name only.
- `pb` — tempting (two letters, fastest to type) but two-letter binaries clash with installed tools too often (`pb` is taken by `pastebinit` on some distros, `protobuf` aliases elsewhere). Rejected.

`blueprints generate --input ...` reads cleanly. `blueprints validate` reads cleanly. The verb-first convention works.

### Generic self-reference in docs

The old docs used "the configurator" as a generic noun ("the configurator does X", "the configurator's output"). The literal replacement "the blueprints does X" doesn't read as English (plural noun, singular verb). Two strategies in the rewritten docs:

- **"Paperclip Blueprints" (proper noun)** in titles and first mentions per file
- **"the tool"** in running prose where the proper noun would be repetitive

This matches how Cargo, Poetry, and similar docs handle the same problem — proper noun for emphasis, generic descriptor for flow.

## Consequences

**Positive:**

- The name is more memorable and more accurate (blueprints, not configurations).
- Short CLI binary (`blueprints`) is pleasant to type repeatedly.
- No existing code or external dependencies to break — the rename happens before any push, any commit beyond the initial skeleton, and before any code is written.
- "Paperclip Blueprints" sets the stage for related future tools under the same brand (`paperclip-deploy`, `paperclip-doctor`, etc.) if any are ever built.

**Negative:**

- Minor inconsistency between the PyPI distribution name (`paperclip-blueprints`) and the CLI binary name (`blueprints`). This pattern is common in Python (e.g., `python-dateutil` distributes `dateutil`; `psycopg2-binary` distributes `psycopg2`); not a problem, but worth noting in `pyproject.toml`'s `[project.scripts]` block when it's created.
- ADRs 001-005 used "Company Configurator" and `configurator` in their text. They've been updated in the rename sweep, but historical readers should know the project was once "Company Configurator." This ADR is the canonical record.

**Risks accepted:**

- Some future Paperclip ecosystem tool may also want the name "Blueprints." Unlikely to be a real conflict (the namespace is small) but possible. If it happens, this tool's full name "Paperclip Blueprints" disambiguates.

## Alternatives considered

1. **Keep "Company Configurator" / `configurator`.** Rejected — the name doesn't describe what the tool produces accurately, and `configurator generate` is one verb too many (the tool generates configs; "configurator generate" is redundant).
2. **`paperclip-cli`.** Rejected — implies it's the official Paperclip CLI, which it isn't. Paperclip has its own CLI (`paperclipai`).
3. **`paperclip-spec` / `paperclip-bundles` / `paperclip-companies`.** Considered. "Blueprints" won on memorability — the others describe the output too literally.
4. **`pclipbp` or other compressed forms.** Rejected for unmemorability.
