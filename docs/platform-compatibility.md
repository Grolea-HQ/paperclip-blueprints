# Platform compatibility

What generated bundles have been verified to do against a running Paperclip, when, and how far that
verification reaches. This is the single home for the dated claim — nothing else in this repository
restates it, because two copies of an expiring fact eventually disagree and the one that gets
updated is never the one being read.

The posture behind this file — how a revision is detected, what is claimed, what expires — is
[ADR-042](adr/042-platform-revision-posture-and-bundle-facing-honesty.md).

---

## Verified

**2026-08-18, against Paperclip schemaVersion 7.**

An example generated bundle of 13 agents imported **successfully, with a warning**.

The warning: bundles produced by this tool declare no schema revision, so the importer reads them as
revision 5 and reports that they predate nine task-data capabilities — label, blocker, document,
work product, monitor, attachment, embedded image, task timestamp, and parent link transfer.

**Nothing is lost.** Those capabilities import only if the bundle carries the corresponding data,
and generated bundles carry none of it. The warning describes data that is not there rather than
data that failed to arrive. This tool therefore emits no schema-revision key; see ADR-042 for why
that is a decision rather than an omission.

## How far this reaches

**It expires.** The claim is against one platform revision on one date. A later revision may change
what imports, and this file does not update itself. If the platform has moved since the date above,
the claim above is history, not a guarantee.

**Live import is the only oracle.** This project validates bundles against the schemas it targets,
but a schema check cannot detect that the platform's own data model has moved underneath it. Every
revision this project has noticed was noticed by importing.

**The version qualification is coarse.** This is a pre-release project: the version is written by
hand in the package metadata, there are no release tags, and it moves only when someone remembers to
move it. So the stamp in a bundle's `README.md` identifies a range of builds, not a build.

The claim covers bundles generated at **v0.1.0a1 or later**. Earlier stamps are pre-release and
unqualified — a bundle stamped with an earlier version may predate this verification by any amount.

If you need to know precisely what a bundle was generated against, regenerate it. For a pre-release
tool that costs a few dollars of model spend, which is a better answer than a stamp implying a
precision it does not have.

**Why the claim covers a later version than it was tested on.** The import above was performed on
bundles generated at v0.1.0a0, one version below the range the claim covers. The evidence transfers
because the intervening change touched only this bundle's `README.md`, the render call that fills
it, a named constant, and documentation — and the importer does not read any of them. Everything the
importer *does* read is byte-identical across the bump, which the test suite asserts file by file
against a snapshot captured before the change. So the verified artifact and the claimed artifact
differ only in a file that plays no part in import.

## What would change this file

- A platform revision that changes what imports, observed by importing.
- A generated bundle that begins to carry one of the capabilities named above, which would make the
  declared-revision question load-bearing rather than cosmetic (ADR-042).
- A release process with tags, after which this file can be keyed per release rather than per range.
