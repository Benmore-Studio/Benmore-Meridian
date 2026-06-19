"""Local registry: tracks all installed skills in ~/.bm/registry.json."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from bm.dryrun import DryRunContext
from bm.models import InstallMethod, RegistryEntry, SkillScope, SkillSource


class Registry:
    def __init__(self, registry_file: Path) -> None:
        self._file = registry_file
        self._entries: dict[str, RegistryEntry] = {}
        if registry_file.exists():
            self._load()

    def _load(self) -> None:
        data = json.loads(self._file.read_text())
        for name, d in data.items():
            self._entries[name] = RegistryEntry.from_dict(d)

    def save(self) -> None:
        """Persist registry to disk. Call explicitly after batch operations."""
        self._file.parent.mkdir(parents=True, exist_ok=True)
        data = {name: asdict(entry) for name, entry in self._entries.items()}
        self._file.write_text(json.dumps(data, indent=2, default=str))

    def add(self, entry: RegistryEntry) -> None:
        """Add or update one entry. Does NOT auto-save; call save() when done."""
        self._entries[entry.name] = entry

    def batch_add(self, entries: list[RegistryEntry], ctx: DryRunContext | None = None) -> None:
        """Add multiple entries and save once. Records ops if ctx.dry_run=True."""
        _ctx = ctx or DryRunContext()
        for entry in entries:
            _ctx.record("registry_add", entry.name)
            if not _ctx.dry_run:
                self._entries[entry.name] = entry
        if not _ctx.dry_run:
            self.save()

    def remove(self, name: str, ctx: DryRunContext | None = None) -> None:
        _ctx = ctx or DryRunContext()
        _ctx.record("registry_remove", name)
        if not _ctx.dry_run:
            self._entries.pop(name, None)
            self.save()

    def get(self, name: str) -> RegistryEntry | None:
        return self._entries.get(name)

    def list_all(self) -> list[RegistryEntry]:
        return list(self._entries.values())

    def sync(
        self,
        claude_skills_dir: Path,
        repo_skills_dir: Path | None = None,
        ctx: DryRunContext | None = None,
    ) -> None:
        """
        Scan ~/.claude/skills/ and reconcile registry.
        Detects source: REPO (symlink into repo), MARKETPLACE (symlink into .agents),
        EXTERNAL (plain dir or symlink elsewhere).
        Always updates install_method and source for existing entries.
        """
        _ctx = ctx or DryRunContext()
        if not claude_skills_dir.exists():
            return

        repo_root = repo_skills_dir.parent if repo_skills_dir else None
        updated: dict[str, RegistryEntry] = {}

        for entry_path in claude_skills_dir.iterdir():
            if not entry_path.is_dir() and not entry_path.is_symlink():
                continue

            name = entry_path.name

            if entry_path.is_symlink():
                target = entry_path.resolve()
                if repo_root and str(target).startswith(str(repo_root)):
                    source = SkillSource.REPO
                elif ".agents" in str(target):
                    source = SkillSource.MARKETPLACE
                else:
                    source = SkillSource.EXTERNAL
                install_method = InstallMethod.SYMLINK
            else:
                source = SkillSource.EXTERNAL
                install_method = InstallMethod.EXTERNAL

            existing = self._entries.get(name)
            new_entry = RegistryEntry(
                name=name,
                installed_path=str(entry_path),
                source=source,
                # preserve user-set scope/project/version if already known
                scope=existing.scope if existing else SkillScope.GENERAL,
                project=existing.project if existing else "",
                version=existing.version if existing else "1.0.0",
                install_method=install_method,
            )
            verb = "registry_add" if name not in self._entries else "registry_update"
            _ctx.record(verb, name)
            updated[name] = new_entry

        if not _ctx.dry_run:
            self._entries.update(updated)
            self.save()
