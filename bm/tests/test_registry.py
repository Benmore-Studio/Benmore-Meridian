from pathlib import Path

from bm.models import RegistryEntry, SkillScope, SkillSource
from bm.registry import Registry


def test_registry_empty_on_first_load(tmp_path: Path) -> None:
    reg = Registry(tmp_path / "registry.json")
    assert reg.list_all() == []


def test_registry_add_and_get(tmp_path: Path) -> None:
    reg = Registry(tmp_path / "registry.json")
    entry = RegistryEntry(
        name="vercel-cli",
        installed_path=str(tmp_path / "vercel-cli"),
        source=SkillSource.REPO,
        scope=SkillScope.GENERAL,
    )
    reg.add(entry)
    assert reg.get("vercel-cli") is not None
    assert reg.get("vercel-cli").name == "vercel-cli"  # type: ignore[union-attr]


def test_registry_persists(tmp_path: Path) -> None:
    path = tmp_path / "registry.json"
    reg = Registry(path)
    reg.add(
        RegistryEntry(
            name="pdf",
            installed_path="/tmp/pdf",
            source=SkillSource.MARKETPLACE,
            scope=SkillScope.GENERAL,
        )
    )
    reg.save()

    reg2 = Registry(path)
    assert reg2.get("pdf") is not None


def test_registry_remove(tmp_path: Path) -> None:
    reg = Registry(tmp_path / "registry.json")
    reg.add(
        RegistryEntry(
            name="tickets",
            installed_path="/tmp/tickets",
            source=SkillSource.REPO,
            scope=SkillScope.GENERAL,
        )
    )
    reg.remove("tickets")
    assert reg.get("tickets") is None


def test_registry_sync_detects_external(tmp_path: Path) -> None:
    claude_skills = tmp_path / ".claude" / "skills"
    claude_skills.mkdir(parents=True)
    external = claude_skills / "my-custom-skill"
    external.mkdir()
    (external / "SKILL.md").write_text("---\nname: my-custom-skill\n---\n")

    reg = Registry(tmp_path / "registry.json")
    reg.sync(claude_skills, repo_skills_dir=tmp_path / "skills")
    entry = reg.get("my-custom-skill")
    assert entry is not None
    assert entry.source == SkillSource.EXTERNAL
