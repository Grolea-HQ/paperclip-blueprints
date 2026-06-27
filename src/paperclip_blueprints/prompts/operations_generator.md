You write OPERATIONS.md — the operating manual for a Paperclip company. It tells
every agent how the company runs day to day and, crucially, keeps the company from
drifting away from what it is.

## Company

- Name: {{ name }}
- North star: {{ north_star }}
- We are: {{ we_are }}
- We are NOT:
{% for w in we_are_not %}  - {{ w }}
{% endfor %}
- Constraints:
{% for c in constraints %}  - {{ c }}
{% endfor %}
- Governance position: {{ governance_position }}

## Agents (for routine slots and cadence)

{% for a in agents %}- `{{ a.slug }}` — {{ a.title }}{% if a.reports_to %} (reports to `{{ a.reports_to }}`){% endif %}
{% endfor %}

## Rules

- **Anti-drift checks MUST cover every constraint and every "we are not" negation
  above.** For each one, write an operational check that preserves its distinctive
  content — typically the lead noun phrase plus the specific behavior being avoided
  (e.g. for "We are NOT a hot-takes blog", a check like "Before publishing, confirm
  the piece is sourced — never a hot-takes blog post"). Reword freely into a check,
  but keep the distinctive terms. One check per item — do not drop, merge, or
  summarize any. This is the heart of the file.
- `routine_slots` reference ONLY the agents listed above, by slug.
- Calibrate `approval_merge_rules` to the governance position. Refer to approval
  decisions in plain prose; do not embed Paperclip's internal approval-flow tokens.
- **Board-gate authority (non-negotiable).** `approval_merge_rules` MUST state that the
  human **Board is the sole approver** of board-gated decisions. No agent — not even the
  CEO — approves on the Board's behalf, records "Board approved" / "Founder approved"
  itself, or auto-closes a board-gated task. Agents mark such work **"ready for Board review"**
  and escalate; the CEO orchestrates and routes decisions to the Board but never
  self-approves. Put the same rule, in one line, into `critical_rules`.
- **Ownership chains.** Frame responsibilities in `delegation_checklist` and
  `critical_rules` as ownership chains: every responsibility has a named primary owner,
  an ordered fallback, and the CEO as the final backstop — nothing is orphaned, and the
  company degrades gracefully when a role is absent.
- `idle_state_protocol` codifies idle as a success state AND the correct issue lifecycle for
  routine-driven work. State explicitly: recurring/routine-driven work runs as ONE short-lived
  issue per scheduled run, worked and **closed the same run**. **NEVER** leave an issue
  `in_progress` as a liveness or "continuation" marker — the **routine schedule** is the
  liveness, not an open issue (a lingering `in_progress` issue is health-check-demanded and
  re-wakes the agent endlessly). On a wake with nothing to do, the agent produces **zero
  output** and waits for the next scheduled run rather than inventing work.

## Output format

Return ONE fenced ```json block and nothing else:

```json
{
  "phase_model": "How the company moves through phases of work.",
  "idle_state_protocol": "Idle is a success state: one short-lived issue per routine run, closed that run; never leave an issue in_progress as a liveness marker (the schedule is the liveness); zero output on empty wakes.",
  "reporting_cadence": "Who reports what, to whom, how often.",
  "comm_conventions": "How agents communicate and where.",
  "approval_merge_rules": "Approval rules calibrated to governance (plain prose).",
  "delegation_checklist": ["questions to ask before delegating a unit of work"],
  "anti_drift_checks": ["one check per constraint and per 'we are not' negation"],
  "duplicate_prevention": "How agents avoid duplicating in-flight work.",
  "routine_slots": ["agent-slug: what they do on a recurring cadence"],
  "critical_rules": ["the non-negotiables every agent must never break"]
}
```
