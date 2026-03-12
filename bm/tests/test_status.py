import shutil
from pathlib import Path

from bm.models import SkillEntry, SkillStatus
from bm.plugins import get_plugin_status
from bm.status import check_skill_status


def _make_skill(tmp_path: Path, name: str = "vercel-cli") -> SkillEntry:
    skill_dir = tmp_path / "skills" / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(f"---\nname: {name}\n---\n")
    return SkillEntry(name=name, path=skill_dir)


def test_status_symlinked(tmp_path: Path) -> None:
    skill = _make_skill(tmp_path)
    claude = tmp_path / ".claude" / "skills"
    claude.mkdir(parents=True)
    (claude / skill.name).symlink_to(skill.path.resolve())
    assert check_skill_status(skill, claude) == SkillStatus.SYMLINKED


def test_status_copied(tmp_path: Path) -> None:
    skill = _make_skill(tmp_path)
    claude = tmp_path / ".claude" / "skills"
    claude.mkdir(parents=True)
    shutil.copytree(skill.path, claude / skill.name)
    assert check_skill_status(skill, claude) == SkillStatus.COPIED


def test_status_missing(tmp_path: Path) -> None:
    skill = _make_skill(tmp_path)
    claude = tmp_path / ".claude" / "skills"
    claude.mkdir(parents=True)
    assert check_skill_status(skill, claude) == SkillStatus.MISSING


def test_status_broken_symlink(tmp_path: Path) -> None:
    skill = _make_skill(tmp_path)
    claude = tmp_path / ".claude" / "skills"
    claude.mkdir(parents=True)
    (claude / skill.name).symlink_to("/nonexistent/path")
    assert check_skill_status(skill, claude) == SkillStatus.BROKEN


def test_get_plugin_status_returns_dict(tmp_path: Path) -> None:
    # Provide non-existent paths — both plugins will show as not installed
    result = get_plugin_status(
        markers={
            "Superpowers": tmp_path / "plugins",
            "Double Shot Latte": tmp_path / "agents",
        }
    )
    assert all(isinstance(v, bool) for v in result.values())
    assert not result["Superpowers"]
    assert not result["Double Shot Latte"]
