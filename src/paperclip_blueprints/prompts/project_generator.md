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

## Output format

Return ONE fenced ```json block and nothing else:

```json
{
  "summary": "One paragraph describing the project and its link to the north star.",
  "success_condition": "A persistent, checkable success condition (an outcome)."
}
```
