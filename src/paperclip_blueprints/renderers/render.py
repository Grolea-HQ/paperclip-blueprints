"""Render a CompanyConfig into the in-memory bundle file map.

Bodies come from Jinja templates in ``templates/``; YAML frontmatter is produced by
:func:`dump_frontmatter` so quoting/order match the reference companies. Returns a
``{relative_path: content}`` map — nothing touches disk here (the atomic write lives
in ``bundle.py``).
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from ..models.output import CompanyConfig
from .frontmatter import dump_frontmatter

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
    undefined=StrictUndefined,
    autoescape=False,
)


def _render(template: str, **ctx: object) -> str:
    return _env.get_template(template).render(**ctx)


def _company_frontmatter(config: CompanyConfig) -> str:
    c = config.company
    return dump_frontmatter(
        {
            "schema": "agentcompanies/v1",
            "name": c.name,
            "description": c.description,
            "version": c.version,
            "tags": c.tags,
            "goals": c.goals,
            "metadata": {"paperclip": {"tone": c.tone, "mono": c.mono}},
        },
        flow_seq_keys={"tags"},
    )


def _agents_frontmatter(config: CompanyConfig) -> str:
    a = config.agent
    return dump_frontmatter(
        {
            "schema": "agentcompanies/v1",
            "slug": a.slug,
            "name": a.name,
            "title": a.title,
            "reportsTo": a.reports_to,
            "skills": a.skills,
        },
        flow_seq_keys={"skills"},
    )


def _skill_frontmatter(config: CompanyConfig) -> str:
    s = config.skill
    return dump_frontmatter(
        {
            "schema": "agentcompanies/v1",
            "slug": s.slug,
            "name": s.name,
            "description": s.description,
        }
    )


def render_files(config: CompanyConfig) -> dict[str, str]:
    """Render every file of a single-agent bundle to a path→content map."""
    agent = config.agent
    ctx = {
        "brief": config.brief,
        "company": config.company,
        "agent": agent,
        "soul": agent.soul,
        "skill": config.skill,
        "license_kind": config.license_kind,
    }
    adir = f"agents/{agent.slug}"
    sdir = f"skills/{config.skill.slug}"

    return {
        ".paperclip.yaml": _render("paperclip_yaml.j2", **ctx),
        "COMPANY.md": _company_frontmatter(config) + "\n" + _render("company_md.j2", **ctx),
        "README.md": _render("readme_md.j2", **ctx),
        "LICENSE.txt": _render("license_txt.j2", **ctx),
        f"{adir}/AGENTS.md": _agents_frontmatter(config) + "\n" + _render("agents_md.j2", **ctx),
        f"{adir}/SOUL.md": _render("soul_md.j2", **ctx),
        f"{adir}/HEARTBEAT.md": _render("heartbeat_md.j2", **ctx),
        f"{adir}/TOOLS.md": _render("tools_md.j2", **ctx),
        f"{sdir}/SKILL.md": _skill_frontmatter(config) + "\n" + _render("skill_md.j2", **ctx),
    }
