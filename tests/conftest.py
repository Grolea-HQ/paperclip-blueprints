"""Shared pytest configuration.

Registers the ``--integration`` flag so tests that make real Anthropic API calls
are skipped by default (Constitution III: no live calls in the default suite).
"""

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add the ``--integration`` flag that enables integration-marked tests."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="run integration tests that make real Anthropic API calls",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Skip ``@pytest.mark.integration`` tests unless ``--integration`` is passed."""
    if config.getoption("--integration"):
        return
    skip = pytest.mark.skip(reason="needs --integration to run (real API call)")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip)
