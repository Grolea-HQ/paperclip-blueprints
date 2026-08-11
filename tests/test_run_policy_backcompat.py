"""Backward-compat gate for feature 014 (release-blocking — do NOT weaken or fold).

A brief with no run-policy values MUST generate byte-identical output to today. The
golden reference `tests/fixtures/runpolicy_baseline.paperclip.yaml` was frozen from the
**unmodified** generator BEFORE the feature landed; this test COMPARES against it and must
never regenerate it. The conditions under which such a fixture may be edited rather than
re-captured are in CONTRIBUTING.md. If this test fails, the override layer has leaked into
the no-override
path and every existing operator's bundle is re-priced — treat it as release-blocking.
"""

from __future__ import annotations

from pathlib import Path

from paperclip_blueprints.generators.client import LLMClient
from paperclip_blueprints.renderers.bundle import generate_bundle_full
from paperclip_blueprints.renderers.render import render_files
from test_cli import _dispatch_full
from test_orchestration import _brief

_BASELINE = Path(__file__).parent / "fixtures" / "runpolicy_baseline.paperclip.yaml"


def test_no_run_policy_prefs_is_byte_identical_to_baseline() -> None:
    config = generate_bundle_full(_brief(), LLMClient(_invoke=_dispatch_full))
    # The fixture brief states no run-policy values.
    assert config.brief.run_policy_preferences is None

    out = render_files(config)[".paperclip.yaml"]
    expected = _BASELINE.read_text()

    # (a) byte-identical to the frozen pre-feature output (role rule untouched); and
    # (b) no heartbeatEnabled key anywhere — the tri-state None renders nothing.
    assert out == expected
    assert "heartbeatEnabled" not in out
