You write a TASK.md — one concrete starter task in a Paperclip company.

## Task

- Slug: {{ slug }}
- Name: {{ name }}
- Part of project: {{ project }}
- Assigned to: {{ assignee }}

## Company identity

- We are: {{ we_are }}
- North star: {{ north_star }}

## Rules

- The `objective` is one short paragraph: what the assignee must achieve and why,
  for THIS company.
- `completion_criteria` are concrete, checkable bullets — an unambiguous definition
  of done for this specific task (not generic advice).

## Output format

Return ONE fenced ```json block and nothing else:

```json
{
  "objective": "One short paragraph: what to achieve and why.",
  "completion_criteria": ["concrete, checkable definition-of-done bullets"]
}
```
