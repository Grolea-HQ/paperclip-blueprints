"""Compatibility gate for feature 020 (release-blocking — do NOT weaken or regenerate).

Every brief on disk must parse to exactly what it parsed to before this feature. The
baselines in ``tests/fixtures/brief_baseline_020/`` were captured from a **detached
worktree at the pre-change commit** (2f5159c), so they record the parser's behaviour at a
commit no working-tree edit can reach. They are frozen references: this test COMPARES
against them and must never regenerate them. The conditions under which such a fixture may
be edited rather than re-captured are in CONTRIBUTING.md.

A baseline records the OUTCOME, whichever it was. Three briefs parse; the shipped template
does not, and "it fails with exactly these messages" is behaviour too — a silent change to
how a template-shaped document fails is the same class of defect as a silent change to how
a real one parses.

``examples/input-template.md`` is handled separately and deliberately. Feature 020 changes
that file (FR-014), so a "must be unchanged" assertion would be false by construction. Its
pre-change baseline is kept as evidence of what the restructure fixes, and
:func:`test_template_baseline_records_the_absorption_defect` pins the defect that made the
restructure necessary. The post-restructure expectation lives with the restructure.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from paperclip_blueprints.models.input import BriefValidationError, parse_brief

_REPO_ROOT = Path(__file__).resolve().parent.parent
_BASELINES = Path(__file__).parent / "fixtures" / "brief_baseline_020"

# The template is excluded: this feature changes it on purpose. See the module docstring.
_UNCHANGED_BRIEFS = [
    "examples/example-brief-indie-game-studio.md",
    "examples/example-brief-research-digest.md",
    "scripts/probe_brief.md",
]

_TEMPLATE = "examples/input-template.md"


def _baseline(rel: str) -> dict[str, object]:
    return json.loads((_BASELINES / f"{rel.replace('/', '__')}.json").read_text(encoding="utf-8"))


def _current(rel: str) -> dict[str, object]:
    text = (_REPO_ROOT / rel).read_text(encoding="utf-8")
    try:
        brief = parse_brief(text)
    except BriefValidationError as exc:
        return {"source": rel, "outcome": "invalid", "messages": list(exc.messages)}
    return {"source": rel, "outcome": "valid", "brief": brief.model_dump(mode="json")}


@pytest.mark.parametrize("rel", _UNCHANGED_BRIEFS)
def test_brief_parses_to_its_frozen_baseline(rel: str) -> None:
    """C7.1 — no brief on disk changes meaning.

    Covers the two cases that constrain the schema's shape: a brief using section 11's
    earlier heading (``Anything else``), and one that stops at section 9 (C7.2, C7.3).
    """
    assert _current(rel) == _baseline(rel)


def test_every_baseline_is_covered_by_a_test() -> None:
    """A baseline nobody compares against is a file, not a gate.

    Without this, adding a brief to the fixtures directory and forgetting to list it would
    leave it silently unchecked — an absence of failures standing in for a positive
    assertion.
    """
    captured = {p.name for p in _BASELINES.glob("*.json")}
    accounted = {f"{rel.replace('/', '__')}.json" for rel in [*_UNCHANGED_BRIEFS, _TEMPLATE]}
    assert captured == accounted


def test_template_baseline_records_the_absorption_defect() -> None:
    """The pre-change template is invalid, and part of why is an absorbed heading.

    ``## Validation checklist`` and ``## What happens next`` carry no ordinal, so the
    splitter does not see them and their bodies fall inside section 12. Their bullet lines
    are then read as run-policy override lines. This pins the defect that FR-014's
    restructure removes, so the restructure has something to be measured against rather
    than being asserted to have worked.
    """
    baseline = _baseline(_TEMPLATE)
    assert baseline["outcome"] == "invalid"
    messages = baseline["messages"]
    assert isinstance(messages, list)
    run_policy = [m for m in messages if str(m).startswith("run_policy_preferences:")]
    assert len(run_policy) == 1, "expected the absorbed lines to surface as one aggregated error"
    # Lines from the two unnumbered trailing sections, neither of which is a run policy.
    assert "One-sentence description" in run_policy[0]
    assert "LICENSE.txt" in run_policy[0]


def test_the_restructured_template_no_longer_absorbs_its_trailing_sections() -> None:
    """The counterpart to the baseline above: what the restructure actually removed.

    The pre-change baseline records twenty checklist and closing-guidance lines being read
    as run-policy overrides. After moving both trailing sections ahead of section 1, the
    template fails on its unfilled fields and nothing else — which is correct for a
    template, whose fields are deliberately unfilled.

    Asserted against the baseline rather than against a hardcoded count, so this test
    states a *change* rather than a snapshot: it fails if the defect returns and it fails
    if the restructure silently removed something else as well.
    """
    before = _baseline(_TEMPLATE)["messages"]
    assert isinstance(before, list)

    with pytest.raises(BriefValidationError) as excinfo:
        parse_brief((_REPO_ROOT / _TEMPLATE).read_text(encoding="utf-8"))
    after = excinfo.value.messages

    removed = [m for m in before if m not in after]
    assert [m.split(":")[0] for m in removed] == ["run_policy_preferences"]
    assert [m for m in after if m not in before] == []
    assert all(m.endswith("Field required") for m in after)
