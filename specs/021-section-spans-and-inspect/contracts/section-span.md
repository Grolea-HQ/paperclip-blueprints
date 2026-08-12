# Contract — the section span

Postconditions asserted by `tests/test_brief_sections.py` and `tests/test_reader_fidelity.py`.

## What a span is

**S1.1** A span is a pair of **UTF-8 byte offsets** into the source document.

**S1.2** The interval is **half-open**: `[start, end)`. `start` is included, `end` is not.

**S1.3** A span covers a section's **body** — the text between its heading line and the next
numbered heading, whitespace-trimmed, exactly as reported.

**S1.4** Offsets index the source **as read without newline translation**. Against a
newline-translated copy they are wrong by one byte per preceding line on a CRLF document.

## What a span is not

Stated explicitly, because a consumer reading only the positive half will assume the rest.

**S2.1** A span makes **no claim about headings**. No span locates a heading line, and no span's
range includes one.

**S2.2** A span makes **no claim about values**. No value carries a span in any form, including a
location without a reproduction guarantee.

**S2.3** A span is not a line range and carries no line or column information.

## The reproduction guarantee

**S3.1** For every section: `source.encode("utf-8")[start:end].decode("utf-8") == body`.

**S3.2** S3.1 holds on a document with **CRLF** line endings.

**S3.3** S3.1 holds on a document containing a character **outside the Basic Multilingual
Plane**.

**S3.4** S3.2 and S3.3 are asserted against a fixture carrying both. Every brief in the
repository is LF and non-astral, so a test over existing briefs would establish only that it
works on those.

**S3.5** `end` is derived as `start + len(body.encode("utf-8"))`. The guarantee therefore holds
by construction, and only `start` can be wrong.

## Edge cases

**S4.1** An empty body yields `start == end`, never an absent span.

**S4.2** A section whose body is entirely whitespace has an empty reported body and an empty
span.

**S4.3** A duplicated ordinal produces one entry per occurrence, each with its own span.

**S4.4** A section that has absorbed an unnumbered heading has a span covering its whole body,
absorbed content included — the span reports what is there, not what should be.

## Reading the source

**S5.1** Every path that reads a brief reads it without newline translation, so all commands
parse the same string for one file.

**S5.2** Parsing a CRLF brief yields **field values identical** to parsing the same brief with LF
endings. Only section bodies differ, and only in their line terminators.

**S5.3** A bundle generated from a CRLF brief is **byte-identical** to one generated from the
same brief with LF endings. This is what makes the reader change additive, and it is asserted
rather than assumed.
