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
