"""Skill and plugin status detection."""

from __future__ import annotations

from pathlib import Path

from bm.models import SkillEntry, SkillStatus


def check_skill_status(skill: SkillEntry, claude_skills_dir: Path) -> SkillStatus:
    target = claude_skills_dir / skill.name
    if target.is_symlink():
        return SkillStatus.SYMLINKED if target.exists() else SkillStatus.BROKEN
    if target.exists():
        return SkillStatus.COPIED
    return SkillStatus.MISSING


def check_plugins(plugins_dir: Path, agents_skills_dir: Path) -> dict[str, bool]:
    return {
        "Superpowers": (plugins_dir / "cache" / "claude-plugins-official").exists(),
        "Double Shot Latte": agents_skills_dir.exists(),
    }
