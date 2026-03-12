"""Core data models for bm — enums and dataclasses only."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class SkillScope(str, Enum):
    """Whether a skill is universal or tied to a specific project."""
    GENERAL = "general"
    PROJECT = "project"


class SkillSource(str, Enum):
    """Where a skill came from."""
    REPO = "repo"
    MARKETPLACE = "marketplace"
    EXTERNAL = "external"


class InstallResult(str, Enum):
    """Result of installing a skill."""
    SYMLINKED = "symlinked"
    COPIED = "copied"
    FAILED = "failed"
    SKIPPED = "skipped"


class SkillStatus(str, Enum):
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
    install_method: str = "symlink"  # "symlink" | "copy" | "external" | "none"
