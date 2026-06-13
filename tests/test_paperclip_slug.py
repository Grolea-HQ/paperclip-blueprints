"""Unit tests for the Paperclip slug replication (ADR-013, contract C1–C6)."""

from paperclip_blueprints.paperclip_slug import dedupe_slug, slugify_project_name


def test_em_dash_and_spaces_collapse() -> None:
    # C1 — the real-world case that broke task association.
    assert (
        slugify_project_name("SEO Content Foundation — First Keyword Cluster")
        == "seo-content-foundation-first-keyword-cluster"
    )


def test_punctuation_and_trim() -> None:
    # C2
    assert slugify_project_name("  Hello, World!  ") == "hello-world"


def test_leading_trailing_separators_stripped() -> None:
    # C3
    assert slugify_project_name("--A B--") == "a-b"


def test_idempotent_on_ascii() -> None:
    # C4
    s = "Pricing Validation (v1)"
    once = slugify_project_name(s)
    assert once == slugify_project_name(once)
    assert once == "pricing-validation-v1"


def test_dedupe_sequence() -> None:
    # C5
    used: set[str] = set()
    assert dedupe_slug("foo", used) == "foo"
    assert dedupe_slug("foo", used) == "foo-2"
    assert dedupe_slug("foo", used) == "foo-3"
    assert "foo" in used and "foo-2" in used and "foo-3" in used


def test_all_non_ascii_returns_empty() -> None:
    # C6 — caller falls back when this happens.
    assert slugify_project_name("日本語") == ""


def test_digits_preserved() -> None:
    assert slugify_project_name("Q3 2026 Launch") == "q3-2026-launch"
