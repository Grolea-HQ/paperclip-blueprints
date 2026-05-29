# ADR-002 — Output Bundle Format

**Status:** Accepted
**Date:** Pre-v0.1, during the rework after reference example configs landed
**Supersedes:** The output specification in the original CLAUDE.md and MASTER_PROMPTS.md (which described a 7-file bundle: `company-spec.md`, `thesis.md`, per-agent SOULs and AGENTS, `ORG.md`, `routines.yml`, `deployment-plan.md`).

---

## Context

The original project skeleton specified v0.1 output as a small bundle of ~7 files. When two real-world example Paperclip companies were obtained (`newsletter-press`, `niche-site-empire`), the actual best-practice output structure turned out to be substantially different:

- ~80 files per company, not 7
- Two distinct schema names in use (`paperclip/v1` for the runtime config, `agentcompanies/v1` for portable content)
- A directory hierarchy with `agents/`, `projects/`, `tasks/`, `skills/` subdirectories
- Several runtime-mutable files (e.g., `PROJECT-INVENTORY.md`) seeded with starter content
- An intentionally near-empty `HEARTBEAT.md` runtime journal per agent
- No `thesis.md`, no `routines.yml`, no `deployment-plan.md` in the best-practice format

The tool's output must match what Paperclip actually imports. Continuing with the original 7-file spec would have produced bundles that fail Paperclip's import flow.

## Decision

The v0.1 output bundle conforms to the structure of the reference example companies:

```
<company-slug>/
├── .paperclip.yaml          # schema: paperclip/v1 — sidebar, agents map, projects map
├── COMPANY.md               # schema: agentcompanies/v1 — frontmatter (name, description, goals,
│                            #   metadata.paperclip.tone) + body (Identity, We are, We are not,
│                            #   North star, Constraints)
├── README.md                # auto-generated overview, mermaid org chart, agent links, goals, projects
├── OPERATIONS.md            # phase model, idle-state protocol, reporting cadence, approval rules,
│                            #   delegation checklist, anti-drift checks, duplicate prevention,
│                            #   routine slots, critical rules summary
├── PROJECT-INVENTORY.md     # completed/in-flight deliverables tables, starter projects, protocol
├── LICENSE.txt
├── agents/<agent-slug>/
│   ├── AGENTS.md            # frontmatter (slug, name, title, reportsTo, skills[]) + body
│   │                        #   (Mandate, Triggers, Workflow handoffs, Deliverables, Decision rights,
│   │                        #   Escalation)
│   ├── SOUL.md              # body only (Identity, What we are, Product reality, What I believe in,
│   │                        #   How I act, What I don't do, My north star)
│   ├── HEARTBEAT.md         # near-empty runtime journal — Steps/Routines/Critical rules sections
│   │                        #   intentionally blank at import time
│   └── TOOLS.md             # Paperclip API config, file system paths, role-specific tools,
│                            #   conventions
├── projects/<project-slug>/
│   └── PROJECT.md           # frontmatter (slug, name, owner) + description + success condition
├── tasks/<task-slug>/
│   └── TASK.md              # frontmatter (slug, name, project, assignee) + objective +
│                            #   completion criteria
└── skills/<skill-slug>/
    └── SKILL.md             # frontmatter (slug, name, description) + When to load, Inputs,
                             #   Procedure, Outputs, Anti-patterns, Reference
```

### Two schema names

- `paperclip/v1` — only in `.paperclip.yaml`. This is the runtime/sidebar config that Paperclip's import flow reads first.
- `agentcompanies/v1` — used in COMPANY.md frontmatter and every per-entity frontmatter (AGENTS.md, PROJECT.md, TASK.md, SKILL.md). This is the portable-content schema.

The blueprints generates both, validates against both before writing files to disk.

### File counts (typical company)

- Top-level files: 6 (`.paperclip.yaml`, `COMPANY.md`, `README.md`, `OPERATIONS.md`, `PROJECT-INVENTORY.md`, `LICENSE.txt`)
- Per agent: 4 files (AGENTS, SOUL, HEARTBEAT, TOOLS). A typical company has 8-16 agents → 32-64 files.
- Per project: 1 file. Typical: 2-4 projects → 2-4 files.
- Per task: 1 file. Typical: 4-8 tasks → 4-8 files.
- Per skill: 1 file. Typical: 8-12 skills → 8-12 files.

Total typical: 50-100 files per company. The reference companies are at the high end (newsletter-press: 81 files; niche-site-empire: 91 files).

## Consequences

**Positive:**

- Generated bundles match what Paperclip actually imports. v0.1's "useful starting point" exit criterion is achievable; the previous spec wouldn't have been.
- The structural fidelity is enforceable via schema validators — bundles that fail the schema check don't get written to disk.
- A lot of files become pure Jinja templates (no LLM call): HEARTBEAT.md, TOOLS.md mostly, README.md, `.paperclip.yaml`, PROJECT-INVENTORY.md, LICENSE.txt. This reduces cost and improves consistency.

**Negative:**

- v0.1's time estimate roughly doubles (from 8-16h to 20-30h). This is mitigated by the v0.1a/v0.1b split (see ADR-005).
- Prompt count goes from 4 to 6-8 (see ADR-004).
- More test surface area — every template, every prompt, every schema validator needs coverage.
- The reference companies in `examples/reference-companies/` become a dependency for prompt design (they're used as few-shot structural references). They must be sanitized so they don't leak operator-identifying content.

**Risks accepted:**

- The Paperclip schemas (`paperclip/v1`, `agentcompanies/v1`) may evolve. The tool may need updates when Paperclip releases a new schema version. We accept this risk; the schemas have been stable in the reference examples and the docs.
- Some files in the bundle are runtime-mutable (PROJECT-INVENTORY.md gets updated by agents as they work). The tool only seeds initial content; subsequent updates are Paperclip's runtime concern.

## Alternatives considered

1. **Keep the original 7-file spec.** Rejected — the bundles wouldn't import into Paperclip.
2. **Generate only `.paperclip.yaml` and COMPANY.md, leave the rest for the operator.** Rejected — the operator value of the tool is largely in the per-agent content generation; cutting it removes the main reason to use the tool.
3. **Generate everything in a single big YAML file and have a post-processor split it into the directory tree.** Rejected — splitting is mechanical work that doesn't earn its complexity; Jinja templates direct-render to the right paths.
