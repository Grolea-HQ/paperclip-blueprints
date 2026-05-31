"""Bundle orchestration: generate -> assemble -> structural check -> atomic write.

The whole bundle is rendered in memory and structurally checked BEFORE anything
touches disk, then written to a temp dir and atomically moved into place. A failed
generation or check leaves no partial bundle (FR-017, research R4/R5).
"""

from __future__ import annotations

import asyncio
import os
import re
import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..generators.agents import generate_agent
from ..generators.client import GenerationError, LLMClient
from ..generators.identity import generate_identity
from ..generators.operations import generate_operations
from ..generators.org import AgentStub, generate_org, generate_org_plan
from ..generators.projects import generate_project
from ..generators.skills import generate_skill
from ..generators.souls import generate_soul
from ..generators.tasks import generate_task
from ..models.input import CompanyBrief
from ..models.output import CompanyConfig
from .render import render_files

_TOP_LEVEL = {".paperclip.yaml", "COMPANY.md", "README.md", "LICENSE.txt"}
_FULL_TOP_LEVEL = _TOP_LEVEL | {"OPERATIONS.md", "PROJECT-INVENTORY.md"}
_AGENT_FILES = {"AGENTS.md", "SOUL.md", "HEARTBEAT.md", "TOOLS.md"}

# Bounded concurrency for the fan-out so a large org does not open dozens of
# simultaneous API calls (R-004).
_CONCURRENCY = 6


class BundleError(Exception):
    """Raised when an assembled bundle fails its structural check."""


def generate_bundle(
    brief: CompanyBrief, client: LLMClient, *, model: str | None = None
) -> CompanyConfig:
    """Run the single-agent generation pipeline (sequential)."""
    company = generate_identity(brief, client, model=model)
    stub = generate_org(brief, company, client, model=model)
    soul = generate_soul(stub, company, client, model=model)
    agent = generate_agent(stub, company, brief, soul, client, single_agent=True, model=model)
    skill = generate_skill(stub.skills[0], company, [agent.name], client, model=model)
    return CompanyConfig(
        mode="single", brief=brief, company=company, agents=[agent], skills=[skill]
    )


async def _gather_full(
    brief: CompanyBrief, client: LLMClient, *, model: str | None = None
) -> CompanyConfig:
    """Fan out per-agent and per-leaf generation concurrently (R-004).

    Identity and the org plan are sequential (everything depends on them); then
    every agent, skill, project, and task is generated concurrently under a
    bounded semaphore; OPERATIONS.md is generated last (it needs the agent list).
    Any failure propagates out of ``gather`` so no partial bundle is ever written.
    """
    company = await asyncio.to_thread(generate_identity, brief, client, model=model)
    plan = await asyncio.to_thread(
        generate_org_plan, brief, company, client, single_agent=False, model=model
    )

    sem = asyncio.Semaphore(_CONCURRENCY)

    async def run(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        async with sem:
            return await asyncio.to_thread(fn, *args, **kwargs)

    reports_by_manager: dict[str, list[str]] = {}
    for a in plan.agents:
        if a.reports_to is not None:
            reports_by_manager.setdefault(a.reports_to, []).append(a.slug)

    async def make_agent(stub: AgentStub) -> Any:
        soul = await run(generate_soul, stub, company, client, model=model)
        peers = (
            [s for s in reports_by_manager.get(stub.reports_to, []) if s != stub.slug]
            if stub.reports_to is not None
            else []
        )
        return await run(
            generate_agent,
            stub,
            company,
            brief,
            soul,
            client,
            manager=stub.reports_to,
            reports=reports_by_manager.get(stub.slug, []),
            peers=peers,
            model=model,
        )

    def _used_by(slug: str) -> list[str]:
        return [a.name for a in plan.agents if slug in a.skills]

    agents, skills, projects, tasks = await asyncio.gather(
        asyncio.gather(*(make_agent(s) for s in plan.agents)),
        asyncio.gather(
            *(
                run(generate_skill, s, company, _used_by(s), client, model=model)
                for s in plan.skill_slugs
            )
        ),
        asyncio.gather(
            *(run(generate_project, p, company, client, model=model) for p in plan.projects)
        ),
        asyncio.gather(*(run(generate_task, t, company, client, model=model) for t in plan.tasks)),
    )

    operations = await asyncio.to_thread(
        generate_operations, company, brief, plan.agents, client, model=model
    )

    try:
        return CompanyConfig(
            mode="full",
            brief=brief,
            company=company,
            agents=list(agents),
            skills=list(skills),
            projects=list(projects),
            tasks=list(tasks),
            operations=operations,
        )
    except Exception as exc:  # noqa: BLE001 - pydantic ValidationError surfaces cleanly
        raise GenerationError(f"assembled bundle failed validation: {exc}") from exc


def generate_bundle_full(
    brief: CompanyBrief, client: LLMClient, *, model: str | None = None
) -> CompanyConfig:
    """Run the full multi-agent generation pipeline (concurrent fan-out)."""
    return asyncio.run(_gather_full(brief, client, model=model))


def _we_are_not_count(company_md: str) -> int:
    """Count the bullets in COMPANY.md's 'We are not.' block."""
    after = company_md.split("**We are not.**", 1)
    if len(after) < 2:
        return 0
    block = re.split(r"\n\*\*", after[1], maxsplit=1)[0]
    return len(re.findall(r"^\s*-\s+\S", block, re.MULTILINE))


def structural_check(files: dict[str, str]) -> None:
    """Validate the in-memory bundle against the contract before any write.

    Operates purely on the rendered files so it validates the actual artifact.
    The mode is inferred from the presence of OPERATIONS.md (full bundle) vs its
    absence (single-agent). This is US1's baseline guard; US3 replaces it with the
    dedicated ``validators/`` module.

    Raises:
        BundleError: on any structural violation.
    """
    if "OPERATIONS.md" in files:
        _check_full(files)
    else:
        _check_single(files)


def _check_single(files: dict[str, str]) -> None:
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

    if "schema: paperclip/v1" not in files[".paperclip.yaml"]:
        raise BundleError(".paperclip.yaml is missing 'schema: paperclip/v1'")
    for rel in ("COMPANY.md", f"agents/{agent_slug}/AGENTS.md", f"skills/{skill_slug}/SKILL.md"):
        if "schema: agentcompanies/v1" not in files[rel]:
            raise BundleError(f"{rel} is missing 'schema: agentcompanies/v1'")

    if _we_are_not_count(files["COMPANY.md"]) < 2:
        raise BundleError("COMPANY.md must have at least 2 'we are not' entries")
    if "idle" not in files[f"agents/{agent_slug}/SOUL.md"].lower():
        raise BundleError("SOUL.md must include an idle-state belief")

    if skill_slug not in files[f"agents/{agent_slug}/AGENTS.md"]:
        raise BundleError(f"agent {agent_slug} does not reference skill {skill_slug}")


def _dirs_under(paths: set[str], prefix: str) -> set[str]:
    return {p.split("/")[1] for p in paths if p.startswith(prefix)}


def _frontmatter_value(text: str, key: str) -> str | None:
    """Read a scalar frontmatter value (e.g. ``project: launch-v1``) from a file."""
    m = re.search(rf"^{re.escape(key)}:\s*(.+)$", text, re.MULTILINE)
    return m.group(1).strip().strip("'\"") if m else None


def _check_full(files: dict[str, str]) -> None:
    paths = set(files)

    missing = _FULL_TOP_LEVEL - paths
    if missing:
        raise BundleError(f"missing top-level files: {sorted(missing)}")

    agent_slugs = _dirs_under(paths, "agents/")
    if not agent_slugs:
        raise BundleError("a full bundle must have at least one agent")
    for slug in agent_slugs:
        have = {p.split("/")[2] for p in paths if p.startswith(f"agents/{slug}/")}
        if have != _AGENT_FILES:
            raise BundleError(f"agent {slug} files wrong: {sorted(have)}")
        if "idle" not in files[f"agents/{slug}/SOUL.md"].lower():
            raise BundleError(f"agent {slug} SOUL.md must include an idle-state belief")

    skill_slugs = _dirs_under(paths, "skills/")
    project_slugs = _dirs_under(paths, "projects/")
    if not project_slugs:
        raise BundleError("a full bundle must have at least one project")
    task_dirs = _dirs_under(paths, "tasks/")
    if not task_dirs:
        raise BundleError("a full bundle must have at least one task")

    # Schema-string invariants across every schema-bearing file.
    if "schema: paperclip/v1" not in files[".paperclip.yaml"]:
        raise BundleError(".paperclip.yaml is missing 'schema: paperclip/v1'")
    schema_bearing = ["COMPANY.md"]
    schema_bearing += [
        p for p in paths if p.endswith(("AGENTS.md", "SKILL.md", "PROJECT.md", "TASK.md"))
    ]
    for rel in schema_bearing:
        if "schema: agentcompanies/v1" not in files[rel]:
            raise BundleError(f"{rel} is missing 'schema: agentcompanies/v1'")

    if _we_are_not_count(files["COMPANY.md"]) < 2:
        raise BundleError("COMPANY.md must have at least 2 'we are not' entries")

    # Skill closure: every skill an agent references resolves to a SKILL.md, and
    # every generated skill is referenced by some agent.
    referenced: set[str] = set()
    for slug in agent_slugs:
        fm = files[f"agents/{slug}/AGENTS.md"]
        m = re.search(r"^skills:\s*\[(.*?)\]", fm, re.MULTILINE)
        if m:
            referenced |= {s.strip() for s in m.group(1).split(",") if s.strip()}
    dangling = referenced - skill_slugs
    if dangling:
        raise BundleError(f"agents reference skills with no SKILL.md: {sorted(dangling)}")
    orphan = skill_slugs - referenced
    if orphan:
        raise BundleError(f"generated skills referenced by no agent: {sorted(orphan)}")

    # Task referential integrity: project + assignee must exist.
    for slug in task_dirs:
        task_md = files[f"tasks/{slug}/TASK.md"]
        proj = _frontmatter_value(task_md, "project")
        assignee = _frontmatter_value(task_md, "assignee")
        if proj not in project_slugs:
            raise BundleError(f"task {slug} references unknown project {proj!r}")
        if assignee not in agent_slugs:
            raise BundleError(f"task {slug} assigned to unknown agent {assignee!r}")

    # Project ownership must resolve.
    for slug in project_slugs:
        owner = _frontmatter_value(files[f"projects/{slug}/PROJECT.md"], "owner")
        if owner not in agent_slugs:
            raise BundleError(f"project {slug} owned by unknown agent {owner!r}")

    # Anti-drift echo: OPERATIONS.md must be non-trivial and carry anti-drift checks.
    if "Anti-drift checks" not in files["OPERATIONS.md"]:
        raise BundleError("OPERATIONS.md is missing its 'Anti-drift checks' section")


def write_bundle(files: dict[str, str], output_dir: str | Path, *, force: bool = False) -> Path:
    """Atomically write the bundle directly into ``output_dir`` (R5/R6).

    ``--output <dir>`` means "write the bundle into this directory" — no slug
    subdirectory is appended.

    Raises:
        BundleError: if the destination is non-empty and ``force`` is not set.
    """
    dest = Path(output_dir)
    if dest.exists() and any(dest.iterdir()) and not force:
        raise BundleError(f"output directory {dest} is not empty; pass --force to overwrite")

    parent = dest.parent
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
    single_agent: bool = False,
    model: str | None = None,
    force: bool = False,
) -> Path:
    """Generate, validate, and atomically write a bundle (full or single-agent).

    The bundle is written directly into ``output_dir`` (no slug subdirectory). The
    full bundle fans out concurrently; the single-agent bundle runs sequentially.
    Validation happens fully in memory before any file is written, so a failed
    generation or check leaves no partial bundle.
    """
    if single_agent:
        config = generate_bundle(brief, client, model=model)
    else:
        config = generate_bundle_full(brief, client, model=model)
    files = render_files(config)
    structural_check(files)
    return write_bundle(files, output_dir, force=force)
