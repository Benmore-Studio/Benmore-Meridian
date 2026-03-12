"""Shared pytest fixtures for bm tests."""

from pathlib import Path

import pytest


@pytest.fixture
def tmp_skills_dir(tmp_path: Path) -> Path:
    """Create a temporary skills directory with fake skills."""
    skills = tmp_path / "skills"
    skills.mkdir()
    for name in ["vercel-cli", "pdf", "tickets"]:
        skill_dir = skills / name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Test skill {name}\n---\n# {name}\n"
        )
    # PCS subdirectory
    pcs = skills / "pcs"
    pcs.mkdir()
    pcs_skill = pcs / "pcs-migration"
    pcs_skill.mkdir()
    (pcs_skill / "SKILL.md").write_text(
        "---\nname: pcs-migration\n"
        "description: Create Alembic migrations for PCS\n---\n# PCS Migration\n"
    )
    return skills


@pytest.fixture
def tmp_claude_skills(tmp_path: Path) -> Path:
    """Create a temporary ~/.claude/skills directory."""
    claude_skills = tmp_path / ".claude" / "skills"
    claude_skills.mkdir(parents=True)
    return claude_skills
