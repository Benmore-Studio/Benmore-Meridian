"""Path constants for bm — no side effects at import time."""

from __future__ import annotations

from pathlib import Path


def _find_repo_root() -> Path:
    """
    Walk up from this file looking for a directory that contains skills/.
    This works with both editable installs (pip install -e) and installed wheels.
    Falls back to reading ~/.bm/repo_root if the walk fails.
    """
    candidate = Path(__file__).resolve()
    for parent in [candidate, *candidate.parents]:
        if (parent / "skills").is_dir() and (parent / "bm").is_dir():
            return parent

    # Fallback: read from stored config
    stored = Path.home() / ".bm" / "repo_root"
    if stored.exists():
        path = Path(stored.read_text().strip())
        if path.is_dir():
            return path

    # Last resort: use __file__ grandparent (correct for editable installs)
    return Path(__file__).parent.parent.parent


REPO_ROOT: Path = _find_repo_root()
SKILLS_DIR: Path = REPO_ROOT / "skills"
PROMPTS_DIR: Path = REPO_ROOT / "prompts"
CLAUDE_DIR: Path = Path.home() / ".claude"
CLAUDE_SKILLS_DIR: Path = CLAUDE_DIR / "skills"
CLAUDE_COMMANDS_DIR: Path = CLAUDE_DIR / "commands"
AGENTS_SKILLS_DIR: Path = Path.home() / ".agents" / "skills"
PLUGINS_DIR: Path = CLAUDE_DIR / "plugins"
BM_DIR: Path = Path.home() / ".bm"
REGISTRY_FILE: Path = BM_DIR / "registry.json"
PROMPT_REGISTRY_FILE: Path = BM_DIR / "prompts.json"
SUGGESTION_CACHE_FILE: Path = BM_DIR / "suggestions.json"

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
