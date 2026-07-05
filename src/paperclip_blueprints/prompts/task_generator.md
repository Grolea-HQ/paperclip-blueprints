You write a TASK.md — one concrete starter task in a Paperclip company.

## Task

- Slug: {{ slug }}
- Name: {{ name }}
- Part of project: {{ project }}
- Assigned to: {{ assignee }}
- Recurring (schedule-driven): {{ is_recurring }}

## The assignee's attached skills

These are the skills the assignee already has. A skill is the single source of truth for
*how* its work is done — its output format, its storage/naming protocol, its step-by-step
procedure, and its source scope.

{% if assignee_skills %}
{% for s in assignee_skills %}
- `{{ s }}`
{% endfor %}
{% else %}
- (none attached)
{% endif %}

## Company identity

- We are: {{ we_are }}
- North star: {{ north_star }}

## Rules

- The `objective` is one short paragraph: what the assignee must achieve and why, for
  THIS company.
- `completion_criteria` are concrete, checkable bullets — an unambiguous definition of
  done for this specific task (not generic advice).

### Defer to the governing skill (do NOT duplicate it)

If one of the assignee's attached skills governs this task's work, the task must be **thin
and deferential**. It states only:

1. the **trigger** (what this task responds to — for a recurring task, its schedule),
2. the **this-run scope** (what to cover on this particular run), and
3. a **reference to the governing skill** — name it explicitly, e.g. "perform <the work>
   per the `<skill-name>` skill; produce its prescribed output, format, and storage."

The task must **NOT** restate the skill's output format, its storage or file-naming
protocol, its step-by-step process, or its source scope. Those live in the skill and only
in the skill. At runtime the agent follows the task as its wake instruction with the skill
as supporting context, so if the task restates a looser version of the skill's how, the
task wins and the output drifts off-spec. Keep the *how* in the skill; the task carries
only *when* + *what-this-run* + *which skill*.

If NO attached skill governs the work, write the objective and criteria normally.

## Output format

Return ONE fenced ```json block and nothing else:

```json
{
  "objective": "One short paragraph: the trigger and this-run scope; if a skill governs the work, reference it and defer the how to it.",
  "completion_criteria": ["concrete, checkable definition-of-done bullets (deferential when a skill governs the how)"]
}
```
