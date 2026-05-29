# CONTEXT — Paperclip Blueprints glossary

The shared language of this project. Definitions only — no implementation
details, no decisions (those live in `docs/adr/`). When a term here conflicts
with how code or prose uses a word, the glossary wins; fix the drift.

---

## Approval type

A **Paperclip runtime concept** for categorizing approval flows between agents
and the operator. The four built-in types, verified against the Paperclip source
(`packages/shared/src/constants.ts`, `APPROVAL_TYPES`):

- `hire_agent`
- `approve_ceo_strategy`
- `budget_override_required`
- `request_board_approval`

(The earlier project assumption of `strategy` / `hire_agent` / `budget_override`
/ `custom` was wrong on three of four. Source: github.com/paperclipai/paperclip,
MIT.)

Approval types are a runtime routing concern. They do **not** appear as literal
tokens in `AGENTS.md`. The canonical `agentcompanies/v1` AGENTS.md body is free
prose instructions; decision rights, when expressed, are plain prose that maps to
these categories at runtime — e.g. "Sponsorship deals over $5,000" routes to a
`budget_override_required` flow without the token appearing in the document.
Enum-in-prose like "Pricing changes (budget_override)" is explicitly avoided.

## agentcompanies/v1

The open package format the bundles target. **The bundle-shape oracle is the
local `examples/reference-companies/`** (community-blessed canonical examples, per
ADR-002), governed by the source-of-truth hierarchy in [[007-source-of-truth-hierarchy]].

The Paperclip repo also ships a minimal `agentcompanies/v1` spec
(`.agents/skills/company-creator/references/companies-spec.md`; web:
agentcompanies.io/specification). It is a **secondary oracle** — useful for
verifying machine-level facts the references leave ambiguous, but it does NOT
override the reference shape. Where they collide, references win. Known
collisions:

- The repo spec lists `slug` as a required COMPANY.md frontmatter field; the
  reference companies omit it → **the generator omits it too** (references win).
  If a real import ever rejects on `slug`, that's the first thing to revisit.
- `tone` / `mono` are not repo-spec fields — they are a Paperclip vendor
  extension under `metadata.paperclip` that the references carry, so the generator
  emits them. `mono` is the company monogram letter, derived from the name
  (Newsletter→N, Agency→A, …); `tone` is one of the six the identity prompt offers.
- `metadata.sources` appears in the references as a `- kind: url` stub, so the
  generator mirrors that shape literally (no fabricated value).
