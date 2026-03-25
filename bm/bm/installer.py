"""Skill discovery and installation (symlink-first, copy fallback)."""

from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

from bm.dryrun import DryRunContext
from bm.models import InstallMethod, InstallResult, SkillEntry, SkillScope, SkillSource
from bm.registry import Registry
from bm.validator import validate_skill

_err = Console(stderr=True)


def _read_skill_description(skill_path: Path) -> str:
    """Read 'description:' from SKILL.md frontmatter. Returns empty string if absent."""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return ""
    for line in skill_md.read_text(encoding="utf-8").splitlines():
        if line.startswith("---") and line != "---":
            break  # end of frontmatter
        if line.startswith("description:"):
            return line.split(":", 1)[1].strip().strip('"')
    return ""


def _is_project_dir(path: Path) -> bool:
    """
    A directory is a *project container* (not a skill) if it has no SKILL.md
    of its own but contains subdirectories that do have SKILL.md files.
    Example: skills/pcs/ is a project dir; skills/vercel-cli/ is a skill.
    """
    if (path / "SKILL.md").exists():
        return False
    return any(
        child.is_dir() and (child / "SKILL.md").exists()
        for child in path.iterdir()
        if not child.name.startswith(".")
    )


def discover_skills(skills_dir: Path) -> list[SkillEntry]:
    """
    Return all SkillEntry objects from skills_dir.

    - Top-level dirs with a SKILL.md → general skills
    - Top-level dirs without SKILL.md but containing skill subdirs → project
      containers; their children are yielded as PROJECT-scoped skills
    - Dirs that are neither (e.g. README-only) are skipped silently

    PCS skills in skills/pcs/ are included automatically; any other
    project folder (skills/myproject/) is discovered the same way.
    """
    entries: list[SkillEntry] = []

    for child in sorted(skills_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue

        # Safety: skip symlinks in the source directory — real skills are always
        # plain directories, never symlinks.  Symlinks here indicate a previous
        # broken install that leaked links back into the repo (the root cause of
        # the circular-symlink corruption in commit 484cdfb).
        if child.is_symlink():
            _err.print(
                f"[yellow]Warning:[/] Skipping symlink '{child.name}' in {skills_dir} "
                f"(expected a real directory, not a symlink)"
            )
            continue

        if _is_project_dir(child):
            project_name = child.name
            for skill_dir in sorted(child.iterdir()):
                if skill_dir.is_symlink():
                    _err.print(
                        f"[yellow]Warning:[/] Skipping symlink '{skill_dir.name}' "
                        f"in {child} (expected a real directory)"
                    )
                    continue
                if skill_dir.is_dir() and not skill_dir.name.startswith("."):
                    entry = SkillEntry(
                        name=skill_dir.name,
                        path=skill_dir,
                        scope=SkillScope.PROJECT,
                        project=project_name,
                        source=SkillSource.REPO,
                        description=_read_skill_description(skill_dir),
                    )
                    validation = validate_skill(entry)
                    if not validation.valid:
                        _err.print(
                            f"[yellow]Warning:[/] {'; '.join(validation.errors)}"
                        )
                    entries.append(entry)
        elif (child / "SKILL.md").exists():
            entry = SkillEntry(
                name=child.name,
                path=child,
                scope=SkillScope.GENERAL,
                source=SkillSource.REPO,
                description=_read_skill_description(child),
            )
            validation = validate_skill(entry)
            if not validation.valid:
                _err.print(
                    f"[yellow]Warning:[/] {'; '.join(validation.errors)}"
                )
            entries.append(entry)
        # else: directory with no SKILL.md and no skill children (e.g. assets/) — skip

    return entries


def install_skill(
    skill: SkillEntry,
    claude_skills_dir: Path,
    force_copy: bool = False,
    ctx: DryRunContext | None = None,
) -> InstallResult:
    """
    Install skill into claude_skills_dir. Idempotent.
    Tries symlink first; falls back to copytree on OSError.
    When ctx.dry_run=True, records the planned op and returns the expected result
    without writing anything.
    """
    _ctx = ctx or DryRunContext()
    target = claude_skills_dir / skill.name

    # Safety: refuse to install if target is inside the source skill tree or
    # vice-versa — this would create circular symlinks that corrupt the repo.
    source_resolved = skill.path.resolve()
    target_parent = claude_skills_dir.resolve()
    if str(target_parent).startswith(str(source_resolved.parent) + "/") or str(
        source_resolved
    ).startswith(str(target_parent) + "/"):
        _err.print(
            f"[red]Error:[/] Refusing circular install — target {target_parent} "
            f"overlaps source {source_resolved.parent}"
        )
        return InstallResult.FAILED

    if _ctx.dry_run:
        verb = "copy" if force_copy else "symlink"
        _ctx.record(verb, str(target), str(skill.path.resolve()))
        return InstallResult.COPIED if force_copy else InstallResult.SYMLINKED

    if target.is_symlink():
        target.unlink()
    elif target.exists():
        shutil.rmtree(target)

    if not force_copy:
        try:
            target.symlink_to(skill.path.resolve())
            return InstallResult.SYMLINKED
        except OSError:
            pass

    try:
        shutil.copytree(skill.path, target)
        return InstallResult.COPIED
    except Exception:
        return InstallResult.FAILED


def remove_skill(
    name: str,
    claude_skills_dir: Path,
    reg: Registry,
    ctx: DryRunContext | None = None,
) -> None:
    """
    Remove an installed skill from ~/.claude/skills/ and the registry.

    Raises ValueError if the skill is EXTERNAL (not managed by bm).
    Missing symlink is a warning, not an error — registry is still cleaned up.
    """
    _ctx = ctx or DryRunContext()
    entry = reg.get(name)

    if entry and entry.source == SkillSource.EXTERNAL:
        raise ValueError(
            f"Skill '{name}' is externally installed and not managed by bm. "
            f"Remove it manually from {claude_skills_dir / name}"
        )

    target = claude_skills_dir / name
    _ctx.record("remove", str(target))

    if not _ctx.dry_run:
        if target.is_symlink() or target.exists():
            if target.is_symlink():
                target.unlink()
            else:
                shutil.rmtree(target)
        else:
            _err.print(
                f"[yellow]Warning:[/] {target} not found — removing registry entry only"
            )

    reg.remove(name, ctx=_ctx)
