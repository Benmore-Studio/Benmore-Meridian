import json
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
        },
        installed_file=tmp_path / "installed_plugins.json",
    )
    assert all(isinstance(v, bool) for v in result.values())
    assert not result["Superpowers"]
    assert not result["Double Shot Latte"]


def _write_registry(path: Path, plugins: dict[str, list[dict[str, str]]]) -> Path:
    path.write_text(json.dumps({"version": 2, "plugins": plugins}))
    return path


def test_plugin_status_reads_registry_from_any_marketplace(tmp_path: Path) -> None:
    registry = _write_registry(
        tmp_path / "installed_plugins.json",
        {
            "superpowers@superpowers-marketplace": [{"scope": "user"}],
            "compound-engineering@compound-engineering-plugin": [{"scope": "user"}],
        },
    )
    result = get_plugin_status(
        markers={
            "Superpowers": tmp_path / "missing-a",
            "Double Shot Latte": tmp_path / "missing-b",
        },
        installed_file=registry,
    )
    assert result == {"Superpowers": True, "Double Shot Latte": True}


def test_plugin_status_registry_overrides_stale_marker(tmp_path: Path) -> None:
    marker = tmp_path / "agents-skills"
    marker.mkdir()
    registry = _write_registry(
        tmp_path / "installed_plugins.json",
        {"superpowers@claude-plugins-official": [{"scope": "user"}], "other@x": []},
    )
    result = get_plugin_status(
        markers={"Superpowers": tmp_path / "missing", "Double Shot Latte": marker},
        installed_file=registry,
    )
    assert result == {"Superpowers": True, "Double Shot Latte": False}


def test_plugin_status_falls_back_to_markers_on_bad_registry(tmp_path: Path) -> None:
    marker = tmp_path / "present"
    marker.mkdir()
    registry = tmp_path / "installed_plugins.json"
    registry.write_text("{not json")
    result = get_plugin_status(
        markers={"Superpowers": marker, "Double Shot Latte": tmp_path / "missing"},
        installed_file=registry,
    )
    assert result == {"Superpowers": True, "Double Shot Latte": False}
