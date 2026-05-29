# ADR-003 — Input Template Format

**Status:** Accepted
**Date:** Pre-v0.1, during the rework
**Relates to:** ADR-002 (output bundle format), ADR-004 (prompt architecture)

---

## Context

The original input template (`examples/input-template.md`) was bet-validation flavored: it asked the operator for `mission`, `revenue_target_eur`, `revenue_target_months`, `capital_available_eur`, `hours_per_week`, `hard_constraints`, `soft_preferences`, operator's `skills/network/assets`, `hard_nos`, `build_in_public`, operating preferences, and a free-text "anything else."

This framing came from a personal-bet-evaluation framework — useful for deciding whether a business idea is worth pursuing, but not the right shape for generating an operational Paperclip company.

When the two reference example companies (`newsletter-press`, `niche-site-empire`) were inspected, the actual `COMPANY.md` files had a fundamentally different structure: name + description + goals + "Identity / We are / We are not / North star / Constraints" body. The input template's domain didn't match the output's domain.

Two options were on the table:

- **Option a:** Reframe the input template to mirror COMPANY.md's structure directly. The operator writes "we are / we are not / north star / constraints" in the input; the tool translates that into the output bundle.
- **Option b:** Keep the bet-validation framing as a "raw brief" and treat the tool's first job as translating raw brief → COMPANY.md identity. Higher cognitive load on the LLM; possibly higher quality if the LLM can do the translation well.

## Decision

**Option a is adopted.** The new input template mirrors COMPANY.md's structure, with operator-friendly inline guidance.

The input template's sections are:

1. **Company name and slug** (display name, hyphenated slug, one-sentence description)
2. **North star** (single measurable persistent outcome; explicit goal-as-outcome rule with examples)
3. **Goals** (2-5 additional measurable outcomes)
4. **We are** (positive identity paragraph)
5. **We are NOT** (anti-drift negations, ≥2 required)
6. **Constraints** (non-negotiable rules, ≥2)
7. **Use case pattern** (optional canonical org template choice: solo-dev-shop / content-operations / product-sprint / oss-maintenance / newsletter / niche-site / custom)
8. **Governance spectrum position** (`tight` / `balanced` / `loose`)
9. **Operator working pattern** (hours/week, capital caps, working pattern)
10. **Adapter preferences** (optional per-role overrides; defaults documented)
11. **Anything else** (free text)

Plus a validation checklist that the `blueprints validate` CLI subcommand runs without making any Anthropic API calls.

## Rationale

Three reasons option a beats option b:

1. **Structural fidelity is enforceable.** When the operator writes "we are not" content directly, the tool can validate it (e.g., "you wrote 1 negation; the rule requires 2+"). With option b, the validation moves to "did the LLM's translation produce 2 negations?" — testable, but failure-prone and harder to debug.

2. **The operator has the domain knowledge, not the LLM.** "We are not a YouTube channel" is something the operator knows about their company; it's not something the LLM can reliably infer from a bet-validation brief. Asking the operator to write it directly is the right division of labor.

3. **The bet-validation framing wasn't producing value.** Even in option b, the LLM would have had to ignore fields like `revenue_target_eur` (which doesn't influence the operational config) and synthesize the identity content from scratch. The translation step would have been thin.

The operator-fillable bet-validation framing is preserved at a different layer: the constraints, north star, and "anything else" sections capture revenue targets and operating preferences naturally. The tool doesn't need a separate `revenue_target` field — if revenue matters, it's in the north star.

## Consequences

**Positive:**

- The input template is now a thin layer over COMPANY.md. The translation work is mechanical (frontmatter rendering, slugification, formatting), not synthesis.
- Validation is fast (`blueprints validate --input ...` runs without API calls) and catches structural mistakes before any LLM cost is incurred.
- The operator learns the COMPANY.md vocabulary by filling in the template — useful when they later edit COMPANY.md directly or onboard a new company.
- Goal-as-outcome and "we are not" rules are enforced at input time, not deferred to prompt synthesis.

**Negative:**

- Operators new to Paperclip have to learn the "we are / we are not" framing before they can fill in the template. The template's inline examples and validation checklist mitigate this.
- The bet-validation use case (using the template as a "should I do this?" tool) is gone. Operators who want that workflow keep using their existing bet-evaluation framework (which lives outside this project).
- Migration cost: any old bet-validation briefs the operator wrote will need to be re-shaped to fit the new template. This is acceptable because there are no old briefs from this project; only the operator's external production-company experience, which is already in the right shape.

**Risks accepted:**

- The use-case-pattern field is optional and may go unused. If most operators always pick `custom`, the canonical patterns might be over-investment. We accept this; the patterns are cheap to maintain and provide useful starting points for first-time operators.

## Alternatives considered

1. **Option b (raw brief → LLM translation).** Discussed above. Rejected for structural-fidelity and division-of-labor reasons.
2. **Two-layer template: bet-evaluation outer, COMPANY.md inner.** Rejected as YAGNI; the operator can use any bet-evaluation framework externally and then fill in this template once they've decided to build.
3. **YAML-only input instead of Markdown.** Rejected because Markdown is human-friendlier and the rendered template feels approachable. YAML is machine-friendlier but the operator-side ergonomics matter more here.
