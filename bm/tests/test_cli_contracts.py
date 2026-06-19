"""CLI smoke tests for public JSON contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

import bm.cli as cli
from bm.models import InstallMethod, RegistryEntry, SkillScope, SkillSource
from bm.registry import Registry

runner = CliRunner()


def _skill(root: Path, name: str, *, valid: bool = True) -> None:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    if valid:
        frontmatter = f"---\nname: {name}\ndescription: {name} skill\n---\n"
    else:
        frontmatter = "---\ndescription: Missing matching name\n---\n"
    (skill_dir / "SKILL.md").write_text(frontmatter, encoding="utf-8")


def _trigger_skill(root: Path, name: str, trigger: str) -> None:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {name} skill\ntriggers:\n  - {trigger}\n---\n",
        encoding="utf-8",
    )


def test_status_json_stdout_is_valid_when_validation_warns(
    tmp_path: Path, monkeypatch: Any
) -> None:
    skills_dir = tmp_path / "skills"
    claude_dir = tmp_path / ".claude" / "skills"
    skills_dir.mkdir()
    claude_dir.mkdir(parents=True)
    _skill(skills_dir, "valid-skill")
    _skill(skills_dir, "invalid-skill", valid=False)

    monkeypatch.setattr(cli, "SKILLS_DIR", skills_dir)
    monkeypatch.setattr(cli, "CLAUDE_SKILLS_DIR", claude_dir)

    result = runner.invoke(cli.app, ["status", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert [item["name"] for item in payload] == ["invalid-skill", "valid-skill"]
    assert "Warning" not in result.stdout


def test_registry_list_json_preserves_public_fields(tmp_path: Path, monkeypatch: Any) -> None:
    registry_file = tmp_path / "registry.json"
    reg = Registry(registry_file)
    reg.add(
        RegistryEntry(
            name="demo",
            installed_path=str(tmp_path / "demo"),
            source=SkillSource.REPO,
            scope=SkillScope.GENERAL,
            install_method=InstallMethod.SYMLINK,
        )
    )
    reg.save()
    monkeypatch.setattr(cli, "REGISTRY_FILE", registry_file)

    result = runner.invoke(cli.app, ["registry", "list", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == [
        {
            "name": "demo",
            "installed_path": str(tmp_path / "demo"),
            "source": "repo",
            "scope": "general",
            "project": "",
            "version": "1.0.0",
            "install_method": "symlink",
        }
    ]


def test_schema_json_prints_deterministic_contract() -> None:
    result = runner.invoke(cli.app, ["schema", "json", "status"])

    assert result.exit_code == 0
    schema = json.loads(result.stdout)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["items"]["required"] == ["name", "status", "scope", "project"]


def test_schema_openapi_contains_benmore_models() -> None:
    result = runner.invoke(cli.app, ["schema", "openapi"])

    assert result.exit_code == 0
    openapi = json.loads(result.stdout)
    assert openapi["openapi"] == "3.1.0"
    assert "/projects/" in openapi["paths"]
    assert "Project" in openapi["components"]["schemas"]


def test_uninstall_all_removes_bm_managed_skills(tmp_path: Path, monkeypatch: Any) -> None:
    claude_dir = tmp_path / ".claude" / "skills"
    registry_file = tmp_path / "registry.json"
    claude_dir.mkdir(parents=True)
    installed = claude_dir / "demo"
    installed.mkdir()
    (installed / "SKILL.md").write_text("---\nname: demo\ndescription: Demo\n---\n")
    external = claude_dir / "external"
    external.mkdir()

    reg = Registry(registry_file)
    reg.add(
        RegistryEntry(
            name="demo",
            installed_path=str(installed),
            source=SkillSource.REPO,
            scope=SkillScope.GENERAL,
            install_method=InstallMethod.COPY,
        )
    )
    reg.add(
        RegistryEntry(
            name="external",
            installed_path=str(external),
            source=SkillSource.EXTERNAL,
            scope=SkillScope.GENERAL,
            install_method=InstallMethod.EXTERNAL,
        )
    )
    reg.save()

    monkeypatch.setattr(cli, "CLAUDE_SKILLS_DIR", claude_dir)
    monkeypatch.setattr(cli, "REGISTRY_FILE", registry_file)

    result = runner.invoke(cli.app, ["uninstall", "--all", "--yes"])

    assert result.exit_code == 0
    assert not installed.exists()
    assert external.exists()
    synced = Registry(registry_file)
    assert synced.get("demo") is None
    assert synced.get("external") is not None


def test_suggest_install_and_cache(tmp_path: Path, monkeypatch: Any) -> None:
    skills_dir = tmp_path / "skills"
    claude_dir = tmp_path / ".claude" / "skills"
    registry_file = tmp_path / "registry.json"
    cache_file = tmp_path / "suggestions.json"
    project_dir = tmp_path / "project"
    skills_dir.mkdir()
    claude_dir.mkdir(parents=True)
    project_dir.mkdir()
    (project_dir / "manage.py").write_text("# django marker\n")
    _trigger_skill(skills_dir, "django-production", "django")

    monkeypatch.setattr(cli, "SKILLS_DIR", skills_dir)
    monkeypatch.setattr(cli, "CLAUDE_SKILLS_DIR", claude_dir)
    monkeypatch.setattr(cli, "REGISTRY_FILE", registry_file)
    monkeypatch.setattr(cli, "SUGGESTION_CACHE_FILE", cache_file)

    result = runner.invoke(
        cli.app, ["suggest", str(project_dir), "--top", "4", "--cache", "--install"]
    )

    assert result.exit_code == 0
    assert (claude_dir / "django-production").exists()
    assert Registry(registry_file).get("django-production") is not None
    cached = json.loads(cache_file.read_text(encoding="utf-8"))
    assert cached[0]["name"] == "django-production"


def test_suggest_intent_installs_and_caches_seo_skills(tmp_path: Path, monkeypatch: Any) -> None:
    skills_dir = tmp_path / "skills"
    claude_dir = tmp_path / ".claude" / "skills"
    registry_file = tmp_path / "registry.json"
    cache_file = tmp_path / "suggestions.json"
    project_dir = tmp_path / "project"
    skills_dir.mkdir()
    claude_dir.mkdir(parents=True)
    project_dir.mkdir()
    for name in ["ai-seo", "seo-audit", "programmatic-seo", "site-capture", "pdf"]:
        _skill(skills_dir, name)

    monkeypatch.setattr(cli, "SKILLS_DIR", skills_dir)
    monkeypatch.setattr(cli, "CLAUDE_SKILLS_DIR", claude_dir)
    monkeypatch.setattr(cli, "REGISTRY_FILE", registry_file)
    monkeypatch.setattr(cli, "SUGGESTION_CACHE_FILE", cache_file)

    result = runner.invoke(
        cli.app,
        [
            "suggest",
            str(project_dir),
            "--intent",
            "improve seo",
            "--top",
            "4",
            "--install",
            "--cache",
        ],
    )

    assert result.exit_code == 0
    cached = json.loads(cache_file.read_text(encoding="utf-8"))
    names = [item["name"] for item in cached]
    assert names == ["ai-seo", "seo-audit", "programmatic-seo", "site-capture"]
    for name in names:
        assert (claude_dir / name).exists()
        assert Registry(registry_file).get(name) is not None


def test_suggest_json_no_matches_outputs_empty_array(tmp_path: Path, monkeypatch: Any) -> None:
    skills_dir = tmp_path / "skills"
    claude_dir = tmp_path / ".claude" / "skills"
    project_dir = tmp_path / "project"
    skills_dir.mkdir()
    claude_dir.mkdir(parents=True)
    project_dir.mkdir()

    monkeypatch.setattr(cli, "SKILLS_DIR", skills_dir)
    monkeypatch.setattr(cli, "CLAUDE_SKILLS_DIR", claude_dir)

    result = runner.invoke(cli.app, ["suggest", str(project_dir), "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == []


def test_suggest_surfaces_security_and_compliance_skills(tmp_path: Path, monkeypatch: Any) -> None:
    skills_dir = tmp_path / "skills"
    claude_dir = tmp_path / ".claude" / "skills"
    project_dir = tmp_path / "project"
    skills_dir.mkdir()
    claude_dir.mkdir(parents=True)
    project_dir.mkdir()
    (project_dir / "README.md").write_text(
        "Healthcare platform with HIPAA, SOC 2, PHI access, audit logs, MFA, and tenant isolation.",
        encoding="utf-8",
    )
    _skill(skills_dir, "hipaa-compliance-guard")
    _skill(skills_dir, "security-compliance-audit")
    _skill(skills_dir, "healthcare-audit-logger")
    _skill(skills_dir, "multi-tenant-guard")

    monkeypatch.setattr(cli, "SKILLS_DIR", skills_dir)
    monkeypatch.setattr(cli, "CLAUDE_SKILLS_DIR", claude_dir)

    result = runner.invoke(cli.app, ["suggest", str(project_dir), "--top", "4", "--json"])

    assert result.exit_code == 0
    names = {item["name"] for item in json.loads(result.stdout)}
    assert "hipaa-compliance-guard" in names
    assert "security-compliance-audit" in names
    assert "multi-tenant-guard" in names


def test_context_global_json_includes_catalog(tmp_path: Path, monkeypatch: Any) -> None:
    skills_dir = tmp_path / "skills"
    claude_dir = tmp_path / ".claude" / "skills"
    project_dir = tmp_path / "project"
    skills_dir.mkdir()
    claude_dir.mkdir(parents=True)
    project_dir.mkdir()
    (project_dir / "README.md").write_text("HIPAA audit trail project", encoding="utf-8")
    _skill(skills_dir, "hipaa-compliance-guard")
    _skill(skills_dir, "django-production")

    monkeypatch.setattr(cli, "SKILLS_DIR", skills_dir)
    monkeypatch.setattr(cli, "CLAUDE_SKILLS_DIR", claude_dir)

    result = runner.invoke(cli.app, ["context", str(project_dir), "--global", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["path"] == str(project_dir.resolve())
    assert "recommended_skills" in payload
    assert payload["skill_catalog"]["Security & Compliance"] == ["hipaa-compliance-guard"]
    assert payload["skill_catalog"]["Backend"] == ["django-production"]
