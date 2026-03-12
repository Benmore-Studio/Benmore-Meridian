"""Tests for bm data models."""

from pathlib import Path

from bm.models import (
    InstallResult,
    RegistryEntry,
    SkillEntry,
    SkillScope,
    SkillSource,
    SkillStatus,
)


def test_skill_entry_defaults() -> None:
    entry = SkillEntry(name="vercel-cli", path=Path("/skills/vercel-cli"))
    assert entry.scope == SkillScope.GENERAL
    assert entry.source == SkillSource.REPO
    assert not entry.is_project_skill


def test_skill_entry_project_scope() -> None:
    entry = SkillEntry(
        name="pcs-migration",
        path=Path("/skills/pcs/pcs-migration"),
        scope=SkillScope.PROJECT,
        project="pcs",
    )
    assert entry.is_project_skill
    assert entry.project == "pcs"


def test_skill_status_enum_values() -> None:
    assert SkillStatus.SYMLINKED.value == "symlinked"
    assert SkillStatus.BROKEN.value == "broken"
    assert SkillStatus.MISSING.value == "missing"
    assert SkillStatus.COPIED.value == "copied"


def test_install_result_enum_values() -> None:
    assert InstallResult.SYMLINKED.value == "symlinked"
    assert InstallResult.FAILED.value == "failed"
    assert InstallResult.COPIED.value == "copied"
    assert InstallResult.SKIPPED.value == "skipped"


def test_registry_entry_serializable() -> None:
    entry = RegistryEntry(
        name="vercel-cli",
        installed_path="/Users/test/.claude/skills/vercel-cli",
        source=SkillSource.REPO,
        scope=SkillScope.GENERAL,
    )
    assert isinstance(entry.installed_path, str)
    assert entry.install_method == "symlink"


def test_skill_source_values() -> None:
    assert SkillSource.REPO.value == "repo"
    assert SkillSource.MARKETPLACE.value == "marketplace"
    assert SkillSource.EXTERNAL.value == "external"
