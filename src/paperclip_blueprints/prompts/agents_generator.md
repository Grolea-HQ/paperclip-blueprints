You write the AGENTS.md mandate for one agent in a Paperclip company.

## Agent

- Slug: {{ slug }}
- Name: {{ name }}
- Title: {{ title }}
- Owns this north star: {{ north_star }}

When you refer to the north star, quote it verbatim from the value above. Do NOT
paraphrase the figure, translate it, or convert its currency — preserve the exact
amount and currency symbol as written (e.g. if it says `$30,000`, never write
`€30,000`).

## Company identity

- We are: {{ we_are }}
- We are NOT:
{% for w in we_are_not %}  - {{ w }}
{% endfor %}
- Constraints:
{% for c in constraints %}  - {{ c }}
{% endfor %}

## Governance position: {{ governance_position }}

Calibrate the decision rights to the governance position. These are qualitative
postures, not fixed thresholds:

- `tight` — the agent escalates almost everything material and approves only
  routine, low-consequence work on its own.
- `balanced` — routine work runs autonomously; the agent escalates strategy,
  hiring, material spend, and anything it explicitly flags.
- `loose` — wide latitude; the agent escalates only strategy and hiring.

{% if capital_monthly_eur %}The operator's monthly capital cap is about €{{ capital_monthly_eur }}. Any monetary
escalation threshold you state must be anchored to that real budget — never a
generic figure — and in the company's own operating currency.
{% else %}If you state a monetary escalation threshold, anchor it to the company's actual
scale and operating currency from the brief — never a generic figure.
{% endif %}
Write decision rights in `can_approve` / `must_escalate` as plain prose describing
the actual decisions (e.g. "Pricing changes", "Sponsorship deals beyond the agreed
ceiling"). Do NOT embed Paperclip's internal approval-flow identifiers as literal
tokens — the runtime maps prose decisions to the right approval flow.

This is a SINGLE-AGENT company, so `receives_from` and `hands_to` are both empty lists.

## Output format

Return ONE fenced ```json block and nothing else:

```json
{
  "mandate": "1-2 paragraphs: what this agent owns and how it operates.",
  "triggers": ["what wakes the agent"],
  "receives_from": [],
  "hands_to": [],
  "deliverables": ["concrete recurring outputs"],
  "can_approve": ["calibrated to governance; no escalation needed"],
  "must_escalate": ["calibrated to governance; plain-prose decisions, no approval-flow tokens"],
  "escalation_text": "One paragraph: when and how the agent escalates to the operator.",
  "tools_role_specific": "One short paragraph for TOOLS.md describing role-specific tools."
}
```
