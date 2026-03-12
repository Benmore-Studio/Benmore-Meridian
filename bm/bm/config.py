"""Path constants for bm — no side effects at import time."""
from __future__ import annotations

from pathlib import Path

_THIS_FILE = Path(__file__)          # bm/bm/config.py
_PACKAGE_DIR = _THIS_FILE.parent     # bm/bm/
_BM_PKG_DIR = _PACKAGE_DIR.parent   # bm/
REPO_ROOT: Path = _BM_PKG_DIR.parent  # Benmore-Meridian/

SKILLS_DIR: Path = REPO_ROOT / "skills"
CLAUDE_DIR: Path = Path.home() / ".claude"
CLAUDE_SKILLS_DIR: Path = CLAUDE_DIR / "skills"
AGENTS_SKILLS_DIR: Path = Path.home() / ".agents" / "skills"
PLUGINS_DIR: Path = CLAUDE_DIR / "plugins"
BM_DIR: Path = Path.home() / ".bm"
REGISTRY_FILE: Path = BM_DIR / "registry.json"

PLUGIN_MARKERS: dict[str, Path] = {
    "Superpowers": PLUGINS_DIR / "cache" / "claude-plugins-official",
    "Double Shot Latte": AGENTS_SKILLS_DIR,
}

PLUGIN_INSTALL_INSTRUCTIONS: dict[str, str] = {
    "Superpowers": (
        "Install Superpowers plugin:\n"
        "  claude plugins install superpowers\n"
        "  or: claude.ai/marketplace → search Superpowers"
    ),
    "Double Shot Latte": (
        "Install Double Shot Latte (compound-engineering):\n"
        "  claude plugins install compound-engineering\n"
        "  GitHub: https://github.com/EveryInc/compound-engineering-plugin"
    ),
}
