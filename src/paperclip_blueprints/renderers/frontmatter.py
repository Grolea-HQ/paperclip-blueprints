"""YAML frontmatter rendering for agentcompanies/v1 and paperclip/v1.

Uses ruamel.yaml (ADR-001, research R7) so the emitted frontmatter matches the
reference companies' style: single-quoted scalars where quoting is needed, inline
(flow) sequences for slug/tag lists, block sequences for prose lists, ``null`` for
None, and insertion-ordered keys.
"""

from __future__ import annotations

import io
from collections.abc import Mapping
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.scalarstring import SingleQuotedScalarString as SQ

# Characters that force single-quoting to keep YAML unambiguous and match the
# reference files. A bare ``/`` is valid in a YAML plain scalar (e.g.
# ``schema: agentcompanies/v1``), so it is deliberately NOT a trigger.
_NEEDS_QUOTE = set(" :#,[]{}\"'@`&*!|>%?")


def _scalar(value: str) -> str | SQ:
    """Single-quote a string scalar if it needs it; otherwise leave it bare."""
    if value == "":
        return value
    if value != value.strip() or any(ch in _NEEDS_QUOTE for ch in value):
        return SQ(value)
    if value.lower() in {"null", "true", "false", "yes", "no", "~"}:
        return SQ(value)
    if not value[0].isalnum():
        return SQ(value)
    return value


def _convert(value: Any, key: str | None, flow_seq_keys: set[str]) -> Any:
    if isinstance(value, Mapping):
        m = CommentedMap()
        for k, v in value.items():
            m[k] = _convert(v, k, flow_seq_keys)
        return m
    if isinstance(value, (list, tuple)):
        seq = CommentedSeq(_convert(item, None, flow_seq_keys) for item in value)
        if key is not None and key in flow_seq_keys:
            seq.fa.set_flow_style()
        return seq
    if isinstance(value, str):
        return _scalar(value)
    return value


def dump_frontmatter(data: Mapping[str, Any], *, flow_seq_keys: set[str] | None = None) -> str:
    """Render ``data`` as a fenced YAML frontmatter block.

    Args:
        data: Insertion-ordered mapping of frontmatter keys to values.
        flow_seq_keys: Keys whose list values should render inline (``[a, b]``)
            instead of as block sequences.

    Returns:
        A string beginning and ending with a ``---`` fence line.
    """
    flow = flow_seq_keys or set()
    root = _convert(data, None, flow)

    yaml = YAML()
    yaml.default_flow_style = False
    yaml.allow_unicode = True
    yaml.width = 4096  # don't wrap long scalars
    # Match the reference companies: block-sequence items indented 2 under their key.
    yaml.indent(mapping=2, sequence=4, offset=2)
    # Emit explicit ``null`` (not empty) to match the reference files.
    yaml.representer.add_representer(
        type(None),
        lambda r, _d: r.represent_scalar("tag:yaml.org,2002:null", "null"),
    )

    buf = io.StringIO()
    yaml.dump(root, buf)
    body = buf.getvalue().rstrip("\n")
    return f"---\n{body}\n---\n"
