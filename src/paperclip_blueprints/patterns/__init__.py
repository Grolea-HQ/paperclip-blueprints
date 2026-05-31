"""Use-case pattern seeds (v0.1b, US2 / R-006).

A pattern seeds the org_planner with a suggested org shape that the prompts then
customize against the brief. Slugs match the input template exactly. ``custom``
(or no pattern) means free-form planning with no seed.
"""

from __future__ import annotations

from . import (
    agency,
    content_operations,
    membership,
    newsletter,
    niche_site,
    open_source_maintenance,
    product_sprint,
    seo_bureau,
    solo_dev_shop,
)
from .base import OrgSeed

_SEEDS: list[OrgSeed] = [
    solo_dev_shop.SEED,
    content_operations.SEED,
    product_sprint.SEED,
    open_source_maintenance.SEED,
    newsletter.SEED,
    niche_site.SEED,
    agency.SEED,
    membership.SEED,
    seo_bureau.SEED,
]

_REGISTRY: dict[str, OrgSeed] = {seed.slug: seed for seed in _SEEDS}

# The full set an operator may name in the brief (the seeds plus the free-form
# escape hatch). Kept in sync with examples/input-template.md §7.
KNOWN_PATTERNS: list[str] = [*sorted(_REGISTRY), "custom"]


class UnknownPatternError(Exception):
    """Raised when a brief names a use-case pattern the tool does not recognize."""

    def __init__(self, slug: str, available: list[str]) -> None:
        self.slug = slug
        self.available = available
        super().__init__(f"unknown use-case pattern {slug!r}; available: {', '.join(available)}")


def get_seed(slug: str | None) -> OrgSeed | None:
    """Return the seed for a pattern slug, or None for ``custom``/unset.

    Raises:
        UnknownPatternError: if the slug is neither a known seed nor ``custom``.
    """
    if slug is None or slug == "custom":
        return None
    if slug not in _REGISTRY:
        raise UnknownPatternError(slug, KNOWN_PATTERNS)
    return _REGISTRY[slug]
