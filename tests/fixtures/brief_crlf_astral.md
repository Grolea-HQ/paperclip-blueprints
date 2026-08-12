# Company Brief — Research Digest (example, multi-agent)

A filled, sanitized example brief for the v0.1b full-bundle flow. It names the
`content-operations` use-case pattern, so the tool seeds a small editorial org and
customizes it against this brief. Copy `examples/input-template.md` to start your
own. Run `blueprints validate --input <this-file>` to confirm it passes the offline
rules (no API calls), then `blueprints generate --input <this-file> --output <dir>`
for the full multi-agent bundle.

---

## 1. Company name and slug

**Name:** Research Digest

**Slug:** research-digest

**One-sentence description:** A weekly newsletter that turns peer-reviewed research into plain-language briefings for working professionals.

---

## 2. North star

**Your north star:**

10,000 engaged paid subscribers at a 40%+ weekly open rate, sustained for two consecutive quarters within 18 months.

---

## 3. Goals

**Your goals:**

1. The weekly issue ships every Tuesday on cadence, never slipping two weeks in a row
2. Free-to-paid conversion holds above 4% quarter over quarter
3. Every claim in a published issue traces to a cited primary source

---

## 4. We are

**Your "we are" paragraph:**

🛰 We are a single-cadence research newsletter. One issue a week, every claim sourced,
written for a smart non-specialist. We grow through referrals and accuracy, not
hot takes or volume. Open rate, conversion, and citation integrity are the numbers
that matter on a given day.

---

## 5. We are NOT

**Your "we are not" list:**

1. **We are NOT** a hot-takes blog. We do not chase the news cycle, we do not publish without a primary source, and we do not run unsourced opinion. Every issue is evidence-first, because trust is the entire product.
2. **We are NOT** a content farm. We do not pad the calendar with daily posts, we do not spin one study into five articles, and we do not trade depth for volume. One careful issue a week beats seven shallow ones.

---

## 6. Constraints

**Your constraints:**

1. One issue a week. Depth and accuracy beat frequency.
2. Every published claim cites a primary source. No exceptions.
3. Sponsorships are disclosed and never shape editorial conclusions.

---

## 7. Use case pattern (optional)

**Your choice:** content-operations

**Notes if customizing the pattern:** Editorial-led; the editor-in-chief owns accuracy and the growth side reports to the founder.

---

## 8. Governance spectrum position

**Your choice:** balanced

**Notes:** Tight approval on anything that touches a published claim or a sponsorship; routine drafting and scheduling run autonomously.

---

## 9. Operator working pattern

- **Hours per week (operator review time):** 8
- **Capital cap (EUR/month, for AI infrastructure spend — Anthropic, OpenRouter, Manifest, VPS):** 250
- **Capital cap (EUR, one-time setup):** 400
- **Single-week cap (optional):** 12
- **Working pattern (optional):** weekday mornings, async-friendly

---

## 10. Adapter preferences (optional)

**Your overrides:**

- CEO → claudelocal opus
- Editor-in-Chief → claudelocal opus

---

## 11. Operating canon

**Other context:**

**The claim-support rule.** Every claim inherits the tier of its weakest support, and that tier travels with the claim into the published issue.
(1) *Byline traceability* — whether a named person stands behind the claim.
(2) *Corroboration depth* — how many unrelated outlets carry it independently.
(3) *Correction history* — whether the outlet has amended this story before.

---

## 12. Run-policy overrides (optional)

By default the tool sets each agent's per-run turn cap and concurrent-run limit by role. **Leave this blank to keep the defaults — an empty section changes nothing**, which is what this example does.

**Your overrides:**

- [e.g., "editor: max turns 8, heartbeat off"]
