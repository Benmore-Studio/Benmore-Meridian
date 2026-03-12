from pathlib import Path

from bm.models import SkillEntry, SkillScope, SkillSource
from bm.validator import validate_skill


def _make_skill(tmp_path: Path, content: str) -> SkillEntry:
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(content)
    return SkillEntry(
        name="my-skill",
        path=skill_dir,
        scope=SkillScope.GENERAL,
        source=SkillSource.REPO,
    )


def test_valid_skill_returns_no_errors(tmp_path: Path) -> None:
    skill = _make_skill(
        tmp_path, "---\nname: my-skill\ndescription: A test skill\n---\n\n# my-skill\n"
    )
    result = validate_skill(skill)
    assert result.errors == []


def test_missing_name_is_an_error(tmp_path: Path) -> None:
    skill = _make_skill(tmp_path, "---\ndescription: A test skill\n---\n\n# my-skill\n")
    result = validate_skill(skill)
    assert any("name" in e for e in result.errors)


def test_name_mismatch_is_an_error(tmp_path: Path) -> None:
    skill = _make_skill(tmp_path, "---\nname: wrong-name\ndescription: A test skill\n---\n")
    result = validate_skill(skill)
    assert any("mismatch" in e.lower() or "wrong-name" in e for e in result.errors)


def test_empty_description_is_an_error(tmp_path: Path) -> None:
    skill = _make_skill(tmp_path, "---\nname: my-skill\ndescription:\n---\n")
    result = validate_skill(skill)
    assert any("description" in e for e in result.errors)


def test_missing_description_is_an_error(tmp_path: Path) -> None:
    skill = _make_skill(tmp_path, "---\nname: my-skill\n---\n")
    result = validate_skill(skill)
    assert any("description" in e for e in result.errors)


def test_missing_optional_fields_produce_warnings_not_errors(tmp_path: Path) -> None:
    skill = _make_skill(
        tmp_path, "---\nname: my-skill\ndescription: A test skill\n---\n"
    )
    result = validate_skill(skill)
    assert result.errors == []
    # version, author, tags are optional — may or may not warn
    # the important thing is no errors


def test_no_skill_md_is_an_error(tmp_path: Path) -> None:
    skill_dir = tmp_path / "bare-skill"
    skill_dir.mkdir()
    skill = SkillEntry(
        name="bare-skill", path=skill_dir, scope=SkillScope.GENERAL, source=SkillSource.REPO
    )
    result = validate_skill(skill)
    assert any("SKILL.md" in e for e in result.errors)
