# ADR-015: The portable-bundle vs operator-environment boundary

## Status

Accepted

## Date

2026-06-20

> Pure decision record — no behavior change. It captures a principle that governs
> which post-generation wiring the tool may pull into the bundle, and is the gate
> for the per-agent model-id feature (issue #4). ADR-016 (governance anti-drift)
> was taken first because it ships a live defect; this fills the reserved 015 slot.

## Context

The tool's value is bespoke synthesis: a brief in, a complete, importable company
bundle out. Generation is the fast, solid part. The opportunity ahead is for the
tool to progressively own more of the **post-generation wiring** that an operator
otherwise sets by hand after import — safe run-policy and approval defaults (ADR-016),
skill→agent attachments (already shipped in the bundle), per-agent model preference
(proposed), and similar. Each such move makes the generated company more "ready to
run" out of the box.

But not everything *can* ride a portable bundle. A bundle is meant to import into
**any** Paperclip instance and produce the same company. Anything specific to one
operator's machine, account, or tenant — secrets, credentials, host paths, gateway
URLs, tenant/JWT configuration — cannot ride a portable bundle, because it would be
wrong (or unsafe) on a different instance. Without a stated principle, each "should
the bundle own this?" decision gets re-argued from scratch, and there's a standing
risk of either under-reaching (leaving wiring manual that could safely ship) or
over-reaching (baking environment-specific values into a bundle and breaking
portability or leaking secrets).

The upstream package format already encodes half of this boundary: its export rules
omit secret values, secret references, machine-local ids, and absolute/host paths,
and place vendor adapter/runtime config in the Paperclip sidecar (`.paperclip.yaml`)
rather than the vendor-neutral base files. This ADR lifts that into a first-class,
explicit design principle for *this* tool, so it can be applied deliberately and
consistently going forward.

## Decision

Adopt the **portability line** as a first-class design principle. For any piece of
post-generation wiring, apply this test:

> **Does this ride a portable bundle to any instance unchanged, or is it specific to
> one operator's environment?**
>
> - **Portable → the bundle may own it.** It is the same on every instance and
>   reproduces the intended company anywhere.
> - **Environment-specific → it stays the operator's to set**, outside the bundle,
>   by design — never baked in.

### What rides the portable bundle

- Company identity and constitution (`COMPANY.md`).
- Org structure and reporting tree; agent mandates, personas, decision rights.
- Skills and **skill→agent attachments** (AGENTS.md `skills:` — already shipped).
- Governance and approval *language* and run-policy *defaults* (ADR-016): board-gate
  authority, escalation posture, per-task policy hints.
- **Per-agent model *id* preference** (e.g. `adapter.config.model`) — a portable
  statement of which model a role should use, the same on any instance. (Enables
  issue #4.)

### What stays operator-environment (never in the bundle)

- Secrets and credentials — API keys, `PAPERCLIP_API_KEY`, tokens, vault references.
- Host paths and machine-local identifiers.
- Gateway/provider **routing**: base URLs, provider selection, env-driven gateway
  configuration — these depend on what the operator's instance actually runs.
- Tenant / auth configuration: per-company JWT signing keys, tenant scoping (a
  deployer-time, per-instance concern).
- Per-instance model **availability** (which models a given gateway actually serves)
  — distinct from the portable model *preference* above.

### The model-id nuance (records the SHOULD-2 rationale)

Shipping a per-agent model **id** is portable — it is a preference that means the
same thing on every instance. Shipping gateway/provider routing, base URLs, or keys
for that model is **not** portable and stays operator-set. So the per-agent model
feature (issue #4) ships only the model-id preference and leaves provider/gateway/
credentials below the line. This rationale stands on its own design merits — the
feature is portable, sits on the right side of this boundary, and is de-risked by the
session-continuity-across-model-swap fix in the current platform release.

### Scope guard

This principle decides *whether* a piece of wiring may ride the bundle; it does not
license expanding the tool toward a fixed catalogue of templates, presets, or roles.
The output stays bespoke. (Same guard as ADR-016.)

## Consequences

### Positive
- Every future "should the bundle own this?" question has one test to apply, applied
  consistently.
- The bundle can progressively own more *portable* wiring (more "ready to run") while
  the line keeps secrets, host config, and tenant/auth firmly operator-side.
- Unblocks the per-agent model-id feature (issue #4) with a clear, pre-agreed limit.

### Negative / limitations
- The line is a judgement applied per case; borderline items (e.g. a model id whose
  availability varies by instance) still need a call — the model-id/availability
  split above is the worked example for how to make it.

### Neutral
- No code or generation change. It is a principle that subsequent ADRs/specs cite.

## Explicitly deferred (recorded so they are not lost)

- **Registering generated skills to the company Skills catalogue** — a publish action
  toward the company-scoped catalogue, not bundle content; revisit as a deployer-side
  capability if wanted.
- **Multi-tenant auth wiring** (per-company JWT keys, tenant scoping) — a v0.2
  deployer concern, firmly below the line (environment/auth).
- **Env-driven gateway routing for local adapters** — operator-environment; the tool
  may *document* it but does not bake it into the bundle.

## Alternatives considered

- **Decide ownership case-by-case with no stated principle.** Rejected — invites
  inconsistent calls and risks baking environment-specific values into bundles.
- **Keep all adapter/runtime wiring out of the bundle entirely.** Rejected — it
  leaves portable, safe wiring (model-id preference, approval defaults) manual for no
  benefit; the line, not a blanket exclusion, is the right tool.
- **Let the bundle carry environment config too (gateways, keys) for convenience.**
  Rejected — breaks portability and risks leaking secrets; these are the canonical
  operator-environment items.

## References

- ADR-002 (output bundle format), ADR-007 (source-of-truth hierarchy),
  ADR-012/013 (prior portable wiring: budgets, import-fidelity), ADR-016 (governance
  anti-drift — same scope guard)
- The upstream package-format export rules (omit secrets/secret-refs/machine-local
  ids/absolute paths; adapter config in the `.paperclip.yaml` sidecar)
- Issues #3 (this ADR), #4 (per-agent model id — gated on this boundary)
