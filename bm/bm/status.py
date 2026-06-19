"""Skill status detection."""

from __future__ import annotations

from pathlib import Path

from bm.core import path_status
from bm.models import SkillEntry, SkillStatus


def check_skill_status(skill: SkillEntry, claude_skills_dir: Path) -> SkillStatus:
    target = claude_skills_dir / skill.name
    return SkillStatus(path_status(target))
