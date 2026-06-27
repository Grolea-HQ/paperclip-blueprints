# ADR-022: One deployment model (Paperclip object model) — deliver the constitution where agents actually receive it

## Status

Accepted — gate-validated. Drives spec 010 (full spec-kit flow with TDD). Extends ADR-013
(import fidelity); revises ADR-002 (the role of `OPERATIONS.md`) and reframes the deployment
model in CLAUDE.md.

## Date

2026-06-26

## Context

A generated bundle imported into a Paperclip company runs **ungoverned** and tells agents to
read a **company-root filesystem that does not exist**. Verified against the Paperclip
companies spec, importer source, and a live import (ADR-007). The granular firsthand evidence
and incident detail are recorded in the local `docs/deployment-gaps.md` (G-P11/G-P12/G-P13);
this ADR records the decision framed as our own reasoning.

### One deployment model

There is **one** deployment model: a **Paperclip company, database-backed, imported**. "Hermes"
is **not** a separate whole-company deployment — it is a **per-agent adapter setting**
(`claude_local` / Hermes / codex, ADR-017) for specific roles. The constitution and governance
are **always Paperclip-sourced**, regardless of an agent's adapter. There is **no native-Hermes
whole-company deployment** — the concept is deleted, not demoted to a rare target. So this is
**object-model-only**; there is no "filesystem mode" to gate behind.

### Storage is split

Agents are **not** filesystem-less. Storage is **split**: **skills materialize as on-disk
catalog files and are agent-reachable** (an agent can edit a catalog `SKILL.md` and the change
goes live); **company, operations, projects, issues are database-backed** — there is **no
company-root tree**. The **only** filesystem an agent may have is its **adapter's own working
directory** — a code/work `cwd` — referenced **only for code tasks**, never for the
constitution/governance.

### What is dropped on import

The data model is Company → Projects → Issues → Documents → Comments, plus
Agents/Goals/Skills/Routines. There is **no "Operations" object**, so `OPERATIONS.md` is
**dropped entirely**. `COMPANY.md` is only **partially** ingested: name/slug/description
populate the company record, but "we are"/"we are not", constraints, north star, and **goals**
are not modeled fields and do **not** survive (goals are not surfaced in the company UI). So the
governance we work hardest to generate never reaches the running company.

### The carriers that reach agents

The per-agent **instruction bundle is `AGENTS.md` + `SOUL.md` + `HEARTBEAT.md` + `TOOLS.md`** —
all four reach the agent. `AGENTS.md` is the primary instruction/mandate carrier. Beyond the
instruction bundle: **Routines** (ingested) carry cadence; **`.paperclip.yaml` company
settings** carry the one importable governance gate (`requireBoardApprovalForNewAgents`);
**Skills** (on-disk catalog) inject when relevant; **issue Documents** are an issue-scoped
backstop. There is **no importable construct** for strategy/spend/custom board reviews or
per-task review gates (those are runtime approval requests cleared in the UI), and no confirmed
company-context auto-injection.

### A live incident: operating rules mis-carried in HEARTBEAT, and a faulty idle-state rule

Operating/"critical rules" content was duplicated into each agent's `HEARTBEAT.md` — wrong
twice: `HEARTBEAT.md` is meant to be the agent's near-empty runtime journal, not a rules
carrier; and a generated idle-state rule ("leave the issue `in_progress` when a routine is the
live continuation path") caused a watch agent to spin on a long-lived `in_progress` issue,
re-waking endlessly (an `in_progress` issue is health-check-demanded constantly, and with
wake-on-demand the agent re-wakes without end).

## Decision

### 1. Object-model-only — no filesystem deployment mode

Generated companies target the **database-backed Paperclip object model**, the single
deployment model. Hermes is a **per-agent adapter** setting, not a deployment. `TOOLS.md` is
**not** made "mode-aware"; the company-root / `COMPANY.md`-as-constitution / `OPERATIONS.md` /
memory-file assumptions are **removed entirely and unconditionally**.

### 2. Deliver the constitution via the instruction bundle — targeted, distributed

Stop treating `OPERATIONS.md`/`COMPANY.md` *files* as the agents' constitution. Distribute the
**relevant** content across the four carriers — do **not** duplicate the whole `COMPANY.md`
into every agent:

- **`AGENTS.md`** carries, per agent: mandate, decision rights, the **idle-state protocol**, and
  the operating/anti-drift rules that agent must enforce. The **CEO** additionally carries the
  full board-gate/approval language, the company critical rules, and the company **goals** (which
  do not survive import).
- **`SOUL.md`** carries the persona-level "we are not" refusals.
- **`HEARTBEAT.md`** is the **genuinely-empty** runtime journal at import — no rules, no file
  references.
- **Routine slots → Routines** (ingested).
- **Hiring board-gate → `requireBoardApprovalForNewAgents: true`** in `.paperclip.yaml` (the one
  importable structured gate). **All other board-gates → CEO `AGENTS.md` prose** (escalate;
  "ready for Board review"; never self-approve/auto-close) — Paperclip exposes no importable
  construct for them.
- **`OPERATIONS.md` stays human/operator documentation only**; the issue-Document operating
  manual is an optional backstop, never the primary carrier.

### 3. Remove the company-root file-read assumptions; keep only the adapter work-dir, for code

Agents are never told to read the constitution/governance from files. Remove: the `TOOLS.md`
"File system" section and company-tree line; the `HEARTBEAT.md` file references and duplicated
rules. The **only** filesystem `TOOLS.md` may reference is the agent's **adapter work `cwd`, for
code/work tasks only**.

### 4. Correct the idle-state protocol

The generated idle-state protocol MUST state: routine-driven recurring work produces **one
short-lived issue per scheduled run**, worked and **closed the same run**; an issue is **never**
left `in_progress` as a liveness marker (the **routine schedule** is the liveness); agents
produce **zero output** on wakes with nothing to do.

### Scope guard

This realigns *where and to whom* the bundle's content is delivered and corrects one generated
rule; it does not expand the tool toward a fixed catalogue of templates/presets/roles, and the
output stays bespoke (same guard as ADR-015/016).

## Consequences

### Positive
- Governance reaches running agents (instruction bundle) instead of being dropped on import.
- Agents stop hunting for a non-existent company-root tree, and stop spinning on `in_progress`
  liveness markers.
- Output matches the single real deployment path; no manual document re-attachment.
- Targeted, distributed delivery keeps each carrier lean and `HEARTBEAT.md` empty as intended.

### Negative / limitations
- The relevant constitution is **duplicated** from `COMPANY.md`/`OPERATIONS.md` into the
  instruction bundle (and `.paperclip.yaml`/Routines); the generator must keep them in sync.
- Most board-gates remain prose (only the hiring gate is structurally enforceable on import).

### Neutral
- `OPERATIONS.md`/`COMPANY.md` remain in the bundle (human docs / company record); their *role*
  changes, not their presence. Skills remain on-disk catalog files.

## Alternatives considered

- **Mode-aware `TOOLS.md` (filesystem vs objects).** Rejected — one deployment model; Hermes is a
  per-agent adapter; a mode toggle encodes a conflation.
- **Keep `OPERATIONS.md`/`COMPANY.md` as the agents' files.** Rejected — dropped/unread on import.
- **Duplicate the whole `COMPANY.md` into every agent.** Rejected — bloats carriers; targeted
  per-role delivery suffices.
- **Carry operating rules in `HEARTBEAT.md`.** Rejected — `HEARTBEAT.md` is the empty runtime
  journal; carrying rules there caused the spin incident.
- **Deliver all board-gates structurally.** Not possible — only `requireBoardApprovalForNewAgents`
  is importable; the rest are runtime approval requests with no manifest field.

## Phase-3 doc edits (greenlit)

- **CLAUDE.md**: state plainly that Hermes is a **per-agent adapter setting** and there is **no
  native-Hermes whole-company deployment mode**; remove "default deployment = native Hermes".
- **ADR-002**: revise `OPERATIONS.md`'s role (human/operator docs, not an agent constitution
  carrier).

## References

- ADR-013 (import fidelity — extended here to COMPANY/OPERATIONS content + the storage model),
  ADR-002 (revised: OPERATIONS.md role), ADR-007 (source hierarchy), ADR-016 (governance content
  now delivered via the instruction bundle), ADR-017 (adapters as a per-agent choice — the
  correct frame for Hermes)
- Local: `docs/deployment-gaps.md` G-P11 (constitution dropped on import), G-P12 (company-root
  file-read assumption), G-P13 (operating rules mis-carried in HEARTBEAT + idle-state spin)
- Spec: `specs/010-object-model-constitution/`
- Templates touched: `templates/tools_md.j2`, `templates/heartbeat_md.j2`, and the agents/soul/
  operations generators
