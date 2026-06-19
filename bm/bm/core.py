"""Core filesystem/parsing helpers with an optional native backend.

The public CLI stays Python/Typer. This module is the compatibility boundary
for hot-path helpers that can be provided by a PyO3 extension when available,
with pure Python fallbacks for editable/source installs.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

try:  # pragma: no cover - native module is optional in source installs.
    _native_backend: Any | None = importlib.import_module("bm._native")
except ImportError:  # pragma: no cover - fallback is covered instead.
    _native_backend = None


def parse_frontmatter(text: str) -> dict[str, str]:
    """Parse simple YAML-ish string frontmatter from SKILL/PROMPT markdown."""
    if _native_backend is not None:
        parsed = _native_backend.parse_frontmatter(text)
        if isinstance(parsed, dict):
            return {str(key): str(value) for key, value in parsed.items()}

    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    result: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        result[key.strip()] = value.strip().strip("'\"")
    return result


def path_status(path: Path) -> str:
    """Return symlinked, copied, broken, or missing for an installed path."""
    if _native_backend is not None:
        status = _native_backend.path_status(str(path))
        if isinstance(status, str):
            return status

    if path.is_symlink():
        return "symlinked" if path.exists() else "broken"
    if path.exists():
        return "copied"
    return "missing"


def paths_overlap(source: Path, target_parent: Path) -> bool:
    """Return True when installing target_parent would overlap source."""
    if _native_backend is not None:
        result: Any = _native_backend.paths_overlap(str(source), str(target_parent))
        if isinstance(result, bool):
            return result

    source_resolved = source.resolve()
    target_resolved = target_parent.resolve()
    source_parent = source_resolved.parent
    return _is_relative_to(target_resolved, source_parent) or _is_relative_to(
        source_resolved, target_resolved
    )


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False
