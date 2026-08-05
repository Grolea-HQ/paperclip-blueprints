# Company Brief — Input Template

Fill out this template to describe the company you want the tool to generate. The tool reads this Markdown file, extracts the structured information, and produces a complete Paperclip company bundle ready to import.

**Instructions:**

- Replace all `[bracketed placeholders]` with your actual content
- The template mirrors the structure of the generated `COMPANY.md` — most fields you write here flow directly into identity content the agents will read on every wakeup
- Be specific rather than aspirational — concrete constraints produce better bundles than vague hopes
- The tool does NOT validate your business idea or strategy; it configures agent infrastructure to execute whatever idea you provide
- Some sections enforce rules from Paperclip best-practice docs (the goal-as-outcome test, the "we are not" anti-drift requirement, span-of-control limits). Pay attention to the notes under each section.

---

## 1. Company name and slug

**Name:** [Display name, e.g., "Newsletter Press" or "Niche Site Empire"]

**Slug:** [Lowercase hyphenated, e.g., newsletter-press. This becomes the bundle directory name and the company ID in Paperclip.]

**One-sentence description:** [The pitch in 20 words or fewer. Used in `COMPANY.md` description, README, and as the company's identifying line in Paperclip's UI.]

**Examples:**

- "Operating company for a single paid newsletter — launch, grow, and monetize on Substack, beehiiv, or ConvertKit with a fixed cadence and the founder's voice as the moat."
- "Operator-led portfolio of programmatic SEO and affiliate content sites — kill ruthlessly, scale winners."
- "Solo developer's product company — three agents handling planning, engineering, and review for a single SaaS codebase."

---

## 2. North star

A single measurable target. This is the company's reason for existing and the metric every delegation is graded against.

**The goal-as-outcome rule:** the north star must describe a sustained state of affairs or a measurable threshold reached on a defined timeline — not a one-off deliverable. If your candidate north star can be "done" by completing one task in one session, push it up a level until you reach something the CEO can keep working toward week over week.

**Bad (task-shaped):** "Launch a landing page for the product."

**Good (outcome-shaped):** "10,000 subscribers and $5,000 MRR — from paid tier or sponsorships, combined — within 90 days of import."

**Good:** "Portfolio earning $20K/month across 5+ sites within 90 days."

**Good:** "Two qualified design-partner contracts signed within 60 days, each with a written commitment to integrate within 90 days."

**Your north star:**

[Replace with one measurable, time-bound, persistent-outcome statement.]

---

## 3. Goals

Two to five additional measurable outcomes that ladder up to the north star. These become the `goals:` list in `COMPANY.md`'s frontmatter and appear in the README.

Apply the same goal-as-outcome rule. Goals are persistent — once completed, the CEO still has meaningful work under each one.

**Examples (newsletter):**

- "Free-to-paid conversion above 2.5%; Day-90 paid retention above 80%"
- "Weekly send shipped on cadence with the founder as the only author"

**Examples (portfolio):**

- "8 active sites with 5 clearing $4K/month each within 12 months"
- "Two sites qualified for premium ad networks (Mediavine or AdThrive) within 12 months"

**Your goals:**

1. [Goal 1]
2. [Goal 2]
3. [Goal 3 — optional]
4. [Goal 4 — optional]
5. [Goal 5 — optional]

---

## 4. We are

Positive identity statements. What kind of company is this, plainly stated, with the load-bearing distinctions baked in. The agents read this on every wakeup; it shapes every decision they make.

The structure that works (from the reference examples): start with a noun phrase ("We are a paid newsletter publisher."), then unpack what that means in plain operational terms.

**Examples (newsletter):**

> "We are a paid newsletter publisher. One author. One voice. One send cadence. We grow a list, convert a slice of free subscribers into paying ones, and sell sponsorships against the free side of the list. Subscribers, open rate, click-through, paid conversion, and churn are the only numbers that matter on a given day."

**Examples (portfolio):**

> "We are a portfolio operator. We run 5+ niche sites concurrently, each targeting clusters of low-competition, high-intent search queries with programmatic SEO and human-edited content. We are E-E-A-T-conscious, schema-disciplined, and Core Web Vitals-tuned because Google rewards those signals with crawl budget and rankings."

**Your "we are" paragraph:**

[Write 2-5 sentences. Start with the noun phrase. Make the load-bearing operational distinctions explicit.]

---

## 5. We are NOT

**This section is required.** At minimum two negations.

This is the anti-drift core of the configuration. Agents will encounter many adjacent ideas during operation — "what if we also did X?" Most of those ideas should be killed at the moment they surface. This section is the kill list.

Each negation has the form: "We are NOT a [thing]. We do not [behavior]. We do not [behavior]." Then explain why this matters operationally.

**Examples (newsletter):**

- "We are NOT a multi-author publication. We do not commission outside writers, we do not run a content network, and we do not let a staff writer's byline replace the founder's voice. If a piece does not pass voice review, it does not ship under our masthead."
- "We are NOT a YouTube channel. We do not produce video as a primary format. We repurpose newsletter issues into LinkedIn and X posts because the inbox is the home base — every other surface is a feeder."
- "We are NOT a free-only newsletter. A paid tier is core to the model. Every editorial decision is graded on whether it moves free-to-paid conversion or paid-tier churn."

**Your "we are not" list:**

1. **We are NOT** [thing]. [Behavior 1]. [Behavior 2]. [Why it matters operationally.]
2. **We are NOT** [thing]. [Behavior 1]. [Behavior 2]. [Why it matters operationally.]
3. [Add more as needed — 2-5 entries is the typical range]

---

## 6. Constraints

Non-negotiable rules the company operates under. These are not soft preferences. Agents read them on every wakeup, the CEO references them when approving work, and they become the "anti-drift checks" in OPERATIONS.md.

Format: one sentence per constraint, in present tense, no hedging.

**Examples (newsletter):**

- "One author. The founder's voice is the moat. No ghostwriting under the founder's byline."
- "Fixed send cadence. The newsletter goes out on the same day, at the same hour, every week. Cadence is the operating heartbeat."
- "Paid tier is not optional. Every free issue points at the paid tier; every welcome sequence sells it."

**Examples (portfolio):**

- "80/20 site economics — kill ruthlessly, scale winners. Any site under $200/month after 9 months goes on the sunset list."
- "E-E-A-T is non-negotiable. Every article has a real author bio with verifiable credentials or experience claims."
- "No black-hat SEO. No PBNs, no link farms, no cloaking."

**Your constraints:**

1. [Constraint 1]
2. [Constraint 2]
3. [Constraint 3]
4. [Constraint 4 — optional]
5. [Constraint 5 — optional]

---

## 7. Use case pattern (optional)

Pick a canonical org structure from the Paperclip community docs to seed your company, or leave blank to let the tool design the org from scratch.

If you pick a pattern, the tool uses it as a starting template — suggested agent list, suggested skill list, suggested project list — and then customizes against your brief. You can still override anything.

**Available patterns:**

- `solo-dev-shop` — 3 agents (CEO → CTO → Engineer). For single-developer product work.
- `content-operations` — 4 agents (CEO → Strategist, Writer, Editor). For blog / newsletter / publication operations.
- `product-sprint` — 3 agents (CEO → CTO → QA). For two-week sprint delegation against an existing backlog.
- `open-source-maintenance` — for OSS project maintenance (issue triage, PR review, doc drift).
- `newsletter` — derived from the `newsletter-press` reference. ~14 agents covering editorial, growth, monetization, analytics.
- `niche-site` — derived from the `niche-site-empire` reference. ~16 agents covering content production, technical SEO, link acquisition, monetization.
- `agency` — derived from the `agency-engine` reference. ~19 agents covering creative, accounts, paid media, SEO, operations, finance. For client-services / retainer agencies.
- `membership` — derived from the `membership-stack` reference. ~15 agents covering content, community, retention, billing, growth. For membership / subscription businesses.
- `seo-bureau` — derived from the `seo-bureau` reference. ~15 agents covering technical SEO, content, link acquisition, reporting. For SEO-led service businesses.
- `custom` — no template; the org_planner designs from scratch.

**Your choice:** [pattern slug, or custom]

**These notes are binding.** The org planner treats what you write here as decisive. State an explicit roster (named agents) or a headcount cap and the tool produces exactly that org — it will not add roles or split one role into a sub-team. State which work runs on a **standing schedule** (a cadence like "Mon/Wed/Fri" or "monthly") and those tasks become **recurring** — each yields a routine in `.paperclip.yaml`, and one stated cadence maps to exactly one recurring task. Everything else is handoff- or heartbeat-driven, not a standing schedule.

**Notes if customizing the pattern:** [Free text — e.g., "Exactly four agents: CEO, signal-scanner, opportunity-strategist, senior-analyst; no sub-teams. Only two cadences are scheduled — a Mon/Wed/Fri signal scan and a monthly board package; everything else is handoff/heartbeat-driven."]

---

## 8. Governance spectrum position

Where on the autonomy ↔ approval spectrum do you want this company to sit? This calibrates the `Decision rights` and `Escalation` sections of every agent's AGENTS.md, the `Approval and merge rules` in OPERATIONS.md, and the per-agent budget caps.

(From [Paperclip's governance-spectrum guide](https://paperclip.community/guides/concepts/governance-spectrum). The five-pattern approvals guide is in [/operations/approval-patterns](https://paperclip.community/guides/operations/approval-patterns).)

**Pick one:**

- `tight` — board approves: strategy, all hires, every external communication, all budget. Agents wait for human review on most work. Suitable for companies where mistakes are costly (regulated industries, customer-facing finance, high-stakes content) or first-week new operators learning the platform.
- `balanced` — board approves: strategy, hires, budget overrides, custom escalations the agent surfaces. Routine task completion runs autonomously. Suitable for most companies after the first 2-4 weeks.
- `loose` — board approves: strategy + hires only. Agents have wide latitude on budget and execution. Suitable for operators who have run the company for a quarter+ and trust the agents.

**Your choice:** [tight | balanced | loose]

**Notes:** [Free text — e.g., "balanced overall but I want tight approval on anything customer-facing for the first 30 days"]

---

## 9. Operator working pattern

How much time you put in and how much money you can spend. Used to size the agent team and the approval workflow density.

- **Hours per week (operator review time):** [e.g., 4]
- **Capital cap (EUR/month, for AI infrastructure spend — Anthropic, OpenRouter, Manifest, VPS):** [e.g., 200]
- **Capital cap (EUR, one-time setup):** [e.g., 500]
- **Single-week cap (optional):** [e.g., 8 — weeks requiring >8h of review are structurally incompatible with the bet]
- **Working pattern (optional):** [e.g., "evenings only, weekends preferred"]

The tool uses these to set:

- Default per-agent monthly budgets (sum should fit within capital cap)
- Default approval-queue cadence (more agents = more queue items = more review time)
- Whether to recommend Hermes Agent's smart-mode approvals (effectively required when operator hours/week < total team size × 0.5)

---

## 10. Adapter preferences (optional)

The Paperclip docs recommend [matching the adapter to the role](https://paperclip.community/guides/adapters/mixed-adapter-teams) rather than running every agent on a default. If you have preferences, capture them here. Otherwise the tool picks defaults based on role.

**Default mapping (when this section is empty):**

- CEO and senior managers → `claudelocal` with Claude Opus 4.7
- Mid-level managers → `claudelocal` with Claude Sonnet 4.6
- Engineers / code-heavy roles → `codexlocal`
- Persistent-memory roles (e.g., research analyst, churn analyst) → `hermeslocal`
- Generic workers running at scale → `opencodelocal` routed through [Manifest](https://paperclip.community/guides/adapters/manifest-auto-routing) for cost-aware tier picking

**Your overrides:**

- [Role/slug → adapter — e.g., "CEO → claudelocal opus" or "All engineers → codexlocal"]
- [Free text — e.g., "I have a Z.AI Coding Plan, route opencode workers there"]

---

## 11. Operating canon

The rules your agents should actually follow — the procedures, rubrics, standards and domain decision rules that no other section captures.

**This section is encoded, not summarised.** What you write here is threaded verbatim into the generated skills, agent mandates, tasks and projects, with an instruction to turn it into procedure. A rubric written here should come back as scoring steps; a threshold table should come back with its actual thresholds. That is the point of the section — but it cuts both ways: an offhand aside written here will also come back as procedure. If it isn't something you want an agent following, it doesn't belong in this section.

**What belongs here:**

- Procedures and standards — how a piece of work is done, and what "done" means
- Rubrics and scoring schemes — the dimensions, and how they are weighted
- Thresholds and classifications — the bands, labels and cut-offs, with their values
- Domain decision rules — what to do when a specific condition holds

**What belongs elsewhere:**

- Org shape — headcount, roster, who reports to whom → **section 7**
- Identity, positioning, what you are and are not → **sections 4–6**
- Hard limits the whole company operates under → **section 6 constraints**

**Mark it up. This is the expected form, not a style preference.**

Write each rule as a **bold-headed block**: a short bold name, then the prose. Where a rule has named parts, **enumerate them and italicise each name**:

```
**<Short name for the rule.>** <The prose that states it — thresholds, bands,
ordering, whatever the rule actually says.>

**<Short name for a rule with named parts.>** <Lead-in sentence.>
(1) *<Name of the first part>* — <what it means>.
(2) *<Name of the second part>* — <what it means>.
(3) *<Name of the third part>* — <what it means>.
```

Those placeholders are a shape, not a recommendation — the rules, parts and values must be yours.

**Why the markup matters.** After generation the tool checks that each rule and each named part actually reached the bundle, and it finds them **by that markup**: bold block heads and enumerated italic names. Prose canon that isn't marked this way still gets threaded to the generators, but it **cannot be checked**, so a rule that silently fails to land will not be reported. If nothing in this section is marked up, the run says so rather than staying quiet — but a mix of marked and unmarked rules will only ever report on the marked ones.

Four details that matter to the check:

- **Name the rule in its heading; don't describe it.** A heading that is a *name* — `**The provenance citation format.**` — can be looked for in the bundle. A heading that is a *sentence* — `**The daily recap does two jobs.**` — cannot: no generated file ever restates a sentence, so that item is reported as **coverage unknown** rather than pretended about. Both are threaded to the generators either way; only the named one can be verified.
- **Enumerate the parts wherever a rule has them.** A rule with named parts is checked part by part, which is precise. A rule with no enumerated parts is checked only by its heading — a weaker signal, since a rule can be encoded faithfully without any file repeating the phrase that names it.
- **Sentence case for part names** — `*Handover completeness*`, not `*Handover Completeness*`. Either reads fine; only one is consistent, and consistency is what makes a missing part recognisable.
- **Italic is only a signal when enumerated.** `*Some Registry*` mid-paragraph is read as a proper noun and ignored, which is what you want — it means you can italicise source names and ordinary emphasis freely without polluting the check.

**Other context:**

[Free text — leave blank if you don't have anything to add.]

---

## 12. Run-policy overrides (optional)

By default the tool sets each agent's per-run turn cap and concurrent-run limit by role. If you want a specific agent bounded differently — or run only on demand, never on a heartbeat — state it here. An agent wake with no bound on turns or concurrency can loop and burn budget before anything stops it; these overrides let you cap that. **Leave this blank to keep the defaults — an empty section changes nothing.**

One override per line, naming the agent and any of the three values (combine on one line, comma-separated):

- `<agent>: max turns <N>` — cap turns per wake (guards against a run that loops)
- `<agent>: max concurrent <N>` — cap simultaneous runs of that agent
- `<agent>: heartbeat off` — do not wake this agent on a heartbeat (`on`/`off`)

Name the agent by role, title, or slug — the same way as adapter preferences. A name that matches no agent is skipped with a warning; a bad value (e.g. `max turns 0`) is rejected before generation.

**Your overrides:**

- [e.g., "research-analyst: max turns 8, heartbeat off"]
- [e.g., "CEO: max concurrent 1"]

---

## Validation checklist

Before passing this to the tool, verify:

- [ ] Company name and slug are set (slug is lowercase-hyphenated)
- [ ] One-sentence description is ≤ 30 words
- [ ] North star is a persistent outcome with a measurable target and timeline (passes the "can this be done in one session?" test — answer must be no)
- [ ] At least 2 goals, all persistent outcomes
- [ ] "We are" paragraph is 2-5 sentences and includes the operational distinctions
- [ ] "We are NOT" list has at least 2 entries
- [ ] At least 2 constraints (real non-negotiable rules, not soft preferences)
- [ ] Use case pattern picked (or explicit `custom`)
- [ ] Governance position picked
- [ ] Hours/week and capital caps filled in
- [ ] No `[bracketed placeholders]` remain

The `blueprints validate --input <this-file>.md` command runs this checklist for you without making any Anthropic API calls.

---

## What happens next

Once filled out, run:

```bash
# Single-agent slice (v0.1a)
blueprints generate --input <this-file>.md --output <output-dir>/ --single-agent

# Full bundle (v0.1b)
blueprints generate --input <this-file>.md --output <output-dir>/
```

The tool will produce a directory matching Paperclip's bundle structure:

- `.paperclip.yaml` — runtime config (sidebar, agents map, projects map)
- `COMPANY.md` — your identity content (Identity, We are, We are not, Constraints, Goals, North star)
- `README.md` — auto-generated overview with mermaid org chart
- `OPERATIONS.md` — phase model, idle-state protocol, approval rules, anti-drift checks (v0.1b only)
- `PROJECT-INVENTORY.md` — starter projects and deliverables tracker (v0.1b only)
- `agents/<slug>/` per agent — AGENTS.md, SOUL.md, HEARTBEAT.md, TOOLS.md
- `projects/<slug>/PROJECT.md` per starter project (v0.1b only)
- `tasks/<slug>/TASK.md` per starter task (v0.1b only)
- `skills/<slug>/SKILL.md` per shared skill
- `LICENSE.txt`

Total generation time: 1-3 minutes for v0.1a, 5-10 minutes for a full v0.1b bundle (parallelized across agents and skills).

The generated bundle imports via Paperclip's import UI.
