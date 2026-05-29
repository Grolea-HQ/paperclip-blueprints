"""Smoke test: the package imports and exposes a version."""

import paperclip_blueprints


def test_package_imports() -> None:
    assert isinstance(paperclip_blueprints.__version__, str)
