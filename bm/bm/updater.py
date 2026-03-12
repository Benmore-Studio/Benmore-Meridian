"""git pull + reinstall."""

from __future__ import annotations

import subprocess
from pathlib import Path

from bm.config import CLAUDE_SKILLS_DIR, REPO_ROOT, SKILLS_DIR
from bm.installer import discover_skills, install_skill
from bm.models import InstallResult


def git_pull(repo_root: Path = REPO_ROOT) -> tuple[bool, str]:
    r = subprocess.run(
        ["git", "pull", "--ff-only"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    return r.returncode == 0, r.stdout + r.stderr


def reinstall_all(
    skills_dir: Path = SKILLS_DIR,
    claude_skills_dir: Path = CLAUDE_SKILLS_DIR,
    force_copy: bool = False,
) -> dict[str, InstallResult]:
    return {
        skill.name: install_skill(skill, claude_skills_dir, force_copy=force_copy)
        for skill in discover_skills(skills_dir)
    }
