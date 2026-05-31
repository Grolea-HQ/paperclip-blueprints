"""Tests for use-case pattern seeds and the registry (T037)."""

import pytest

from paperclip_blueprints.patterns import (
    KNOWN_PATTERNS,
    UnknownPatternError,
    get_seed,
)
from paperclip_blueprints.patterns.base import OrgSeed

_EXPECTED = {
    "solo-dev-shop",
    "content-operations",
    "product-sprint",
    "open-source-maintenance",
    "newsletter",
    "niche-site",
    "agency",
    "membership",
    "seo-bureau",
}


def test_known_patterns_match_input_template_set() -> None:
    assert set(KNOWN_PATTERNS) == _EXPECTED | {"custom"}


@pytest.mark.parametrize("slug", sorted(_EXPECTED))
def test_each_seed_is_usable(slug: str) -> None:
    seed = get_seed(slug)
    assert isinstance(seed, OrgSeed)
    assert seed.slug == slug
    # A usable seed suggests a hierarchy, skills, and starter projects.
    assert seed.suggested_roles
    assert any(reports_to is None for _, reports_to in seed.suggested_roles)  # has a root
    assert seed.suggested_skills
    assert seed.suggested_projects
    rendered = seed.render()
    assert "Suggested roles:" in rendered


def test_custom_and_unset_yield_no_seed() -> None:
    assert get_seed("custom") is None
    assert get_seed(None) is None


def test_unknown_pattern_raises_with_available_set() -> None:
    with pytest.raises(UnknownPatternError) as exc:
        get_seed("franchise-empire")
    assert exc.value.slug == "franchise-empire"
    assert "solo-dev-shop" in exc.value.available
    assert "custom" in str(exc.value)
