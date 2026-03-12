from bm.installer import discover_skills, install_skill
from bm.models import InstallResult, SkillScope


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
