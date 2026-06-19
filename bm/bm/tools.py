"""Developer tool definitions for bm tools install."""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class DevTool:
    name: str
    description: str
    brew_formula: str  # macOS
    apt_package: str = ""  # Linux fallback
    check_cmd: str = ""  # command to verify install (defaults to name)
    url: str = ""

    def __post_init__(self) -> None:
        if not self.check_cmd:
            self.check_cmd = self.name

    def is_installed(self) -> bool:
        """Return True if the tool's binary is on PATH."""
        return shutil.which(self.check_cmd) is not None


TOOLS: dict[str, DevTool] = {
    "ripgrep": DevTool(
        name="ripgrep",
        description="Extremely fast grep replacement",
        brew_formula="ripgrep",
        apt_package="ripgrep",
        check_cmd="rg",
        url="https://github.com/BurntSushi/ripgrep",
    ),
    "fzf": DevTool(
        name="fzf",
        description="Fuzzy finder for the terminal",
        brew_formula="fzf",
        apt_package="fzf",
        url="https://github.com/junegunn/fzf",
    ),
    "lazygit": DevTool(
        name="lazygit",
        description="Simple terminal UI for git",
        brew_formula="lazygit",
        url="https://github.com/jesseduffield/lazygit",
    ),
    "bat": DevTool(
        name="bat",
        description="cat with syntax highlighting",
        brew_formula="bat",
        apt_package="bat",
        url="https://github.com/sharkdp/bat",
    ),
    "eza": DevTool(
        name="eza",
        description="Modern ls replacement",
        brew_formula="eza",
        url="https://github.com/eza-community/eza",
    ),
    "zoxide": DevTool(
        name="zoxide",
        description="Smarter cd command",
        brew_formula="zoxide",
        apt_package="zoxide",
        url="https://github.com/ajeetdsouza/zoxide",
    ),
    "delta": DevTool(
        name="delta",
        description="Better git diff viewer",
        brew_formula="git-delta",
        check_cmd="delta",
        url="https://github.com/dandavison/delta",
    ),
    "gh": DevTool(
        name="gh",
        description="GitHub CLI",
        brew_formula="gh",
        apt_package="gh",
        url="https://cli.github.com/",
    ),
}


def _is_macos() -> bool:
    return sys.platform == "darwin"


def _is_linux() -> bool:
    return sys.platform.startswith("linux")


def install_tool(tool: DevTool) -> tuple[bool, str]:
    """
    Install a single tool via Homebrew (macOS) or apt-get (Linux).
    Returns (success, message).
    """
    if _is_macos():
        if not shutil.which("brew"):
            return False, "Homebrew not found. Install from https://brew.sh"
        cmd = ["brew", "install", tool.brew_formula]
    elif _is_linux():
        if not tool.apt_package:
            return False, f"No apt package defined for '{tool.name}'"
        if not shutil.which("apt-get"):
            return False, "apt-get not found; install manually"
        cmd = ["sudo", "apt-get", "install", "-y", tool.apt_package]
    else:
        return False, f"Unsupported platform: {sys.platform}"

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return True, f"Installed {tool.name}"
    return False, result.stderr.strip() or result.stdout.strip()
