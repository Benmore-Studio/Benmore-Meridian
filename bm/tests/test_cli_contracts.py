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
