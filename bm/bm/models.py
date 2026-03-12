"""Core data models for bm — enums and dataclasses only."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class SkillScope(StrEnum):
    """Whether a skill is universal or tied to a specific project."""

    GENERAL = "general"
    PROJECT = "project"


class SkillSource(StrEnum):
    """Where a skill came from."""

    REPO = "repo"
    MARKETPLACE = "marketplace"
    EXTERNAL = "external"


class InstallResult(StrEnum):
    """Result of installing a skill."""

    SYMLINKED = "symlinked"
    COPIED = "copied"
    FAILED = "failed"
    SKIPPED = "skipped"


class InstallMethod(StrEnum):
    """How a skill was installed into ~/.claude/skills/."""

    SYMLINK = "symlink"
    COPY = "copy"
    EXTERNAL = "external"
    NONE = "none"


class SkillStatus(StrEnum):
    """Current installation status of a skill."""

    SYMLINKED = "symlinked"
    COPIED = "copied"
    MISSING = "missing"
    BROKEN = "broken"


@dataclass
class SkillEntry:
    """A skill discovered in the repository."""

    name: str
    path: Path
    scope: SkillScope = SkillScope.GENERAL
    project: str = ""
    source: SkillSource = SkillSource.REPO
    version: str = "1.0.0"
    description: str = ""

    @property
    def is_project_skill(self) -> bool:
        """True if this skill is scoped to a specific project."""
        return self.scope == SkillScope.PROJECT


@dataclass
class RegistryEntry:
    """A skill tracked in the local registry."""

    name: str
    installed_path: str  # str so JSON-serializable
    source: SkillSource
    scope: SkillScope
    project: str = ""
    version: str = "1.0.0"
    install_method: InstallMethod = InstallMethod.SYMLINK

    @classmethod
    def from_dict(cls, d: dict[str, str]) -> RegistryEntry:
        """Deserialize from a registry JSON entry."""
        return cls(
            name=d["name"],
            installed_path=d["installed_path"],
            source=SkillSource(d["source"]),
            scope=SkillScope(d["scope"]),
            project=d.get("project", ""),
            version=d.get("version", "1.0.0"),
            install_method=InstallMethod(d.get("install_method", "symlink")),
        )
