"""Skill discovery and installation (symlink-first, copy fallback)."""

from __future__ import annotations

import shutil
from pathlib import Path

from bm.models import InstallResult, SkillEntry, SkillScope, SkillSource


def _read_skill_description(skill_path: Path) -> str:
    """Read 'description:' from SKILL.md frontmatter. Returns empty string if absent."""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return ""
    for line in skill_md.read_text().splitlines():
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

        if _is_project_dir(child):
            project_name = child.name
            for skill_dir in sorted(child.iterdir()):
                if skill_dir.is_dir() and not skill_dir.name.startswith("."):
                    entries.append(
                        SkillEntry(
                            name=skill_dir.name,
                            path=skill_dir,
                            scope=SkillScope.PROJECT,
                            project=project_name,
                            source=SkillSource.REPO,
                            description=_read_skill_description(skill_dir),
                        )
                    )
        elif (child / "SKILL.md").exists():
            entries.append(
                SkillEntry(
                    name=child.name,
                    path=child,
                    scope=SkillScope.GENERAL,
                    source=SkillSource.REPO,
                    description=_read_skill_description(child),
                )
            )
        # else: directory with no SKILL.md and no skill children (e.g. assets/) — skip

    return entries


def install_skill(
    skill: SkillEntry,
    claude_skills_dir: Path,
    force_copy: bool = False,
) -> InstallResult:
    """
    Install skill into claude_skills_dir. Idempotent.
    Tries symlink first; falls back to copytree on OSError.
    """
    target = claude_skills_dir / skill.name

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
