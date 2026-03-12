from pathlib import Path

import pytest

from bm.dryrun import DryRunContext
from bm.installer import discover_skills, install_skill, remove_skill
from bm.models import InstallMethod, InstallResult, RegistryEntry, SkillScope, SkillSource
from bm.registry import Registry


def test_discover_finds_top_level(tmp_skills_dir):
    skills = discover_skills(tmp_skills_dir)
    names = [e.name for e in skills]
    assert "vercel-cli" in names and "pdf" in names


def test_discover_flattens_pcs(tmp_skills_dir):
    skills = discover_skills(tmp_skills_dir)
    names = [e.name for e in skills]
    assert "pcs-migration" in names
    assert "pcs" not in names  # pcs/ dir itself not included


def test_discover_pcs_is_project_scoped(tmp_skills_dir):
    skills = discover_skills(tmp_skills_dir)
    pcs = next(e for e in skills if e.name == "pcs-migration")
    assert pcs.scope == SkillScope.PROJECT
    assert pcs.project == "pcs"


def test_install_creates_symlink(tmp_skills_dir, tmp_claude_skills):
    skill = next(e for e in discover_skills(tmp_skills_dir) if e.name == "vercel-cli")
    result = install_skill(skill, tmp_claude_skills)
    assert result == InstallResult.SYMLINKED
    assert (tmp_claude_skills / "vercel-cli").is_symlink()


def test_install_force_copy(tmp_skills_dir, tmp_claude_skills):
    skill = next(e for e in discover_skills(tmp_skills_dir) if e.name == "pdf")
    result = install_skill(skill, tmp_claude_skills, force_copy=True)
    assert result == InstallResult.COPIED
    assert not (tmp_claude_skills / "pdf").is_symlink()


def test_install_idempotent(tmp_skills_dir, tmp_claude_skills):
    skill = next(e for e in discover_skills(tmp_skills_dir) if e.name == "tickets")
    install_skill(skill, tmp_claude_skills)
    result = install_skill(skill, tmp_claude_skills)
    assert result in (InstallResult.SYMLINKED, InstallResult.COPIED)


def test_install_skill_dry_run_records_op_but_does_not_write(
    tmp_skills_dir: Path, tmp_claude_skills: Path
) -> None:
    skills = discover_skills(tmp_skills_dir)
    assert skills  # at least one skill discovered
    skill = skills[0]

    ctx = DryRunContext(dry_run=True)
    result = install_skill(skill, tmp_claude_skills, ctx=ctx)

    # Nothing written
    assert not (tmp_claude_skills / skill.name).exists()
    # Op recorded
    assert len(ctx.ops) == 1
    assert ctx.ops[0].verb in ("symlink", "copy")
    assert skill.name in ctx.ops[0].target
    # Result still returned for caller awareness
    assert result in (InstallResult.SYMLINKED, InstallResult.COPIED)


def test_remove_skill_deletes_symlink_and_registry_entry(
    tmp_skills_dir: Path, tmp_claude_skills: Path, tmp_path: Path
) -> None:
    skills = discover_skills(tmp_skills_dir)
    skill = skills[0]
    # Install first
    install_skill(skill, tmp_claude_skills)
    assert (tmp_claude_skills / skill.name).exists()

    reg_file = tmp_path / "registry.json"
    reg = Registry(reg_file)
    reg.add(
        RegistryEntry(
            name=skill.name,
            installed_path=str(tmp_claude_skills / skill.name),
            source=SkillSource.REPO,
            scope=SkillScope.GENERAL,
            install_method=InstallMethod.SYMLINK,
        )
    )
    reg.save()

    ctx = DryRunContext(dry_run=False)
    remove_skill(skill.name, tmp_claude_skills, reg, ctx)

    assert not (tmp_claude_skills / skill.name).exists()
    assert reg.get(skill.name) is None


def test_remove_skill_dry_run_records_ops_only(
    tmp_skills_dir: Path, tmp_claude_skills: Path, tmp_path: Path
) -> None:
    skills = discover_skills(tmp_skills_dir)
    skill = skills[0]
    install_skill(skill, tmp_claude_skills)

    reg_file = tmp_path / "registry.json"
    reg = Registry(reg_file)
    reg.add(
        RegistryEntry(
            name=skill.name,
            installed_path=str(tmp_claude_skills / skill.name),
            source=SkillSource.REPO,
            scope=SkillScope.GENERAL,
            install_method=InstallMethod.SYMLINK,
        )
    )
    reg.save()

    ctx = DryRunContext(dry_run=True)
    remove_skill(skill.name, tmp_claude_skills, reg, ctx)

    # Nothing changed
    assert (tmp_claude_skills / skill.name).exists()
    assert reg.get(skill.name) is not None
    # Ops recorded
    assert any(op.verb == "remove" for op in ctx.ops)
    assert any(op.verb == "registry_remove" for op in ctx.ops)


def test_remove_skill_warns_when_target_already_missing(
    tmp_skills_dir: Path,
    tmp_claude_skills: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Should not raise if symlink already gone — just removes registry entry."""
    skill_name = "phantom-skill"
    reg_file = tmp_path / "registry.json"
    reg = Registry(reg_file)
    reg.add(
        RegistryEntry(
            name=skill_name,
            installed_path=str(tmp_claude_skills / skill_name),
            source=SkillSource.REPO,
            scope=SkillScope.GENERAL,
            install_method=InstallMethod.SYMLINK,
        )
    )
    reg.save()

    ctx = DryRunContext(dry_run=False)
    remove_skill(skill_name, tmp_claude_skills, reg, ctx)  # should not raise
    assert reg.get(skill_name) is None


def test_remove_skill_raises_for_external_skill(
    tmp_claude_skills: Path, tmp_path: Path
) -> None:
    skill_name = "external-skill"
    reg_file = tmp_path / "registry.json"
    reg = Registry(reg_file)
    reg.add(
        RegistryEntry(
            name=skill_name,
            installed_path=str(tmp_claude_skills / skill_name),
            source=SkillSource.EXTERNAL,
            scope=SkillScope.GENERAL,
            install_method=InstallMethod.EXTERNAL,
        )
    )
    reg.save()

    with pytest.raises(ValueError, match="external"):
        remove_skill(skill_name, tmp_claude_skills, reg, DryRunContext())
