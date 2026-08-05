# ADR-019: Reuse the ecosystem's commodity skills; synthesize only company-specific ones

## Status

**Proposed — deliberately deferred, not undecided.** Committed in this state so it stops
reading as an open question on every sweep. No implementation until the trigger below fires.

**Deferral trigger**: revisit when validator **I5** supports a *referenced, resolved-at-install*
skill kind. I5 currently enforces strict closure — every skill an agent references must have a
`SKILL.md` in the bundle, and every `SKILL.md` must be referenced by an agent. A commodity skill
reused from the platform catalogue has no `SKILL.md` by definition, so this decision cannot be
implemented without first widening that invariant. Until then the generator keeps synthesising
every skill, and that is the intended behaviour, not an oversight.

**Standing constraint on adjacent work** (added 2026-08-05): any feature that reasons over the
skill set must not hard-assume every skill is synthesised. In particular, a mechanical
canon-coverage check over the rendered bundle must treat a *referenced* commodity skill that
legitimately carries no company canon as **out of scope for coverage**, never as a coverage
failure. Encoding "every skill contains canon" would build in an assumption this ADR is expected
to invalidate, and would then fail loudly on exactly the bundles it was supposed to improve.

## Date

2026-06-22

## Context

The generator synthesizes **every** skill from scratch: `org_planner` invents 1–3
capability slugs per agent, and `skill_generator` (Sonnet) produces a `SKILL.md` for each
one. Most companies, however, need the *same* commodity capabilities — docs maintenance,
issue triage, task planning, QA acceptance, a GitHub PR workflow — and Paperclip already
ships these as a built-in, version-pinned, auditable skills catalogue
(docs.paperclip.ing → guides/org/skills). Synthesizing a commodity skill from scratch
spends credits to produce a *weaker, unmaintained* artifact than the vetted one the
platform already carries.

There is already an implicit acknowledgement of this in the bundle: `TOOLS.md` and
`HEARTBEAT.md` name the built-in `paperclip` and `para-memory-files` skills in prose,
assuming they exist on every instance — but they are never wired as real attachments.

### What blocks "just reference it" today

1. **Closure invariant.** Validator **I5** (and `bundle.py` `_verify`) require that every
   slug in an agent's `skills:` resolves to a generated `skills/<slug>/SKILL.md`, and that
   every `SKILL.md` is referenced by some agent. A *referenced* skill is a slug with **no**
   `SKILL.md` in the bundle, so under today's rules it is flagged as dangling. Referencing
   is impossible without a new closure model that admits "referenced, resolved at install"
   as a first-class skill kind.
2. **Install-before-attach.** An `AGENTS.md` `skills: <slug>` attachment only resolves if
   the skill is already in the **company** Skills library. Built-in catalogue skills ship
   with the instance; skills.sh skills must be installed (pinned to a commit) at company
   level *before* the attachment resolves. The bundle currently carries no install intent
   for anything it does not synthesize.
3. **Trust boundary.** Pulling arbitrary, unpinned community content would import an
   unvetted, drifting dependency into a *governed* wedge — the opposite of the catalogue's
   value. Any reuse must resolve against an explicit, vetted, pinned set.

This is the consume-side of ADR-015's explicitly-deferred "registering generated skills to
the company Skills catalogue" item, and the portability test (ADR-015) now answers it
cleanly.

## Decision

Resolve each needed commodity capability to an **existing ecosystem skill and *reference*
it**; synthesize (embed) a `SKILL.md` only when the capability is genuinely
company-specific. Five sub-decisions:

### 1. Reuse the ecosystem — do **not** build a Blueprints skill library (scope guard)

Blueprints holds only a small **resolution table of pointers** to ecosystem skills — never
skill *content* for commodity capabilities, and never a maintained library of its own. The
company-specific layer stays bespoke and synthesized exactly as today. This reuses the
commodity layer and synthesizes the company-specific layer; it does not move Blueprints
into skill maintenance. (Same scope guard as ADR-015/016/018: this does not license a
fixed catalogue of templates/presets/roles.)

### 2. Sources & trust — a vetted, pinned set; resolve in trust order

- **Primary: Paperclip's built-in catalogue** (Paperclip-managed, version-pinned,
  auditable — the correct trust level for a governed wedge). The vetted set we resolve
  against:
  - *Bundled:* docs maintenance, issue triage, task planning, QA acceptance,
    GitHub PR workflow, wireframes.
  - *Optional:* browser-driving, release announcement, design critique, recent-web
    research.
- **Secondary: skills.sh**, as an **explicit allowlist pinned to a commit** — never
  arbitrary or unpinned community content. The allowlist may start **empty**; entries are
  added deliberately, each with its pinned source string, by operator review.
- **Resolution order:** built-in catalogue → skills.sh pinned allowlist → synthesize a
  company-specific skill.

Nothing outside this vetted set is ever referenced. Anything unmatched is synthesized.

### 3. Matching — a deterministic, auditable capability→skill table, synth as fallback

The catalogue is small and known, so the mapping is a **pure, deterministic resolver**
(a `renderers/`-style function, mirroring `renderers/adapter.py` / `renderers/budget.py`),
not an LLM call — keeping the trust-sensitive decision out of model creativity. The table
maps a curated set of capability tokens/synonyms (derived from `org_planner`'s emitted slug
and title) to a catalogue/allowlist skill. A capability matches **only** on an explicit
table entry; **no confident match → synthesize** (today's behavior). This is conservative
by construction: false negatives cost a synthesized skill (status quo), never a wrong
reference. Optionally, `org_planner` can be made catalogue-aware so it *names* capabilities
in catalogue-aligned terms to raise the match rate — but the deterministic table remains
the trust anchor, not the prompt.

### 4. Reference mechanism — a skill *kind*, a declared source, and updated closure

Introduce a skill **kind**:

- **Embedded** (company-specific): unchanged — `skills/<slug>/SKILL.md` synthesized, plus
  the `AGENTS.md skills:` attachment.
- **Referenced** (commodity): **no** `SKILL.md`; the same `AGENTS.md skills: <slug>`
  attachment, **plus** a machine-readable declaration of the skill's **source** (built-in
  catalogue id, or a skills.sh source string pinned to a commit) so install-before-attach
  can happen.

The bundle carries referenced skills two ways, for two phases:

- **v0.1 (manual import):** emit the **install commands / source strings** for the
  operator (surfaced in `OPERATIONS.md` / `SETUP` / `README`), so they install the
  referenced skills into the company library before/at import, after which the existing
  `skills:` attachments resolve.
- **v0.2 (deploy step):** the deployer installs and attaches via the skills API
  (e.g. install pinned skills.sh skills, then `POST /api/agents/{id}/skills/sync`, or
  `desiredSkills` at hire). Exact API shape to be verified against the live instance at
  implementation.

**Closure model update (importability hard-gate, analogous to S12):** an `AGENTS.md` skill
slug is valid if it is **either** an embedded `SKILL.md` **or** a declared referenced skill
with a valid pinned source; every declared referenced skill must be referenced by some
agent (no orphans); and **no referenced source may fall outside the vetted set or be
unpinned**. I5 is widened to admit the referenced kind; a new check rejects
unvetted/unpinned sources.

### 5. Portability — confirmed; this answers ADR-015's consume-side deferral

Apply the ADR-015 test:

- **Built-in catalogue references are portable** — the catalogue ships with *every*
  Paperclip instance, so a referenced built-in slug means the same thing everywhere.
- **skills.sh references are portable** — pinned to a commit, they are reproducible on any
  instance.
- **Arbitrary instance-local skills are *not* portable** — exactly the concern ADR-015
  flagged; the vetted-set guard keeps them out.

So referencing these two sources sits cleanly on the **portable** side of ADR-015 and
resolves the embed-vs-reference tension. This answers the **consume** direction of
ADR-015's deferred catalogue item. The **publish** direction (registering *synthesized*
skills *up* to the catalogue) stays deferred — and for commodity capabilities becomes moot,
since we no longer synthesize them.

## Scope & sequencing (for the operator's decision)

Recommend **two specs**, phase-aligned:

- **Spec A — resolution + reference-in-bundle (v0.1, priority HIGH).** Vetted set + pinned
  skills.sh allowlist; the deterministic capability→skill resolver; embedded-vs-referenced
  skill kind; referenced-skills manifest + operator install commands in
  `OPERATIONS.md`/`SETUP`; widened I5 + new unvetted/unpinned-source gate. Fully testable
  offline (no live API); delivers the credit saving and the stronger vetted skills
  immediately. Do the vetted-set + mapping table first (highest-trust part).
- **Spec B — deployer auto-install + attach (v0.2, deferred).** Install pinned skills.sh
  skills and attach via the skills API (`/skills/sync`, `desiredSkills`). Gated on the
  v0.2 deploy foundation and live-API verification; honors phase discipline (no v0.2
  features pulled into v0.1).

## Consequences

### Positive
- Stops spending credits to produce weaker commodity skills; agents get vetted, maintained,
  version-pinned capabilities.
- The governed wedge stays governed: only a vetted, pinned set is referenced; the mapping is
  deterministic and auditable.
- Resolves ADR-015's deferred consume-side question with a clear portability rationale.
- Makes the existing implicit assumption (`paperclip`/`para-memory-files` named in prose)
  explicit and actually wired.

### Negative / limitations
- New closure model and a manifest add surface area to the validator and the bundle format.
- Match rate depends on the table's coverage; under-matching silently falls back to
  synthesis (acceptable — it is the status quo, and the no-silent-cap rule means we log when
  a capability was synthesized rather than referenced).
- v0.1 leaves install as an operator step until the v0.2 deployer closes it.

### Neutral
- Company-specific skills are synthesized exactly as today; single-agent path unaffected
  except that its one skill may now resolve to a reference.

## Open verification items (confirm against tier-1 docs / live instance, ADR-007)

- Whether built-in catalogue skills are attachable by slug directly, or require a
  company-level enable/add before an `AGENTS.md skills:` attachment resolves.
- The exact skills API shape for install + attach (`/api/agents/{id}/skills/sync`,
  `desiredSkills` at hire) — for Spec B.
- The canonical slug/key form for each built-in catalogue skill (so references match
  `normalizeSkillKey` on import).

## Alternatives considered

- **Keep synthesizing everything.** Rejected — wastes credits on weaker artifacts and
  ignores the maintained catalogue.
- **Reference arbitrary community skills by source string.** Rejected — imports unvetted,
  drifting, possibly unpinned dependencies into a governed wedge; violates the trust
  boundary.
- **LLM-driven matching of capability→catalogue skill.** Rejected as the trust anchor —
  matching must be deterministic and auditable; the LLM may *assist* slug naming but does
  not decide references.
- **Build a Blueprints-maintained skill library.** Rejected — explicitly out of scope; the
  point is to reuse the ecosystem, not become a maintainer.

## References

- ADR-002 (output bundle format), ADR-004 (prompt architecture),
  ADR-007 (source-of-truth hierarchy — catalogue is tier-1, skills.sh tier-2),
  ADR-009 (in-stack validator — I5 closure), ADR-012/017 (deterministic
  render-from-role pattern: `renderers/budget.py`, `renderers/adapter.py`),
  ADR-015 (portability boundary — this answers its deferred catalogue item),
  ADR-018 (deterministic-where-cheap, synthesize-where-fuzzy precedent)
- docs.paperclip.ing → guides/org/skills (built-in catalogue; skills.sh marketplace;
  import-by-source-string)
- Current wiring: `generators/skills.py`, `prompts/skill_generator.md`,
  `prompts/org_planner.md` (slug assignment), `validators/integrity.py` (I5),
  `templates/tools_md.j2` / `heartbeat_md.j2` (built-in skills already named in prose)
