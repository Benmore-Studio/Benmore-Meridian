"""Local registry: tracks all installed skills in ~/.bm/registry.json."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from bm.models import RegistryEntry, SkillScope, SkillSource


class Registry:
    def __init__(self, registry_file: Path) -> None:
        self._file = registry_file
        self._entries: dict[str, RegistryEntry] = {}
        if registry_file.exists():
            self._load()

    def _load(self) -> None:
        data = json.loads(self._file.read_text())
        for name, d in data.items():
            self._entries[name] = RegistryEntry(
                name=d["name"],
                installed_path=d["installed_path"],
                source=SkillSource(d["source"]),
                scope=SkillScope(d["scope"]),
                project=d.get("project", ""),
                version=d.get("version", "1.0.0"),
                install_method=d.get("install_method", "symlink"),
            )

    def save(self) -> None:
        self._file.parent.mkdir(parents=True, exist_ok=True)
        data = {name: asdict(entry) for name, entry in self._entries.items()}
        self._file.write_text(json.dumps(data, indent=2, default=str))

    def add(self, entry: RegistryEntry) -> None:
        self._entries[entry.name] = entry
        self.save()

    def remove(self, name: str) -> None:
        self._entries.pop(name, None)
        self.save()

    def get(self, name: str) -> RegistryEntry | None:
        return self._entries.get(name)

    def list_all(self) -> list[RegistryEntry]:
        return list(self._entries.values())

    def sync(self, claude_skills_dir: Path, repo_skills_dir: Path | None = None) -> None:
        """
        Scan ~/.claude/skills/ and reconcile registry.
        Detects source: REPO (symlink into repo), MARKETPLACE (symlink into .agents),
        EXTERNAL (plain dir or symlink elsewhere).
        """
        if not claude_skills_dir.exists():
            return

        repo_root = repo_skills_dir.parent if repo_skills_dir else None

        for entry in claude_skills_dir.iterdir():
            if not entry.is_dir() and not entry.is_symlink():
                continue

            name = entry.name
            installed_path = str(entry)

            if entry.is_symlink():
                target = entry.resolve()
                if repo_root and str(target).startswith(str(repo_root)):
                    source = SkillSource.REPO
                elif ".agents" in str(target):
                    source = SkillSource.MARKETPLACE
                else:
                    source = SkillSource.EXTERNAL
                install_method = "symlink"
            else:
                source = SkillSource.EXTERNAL
                install_method = "copy"

            if name not in self._entries:
                self._entries[name] = RegistryEntry(
                    name=name,
                    installed_path=installed_path,
                    source=source,
                    scope=SkillScope.GENERAL,
                    install_method=install_method,
                )

        self.save()
