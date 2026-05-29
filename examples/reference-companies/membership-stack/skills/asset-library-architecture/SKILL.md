---
schema: agentcompanies/v1
slug: asset-library-architecture
name: asset-library-architecture
description: 'How Membership Stack structures, tags, versions, and deprecates assets in the library so it compounds in value — driving asset library growth that lifts every member''s LTV instead of collapsing into a 200-asset dump folder.'
---

# asset-library-architecture

*The library is the product. We treat it like a product — taxonomied, tagged, versioned, never silently deleted.*

## When to load this skill

- A new template, tool, guide, or video is moving toward release and needs a home in the tree.
- A returning asset needs a version bump because its inputs or outputs are changing.
- The Product Manager is proposing a new tag for the approved vocabulary.
- An asset is being retired and needs to move to `library/_deprecated/`.
- A search-for-an-asset support ticket reveals members can't find something that exists — a taxonomy or tagging gap.

## Inputs

- The asset slug, category (template / tool / guide / video), and proposed sub-category.
- The asset's release notes (what is new or what changed from the previous version).
- The approved tag vocabulary from `library/_meta/tag-vocabulary.md`.
- For a deprecation: the replacement asset slug (if any) and the redirect note copy.

## Procedure

1. **Place the asset.** Every asset lives at exactly one path:

   ```
   library/
     templates/<category>/<asset-slug>/
     tools/<category>/<tool-slug>/
     guides/<category>/<guide-slug>/
     videos/<category>/<video-slug>/
   ```

2. **Write the INDEX.md.** Title, category, tags (from the approved vocabulary only), version (`vMAJOR.MINOR`), release date, owner agent, summary, "who this is for", and "what you do with it". No INDEX.md, no release.
3. **Add release-notes.md.** What changed between this version and the previous one. New assets get a v1.0 entry that names the job-to-be-done.
4. **Apply tags from the approved vocabulary.** Flat tags, no hierarchies, no capitals, no spaces, no duplicates of the category. New tags require Product Manager proposal + CEO approval before they enter the vocabulary.
5. **Version on every change.** Bump MAJOR when the asset's contract changes (different inputs or different outputs). Bump MINOR for clarity edits or fixes. Never edit a published asset in place without bumping at least MINOR — members rely on stability and bookmarks.
6. **Deprecate, do not delete.** Move retired assets to `library/_deprecated/<asset-slug>/` and leave a redirect note in the original `INDEX.md` pointing to the replacement (if any). Members may have bookmarked or shared the original URL.

## Outputs

- `library/<type>/<category>/<asset-slug>/INDEX.md` — fully populated against the schema above.
- `library/<type>/<category>/<asset-slug>/release-notes.md` — version history.
- A delta line for the Retention Analyst's weekly cohort report under "library count" so asset library growth is visible against the 50-assets-in-90-days goal.
- A community announcement entry for the Community Manager (handled by the content-release-calendar handoff).

## Anti-patterns

- Dropping an asset into the root of `library/` or into a category that doesn't match the four-type taxonomy.
- Inventing a new tag inline because the right one "isn't quite there" — propose it through the Product Manager instead.
- Editing a published asset in place without a version bump — silent edits break members who relied on the previous behavior.
- Hard-deleting a deprecated asset — bookmarks and shared links become 404s and erode trust.
- Letting "the back catalogue" rot because every release agent is focused on the most recent shipment — month-twelve conversion depends on a navigable archive, not the newest drop.
- Treating community threads or marketing copy as library assets — they belong elsewhere; the library is templates, tools, guides, and videos only.

## Reference

Pair this skill with:
- `template-design-standards` for what a template-type asset must contain.
- `tool-build-process` for what a tool-type asset must contain.
- `content-release-calendar` for the weekly slot that lands each new asset.
