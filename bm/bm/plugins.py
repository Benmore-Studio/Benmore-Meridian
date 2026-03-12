"""Plugin detection and install guidance."""

from __future__ import annotations

from pathlib import Path

from bm.config import PLUGIN_INSTALL_INSTRUCTIONS, PLUGIN_MARKERS


def get_plugin_status(markers: dict[str, Path] | None = None) -> dict[str, bool]:
    if markers is None:
        markers = PLUGIN_MARKERS
    return {name: path.exists() for name, path in markers.items()}


def format_install_guide(plugin_name: str) -> str:
    return PLUGIN_INSTALL_INSTRUCTIONS.get(
        plugin_name,
        f"Visit claude.ai/marketplace to install {plugin_name}",
    )
