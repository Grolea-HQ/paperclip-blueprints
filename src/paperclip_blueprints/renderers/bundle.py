"""Bundle orchestration: generate -> assemble -> structural check -> atomic write.

The whole bundle is rendered in memory and structurally checked BEFORE anything
touches disk, then written to a temp dir and atomically moved into place. A failed
generation or check leaves no partial bundle (FR-017, research R4/R5).
"""

from __future__ import annotations

import os
import re
import shutil
import tempfile
from pathlib import Path

from ..generators.agents import generate_agent
from ..generators.client import LLMClient
from ..generators.identity import generate_identity
from ..generators.org import generate_org
from ..generators.skills import generate_skill
from ..generators.souls import generate_soul
from ..models.input import CompanyBrief
from ..models.output import CompanyConfig
from .render import render_files

_TOP_LEVEL = {".paperclip.yaml", "COMPANY.md", "README.md", "LICENSE.txt"}
_AGENT_FILES = {"AGENTS.md", "SOUL.md", "HEARTBEAT.md", "TOOLS.md"}


class BundleError(Exception):
    """Raised when an assembled bundle fails its structural check."""


def generate_bundle(
    brief: CompanyBrief, client: LLMClient, *, model: str | None = None
) -> CompanyConfig:
    """Run the single-agent generation pipeline (sequential in v0.1a)."""
    company = generate_identity(brief, client, model=model)
    stub = generate_org(brief, company, client, model=model)
    soul = generate_soul(stub, company, client, model=model)
    agent = generate_agent(stub, company, brief, soul, client, model=model)
    skill = generate_skill(stub.skills[0], company, [agent.name], client, model=model)
    return CompanyConfig(brief=brief, company=company, agent=agent, skill=skill)


def _we_are_not_count(company_md: str) -> int:
    """Count the bullets in COMPANY.md's 'We are not.' block."""
    after = company_md.split("**We are not.**", 1)
    if len(after) < 2:
        return 0
    block = re.split(r"\n\*\*", after[1], maxsplit=1)[0]
    return len(re.findall(r"^\s*-\s+\S", block, re.MULTILINE))


def structural_check(files: dict[str, str]) -> None:
    """Validate the in-memory bundle against the single-agent contract (R4).

    Operates purely on the rendered files so it validates the actual artifact.

    Raises:
        BundleError: on any structural violation.
    """
    paths = set(files)

    missing = _TOP_LEVEL - paths
    if missing:
        raise BundleError(f"missing top-level files: {sorted(missing)}")

    agent_dirs = {p.split("/")[1] for p in paths if p.startswith("agents/")}
    if len(agent_dirs) != 1:
        raise BundleError(f"expected exactly one agent, found {sorted(agent_dirs)}")
    (agent_slug,) = agent_dirs
    have = {p.split("/")[2] for p in paths if p.startswith(f"agents/{agent_slug}/")}
    if have != _AGENT_FILES:
        raise BundleError(f"agent {agent_slug} files wrong: {sorted(have)}")

    skill_dirs = {p.split("/")[1] for p in paths if p.startswith("skills/")}
    if len(skill_dirs) != 1:
        raise BundleError(f"expected exactly one skill, found {sorted(skill_dirs)}")
    (skill_slug,) = skill_dirs
    if f"skills/{skill_slug}/SKILL.md" not in paths:
        raise BundleError(f"skill {skill_slug} is missing SKILL.md")

    if len(paths) != 9:
        raise BundleError(f"expected exactly 9 files, found {len(paths)}")

    # Schema-string invariants.
    if "schema: paperclip/v1" not in files[".paperclip.yaml"]:
        raise BundleError(".paperclip.yaml is missing 'schema: paperclip/v1'")
    for rel in ("COMPANY.md", f"agents/{agent_slug}/AGENTS.md", f"skills/{skill_slug}/SKILL.md"):
        if "schema: agentcompanies/v1" not in files[rel]:
            raise BundleError(f"{rel} is missing 'schema: agentcompanies/v1'")

    # Best-practice invariants visible in the artifact.
    if _we_are_not_count(files["COMPANY.md"]) < 2:
        raise BundleError("COMPANY.md must have at least 2 'we are not' entries")
    if "idle" not in files[f"agents/{agent_slug}/SOUL.md"].lower():
        raise BundleError("SOUL.md must include an idle-state belief")

    # Skill cross-reference: the agent must list the generated skill.
    if skill_slug not in files[f"agents/{agent_slug}/AGENTS.md"]:
        raise BundleError(
            f"agent {agent_slug} does not reference skill {skill_slug}"
        )


def write_bundle(
    files: dict[str, str], output_dir: str | Path, slug: str, *, force: bool = False
) -> Path:
    """Atomically write the bundle to ``<output_dir>/<slug>/`` (R5/R6).

    Raises:
        BundleError: if the destination is non-empty and ``force`` is not set.
    """
    parent = Path(output_dir)
    dest = parent / slug
    if dest.exists() and any(dest.iterdir()) and not force:
        raise BundleError(f"output directory {dest} is not empty; pass --force to overwrite")

    parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(dir=parent))
    try:
        for rel, content in files.items():
            target = tmp / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        if dest.exists():
            shutil.rmtree(dest)
        os.replace(tmp, dest)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    return dest


def build_and_write(
    brief: CompanyBrief,
    output_dir: str | Path,
    client: LLMClient,
    *,
    model: str | None = None,
    force: bool = False,
) -> Path:
    """Generate, validate, and atomically write a single-agent bundle."""
    config = generate_bundle(brief, client, model=model)
    files = render_files(config)
    structural_check(files)
    return write_bundle(files, output_dir, brief.slug, force=force)
