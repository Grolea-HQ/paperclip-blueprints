# ADR-016: Governance naming and board-gate anti-drift in generated bundles

## Status

Accepted

## Date

2026-06-20

> ADR-015 is reserved for the portable-bundle-vs-operator-environment boundary
> (tracked separately). This ADR (016) is taken first because the defect below
> ships in every generated company today.

## Context

Two governance failures were observed operating a generated company, and the
generator propagates both into *every* bundle it produces:

1. **Role-name collision.** The top agent was titled "Founder / CEO", colliding
   with the human founder/board who actually runs and approves for the company.
   The generator causes this directly: `prompts/org_planner.md`'s output example
   names the root agent `"Founder / CEO"`, and nothing bars an agent name/title
   that collides with the human principal's role.
2. **Self-approval drift.** Agents wrote "Founder approved" / "Board approved" and
   **auto-closed board-gated tasks** — approving on the human board's behalf
   instead of escalating to it.

The tool already exists to enforce structural anti-drift rules (goal-as-outcome,
span-of-control, "we are not"). Governance authority and naming are the same class
of rule: every generated company inherits its approval language and its top-agent
naming, so the correct place to fix this is the generator, not each deployment.

Platform-level guards in the current Paperclip release (self-comment / terminal
reopen guards; auto-complete of approved review comments) reduce some runtime
self-interaction but do **not** make the *bundle* ship correct naming or approval
language. The bundle must encode it.

### Design principle adopted: ownership chains

To make the governance encoding coherent rather than a list of don'ts, model every
capability or responsibility as an **ownership chain**: a defined **primary owner**
agent, an **ordered fallback**, and the **CEO as the final backstop**. The goals:

- No responsibility is ever orphaned.
- The company degrades gracefully when a role is absent — there is always a defined
  owner and a clear escalation path.

This reinforces the anti-drift posture: every capability has an accountable owner,
agents **escalate rather than self-approve**, the **CEO orchestrates**, and the
**human Board is the sole approver**. The existing single-root, acyclic reporting
tree (validator rules I1/I3) already *structurally* guarantees the chain — every
non-root agent reports upward to exactly one manager, terminating at the CEO. This
ADR makes the generated *prose* state that chain explicitly and adds the missing
naming and approval-authority rules on top of it.

### Scope guard (non-negotiable)

The tool's value is **bespoke synthesis of an original company from a brief.** This
ADR borrows only the ownership-and-escalation *concept* into the governance
encoding. It does **not** introduce a fixed catalogue of prebuilt templates,
presets, or roles — that is a different product shape and would dilute the bespoke
output. The generator keeps inventing the company; it just governs it correctly.

## Decision

Encode three governance rules into the generators (prompts + templates) and enforce
the mechanizable ones with validators.

1. **Naming guard (deterministic).** No generated agent's `name` or `title` may
   collide with the human principal's role. The human founder/board sits **above**
   the company as its approver and is **never an agent**. The root agent is the
   **CEO** (or a company-specific executive title), never **"Founder"**,
   **"Co-founder"**, or **"Board"**. Reserved role-words (case-insensitive, as a
   standalone name component): `founder`, `co-founder`, `cofounder`, `board`.
   - `prompts/org_planner.md`: fix the output example (`"Founder / CEO"` → `"CEO"`)
     and state the rule; `prompts/identity_generator.md`: state that the human
     owner/board is the company's principal and is never personified as an agent.
   - **Validator I13** (integrity): reject any agent whose `name`/`title` contains a
     reserved role-word as a standalone token.
   - `owner` is intentionally **not** reserved (legitimate roles like "Product
     Owner" exist); the collision risk is specifically the founder/board principal.

2. **Board-gate authority (prompt-encoded + presence-checked).** Generated
   `OPERATIONS.md` and `AGENTS.md` make the **human Board the sole approver** of
   board-gated decisions. No agent — not even the CEO — approves on the Board's
   behalf, records "Board approved" / "Founder approved" itself, or auto-closes a
   board-gated task. Agents mark such work **"ready for Board review"** and
   escalate; the CEO **orchestrates and routes to the Board** and never
   self-approves. `can_approve` is limited to work genuinely within an agent's own
   authority; board-gated matters always go to `must_escalate`.
   - Encoded in `operations_generator.md` (`approval_merge_rules`, `critical_rules`)
     and `agents_generator.md` (decision rights, `escalation_text`).
   - **Validator S11** (schema-shape): assert the rendered `OPERATIONS.md` carries
     board-as-approver / escalate-don't-self-approve framing (presence check, in the
     style of the existing anti-drift coverage check S7). Prose correctness beyond
     presence is enforced by the prompts, as with the other P-PAT rules.

3. **Ownership-chain framing (prompt-encoded).** The org planner designs the tree so
   every capability has one accountable owner; the generated `OPERATIONS.md`
   delegation/critical-rules and each `AGENTS.md` mandate state the primary owner,
   the ordered fallback, and the CEO as final backstop — "no responsibility is
   orphaned; the company degrades gracefully when a role is absent." This is prose
   encoding layered on the already-guaranteed single-root tree; no new model field.

## Consequences

### Positive
- Every generated company stops shipping the founder/board name collision and the
  self-approval language — the two observed production failures — by construction.
- Governance reads as a coherent ownership model (accountable owner → fallback →
  CEO backstop, Board approves) rather than a list of prohibitions.
- The deterministic naming guard (I13) is fully testable and catches the exact
  failure (`"Founder / CEO"`).

### Negative / limitations
- Board-gate *prose* correctness is prompt-encoded and only presence-checked (S11),
  not fully mechanizable — same limitation as the existing P-PAT anti-drift rules.
- The reserved-word list is deliberately narrow (founder/board family) to avoid
  false positives on legitimate roles; a cleverly-worded collision could still slip
  the deterministic check and rely on the prompt + review.

### Neutral
- No new Pydantic model or field; encoded in existing prose fields and the existing
  reporting-tree structure.
- The reserved-word list and the S11 phrasing are policy, tunable without structural
  change.

## Alternatives considered

- **A fixed catalogue of governance-correct role templates.** Rejected by the scope
  guard — it changes the product from bespoke synthesis to a template library and
  dilutes the differentiator. Only the ownership concept is borrowed.
- **A structured `fallback_owner` field on the agent model.** Rejected (YAGNI): the
  single-root reporting tree already encodes the fallback chain; adding a field
  duplicates it and invites a template-shaped model. Prose + structure suffice.
- **Fully validating approval prose.** Rejected as infeasible/brittle; presence
  check + prompt encoding matches how the codebase already handles anti-drift prose.
- **Reserving `owner` too.** Rejected — false positives on legitimate roles
  ("Product Owner"); the collision risk is the founder/board principal specifically.
- **Relying on platform self-comment/reopen guards.** Rejected — they operate at
  runtime and do not make the bundle ship correct naming/approval language.

## References

- ADR-004 (prompt architecture), ADR-008 (generation), ADR-012/013 (prior
  generation-behavior features and the validator-rule numbering), ADR-009
  (in-stack validators)
- Internal best-practice patterns: governance-spectrum calibration, "we are not"
  anti-drift, span-of-control — this ADR is the same class of structural rule
- `prompts/{org_planner,identity_generator,operations_generator,agents_generator}.md`;
  `validators/{integrity,schema_shape}.py`
