# ADR-041: Locate brief sections by byte span, and expose parsed values through an inspect document

## Status

Accepted

## Date

2026-08-12

## Context

A programmatic consumer needed two things it could not re-derive safely. Section boundaries
existed only inside the scan, which computed heading offsets and discarded them; re-deriving
them with a second regex would be a second definition of where a section starts, free to drift
from the parser's. Parsed values were reachable in-process as a `CompanyBrief` and not at all
across a process boundary, leaving scraping or a reimplemented parser.

A precondition turned out not to hold: `Path.read_text` performs universal-newline translation,
so on a CRLF brief the string parsed was never the file. Offsets against it are shifted by one
byte per preceding line.

## Decision

**Section spans.** Each scanned section carries a half-open `[start, end)` range of **UTF-8
bytes** locating its body. `end` is derived as `start + len(body.encode("utf-8"))`, so slicing
the source over the span reproduces the reported body by construction. Spans cover the body
only, never the heading, and no value carries a span in any form.

**Faithful reading.** Every brief-reading path reads without newline translation, through one
reader. This is a defect fix reached through the feature: byte offsets are meaningless against a
string that is not the file.

**The inspect document.** A new `inspect` command emits a versioned document that embeds the
validate document verbatim rather than restating validity. Sections appear whatever the outcome;
values only when parsing succeeded. Values reach the wire through an explicit projection, one
entry per field.

## Consequences

- A consumer reads the file as bytes, slices the half-open range and decodes — the same three
  steps in any language.
- Byte offsets fail loudly when a consumer forgets to convert: slicing a string with one breaks
  on the first em dash, which briefs carry in quantity. Code-point offsets would have worked in a
  UTF-16 language until an astral character appeared.
- Replacing a body span cannot change which section it is. Locating or replacing a heading is
  not offered, because that would let a consumer undo the structural identity check.
- A CRLF brief now parses as what it is. Values are unchanged — every value path splits lines,
  discarding terminators, and rejoins with a newline — and a generated bundle is byte-identical,
  both asserted rather than assumed. Only section bodies differ.
- The same split-and-rejoin that keeps a carriage return out of every value is why a multi-line
  value is not a slice of a CRLF source, and therefore why values carry no spans.
- One definition of a failure: a change to the validate document appears in the inspect document
  automatically. The two versions are independent, so a new brief field bumps only the latter.
- A new field on the brief model fails the suite until it is deliberately projected or excluded.
- Value spans remain unavailable until the anchored-block reader's line-ending rejoin is fixed;
  that work owns it.

## Alternatives considered

- **Code-point or UTF-16 offsets:** rejected — correct in one language, silently wrong across the
  boundary, and no repository fixture would have exposed it.
- **Line and column:** rejected — the standard library treats U+2028, U+000B, U+000C and U+0085 as
  line breaks where a consumer splitting on carriage-return/newline does not, so the two sides do
  not agree on what a line is.
- **Value spans without a reproduction guarantee:** rejected — a weak variant beside a strong one
  is eventually used as the strong one, and it fails on the inputs least likely to be tested.
- **Faithful reading for the new command only:** rejected — two commands would parse different
  strings for one file.
- **Keeping newline translation and documenting the offsets against it:** rejected — the
  reproduction test would pass because we test our string while a consumer slices their file.
- **A flag on `validate` instead of a command:** rejected — one command emitting two document
  shapes forces a consumer to branch on which it received.
- **`model_dump` for the values:** rejected — every model edit becomes a wire change by default,
  while the version number reads the same.

## References

- `specs/021-section-spans-and-inspect/` — spec and contracts
- ADR-040 — the declared section schema these spans locate, and the documents this one joins
- `tests/fixtures/brief_crlf_astral.md` — the fixture that varies the two axes the repository's
  briefs hold constant
