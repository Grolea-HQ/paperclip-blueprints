You write a SKILL.md — a reusable, loadable capability document for a Paperclip agent.

## Skill to write

- Slug: {{ slug }}
- Used by: {{ used_by }}

## Company identity

- We are: {{ we_are }}
- North star: {{ north_star }}
- Constraints:
{% for c in constraints %}  - {{ c }}
{% endfor %}

## Rules

- The skill must be concrete and operational for THIS company — a procedure an agent
  can actually follow, not generic advice.
- `when_to_load` lists the specific situations that should trigger loading the skill.
- `anti_patterns` lists the mistakes this skill exists to prevent, tied to the constraints.
- `name` should equal the slug.

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
  "slug": "{{ slug }}",
  "name": "{{ slug }}",
  "description": "One sentence: what this skill keeps true and why it matters.",
  "when_to_load": ["specific trigger situations"],
  "inputs": ["the files/data the skill reads"],
  "procedure": ["ordered, concrete steps"],
  "outputs": ["what the skill produces"],
  "anti_patterns": ["mistakes it prevents, tied to constraints"],
  "references": []
}
```
