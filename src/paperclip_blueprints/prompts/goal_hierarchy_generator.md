You assign ownership for a Paperclip company's goals. The company's single north star is
the root goal; each goal below reports up to it. Your job is to decide, for EACH goal, the
one agent accountable for that outcome and the level at which it sits.

## The north star (the root goal — already owned by the org root)

{{ north_star }}

## The goals to assign (in order)

{% for g in goals %}
{{ loop.index }}. {{ g }}
{% endfor %}

## The agents (owner candidates) and their mandates

{% for a in agents %}
- `{{ a.slug }}` — {{ a.title }}: {{ a.mandate }}
{% endfor %}

## How to decide

For each goal, pick the ONE agent whose mandate makes it accountable for that outcome, and
set the level:

- **`level: "agent"`** — a single agent owns the outcome. Set `owner` to that agent's slug.
- **`level: "team"`** — a manager owns the outcome on behalf of the agents reporting to it.
  Set `owner` to the manager's slug.
- **`level: "company"`** — the goal is genuinely cross-cutting with NO single accountable
  agent (or the company is too small for role separation). Set `owner` to `"company"`.

Rules:

- Nest with reasoned ownership. Default to `"company"` ONLY when no single agent owns the
  outcome — do NOT push everything to company level, and do NOT invent an owner where the
  mandates do not support one.
- `owner` MUST be one of the agent slugs listed above, or the literal `"company"`.
- Return EXACTLY one assignment per goal, in the SAME ORDER as the goals above.

## Output format

Return ONE fenced ```json block and nothing else:

```json
{
  "assignments": [
    {"owner": "<agent-slug or 'company'>", "level": "agent | team | company"}
  ]
}
```
