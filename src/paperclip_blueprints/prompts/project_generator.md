You write a PROJECT.md — the brief for one starter project in a Paperclip company.

## Project

- Slug: {{ slug }}
- Name: {{ name }}
- Owned by: {{ owner }}

## Company identity

- We are: {{ we_are }}
- North star: {{ north_star }}
- Constraints:
{% for c in constraints %}  - {{ c }}
{% endfor %}

## Rules

- The `summary` is one paragraph: what this project is and why it matters to the
  north star, for THIS company.
- The `success_condition` is a persistent, checkable condition that defines "done
  well" — not a one-off step. It should read like an outcome, not a task.

{% if operating_canon %}
## Operating canon (brief, section 11)

{{ operating_canon }}

**This is operating canon, not background.** It is the operator's stated way of working,
and section 11 is the only place it appears — nothing else in this brief carries it.

Encode it into what you write: its named dimensions, thresholds, classes, labels and rules
must show up as concrete steps, criteria or checks in your output, with their actual names
and values. Do NOT compress it into a summary sentence. Do NOT restate it as context and
then write something generic. If a slug or title you were given is named after part of this
canon, the canon is what that artifact must actually contain.

Where the canon conflicts with your own sense of best practice, the canon wins.
{% endif %}

## Output format

Return ONE fenced ```json block and nothing else:

```json
{
  "summary": "One paragraph describing the project and its link to the north star.",
  "success_condition": "A persistent, checkable success condition (an outcome)."
}
```
