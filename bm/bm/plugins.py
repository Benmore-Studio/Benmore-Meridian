"""Plugin detection and install guidance."""

from __future__ import annotations

import json
from pathlib import Path

from bm.config import (
    INSTALLED_PLUGINS_FILE,
    PLUGIN_IDS,
    PLUGIN_INSTALL_INSTRUCTIONS,
    PLUGIN_MARKERS,
)


def _installed_plugin_names(installed_file: Path) -> set[str] | None:
    """Plugin names from Claude Code's registry, or None if it can't be read.

    Registry keys are "<plugin>@<marketplace>"; the marketplace varies by how
    the plugin was installed, so only the plugin name is compared.
    """
    try:
        data = json.loads(installed_file.read_text())
    except (OSError, ValueError):
        return None
    plugins = data.get("plugins") if isinstance(data, dict) else None
    if not isinstance(plugins, dict):
        return None
    return {key.split("@", 1)[0] for key, installs in plugins.items() if installs}


def get_plugin_status(
    markers: dict[str, Path] | None = None,
    installed_file: Path | None = None,
) -> dict[str, bool]:
    if markers is None:
        markers = PLUGIN_MARKERS
    if installed_file is None:
        installed_file = INSTALLED_PLUGINS_FILE

    installed = _installed_plugin_names(installed_file)
    if installed is None:
        return {name: path.exists() for name, path in markers.items()}
    return {name: PLUGIN_IDS.get(name, name) in installed for name in markers}


def format_install_guide(plugin_name: str) -> str:
    return PLUGIN_INSTALL_INSTRUCTIONS.get(
        plugin_name,
        f"Visit claude.ai/marketplace to install {plugin_name}",
    )
