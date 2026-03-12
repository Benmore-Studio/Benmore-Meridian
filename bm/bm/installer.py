"""Skill discovery and installation (symlink-first, copy fallback)."""
from __future__ import annotations

import shutil
from pathlib import Path

from bm.models import InstallResult, SkillEntry, SkillScope, SkillSource


def _read_skill_description(skill_path: Path) -> str:
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return ""
    for line in skill_md.read_text().splitlines():
        if line.startswith("description:"):
            return line.split(":", 1)[1].strip().strip('"')
    return ""


def discover_skills(
    skills_dir: Path,
    pcs_subdir: str = "pcs",
) -> list[SkillEntry]:
    """
    Return SkillEntry list from skills_dir.
    Flattens skills/pcs/* -> project-scoped entries named "pcs-{x}".
    Skips hidden entries and README files.
    """
    entries: list[SkillEntry] = []

    for child in sorted(skills_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        if child.name == pcs_subdir:
            for pcs_child in sorted(child.iterdir()):
                if pcs_child.is_dir() and not pcs_child.name.startswith("."):
                    entries.append(SkillEntry(
                        name=pcs_child.name,
                        path=pcs_child,
                        scope=SkillScope.PROJECT,
                        project=pcs_subdir,
                        source=SkillSource.REPO,
                        description=_read_skill_description(pcs_child),
                    ))
        else:
            entries.append(SkillEntry(
                name=child.name,
                path=child,
                scope=SkillScope.GENERAL,
                source=SkillSource.REPO,
                description=_read_skill_description(child),
            ))

    return entries


def install_skill(
    skill: SkillEntry,
    claude_skills_dir: Path,
    force_copy: bool = False,
) -> InstallResult:
    """
    Install skill into claude_skills_dir. Idempotent.
    Tries symlink; falls back to copytree on OSError.
    """
    target = claude_skills_dir / skill.name

    if target.is_symlink() or target.exists():
        if target.is_symlink():
            target.unlink()
        else:
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
