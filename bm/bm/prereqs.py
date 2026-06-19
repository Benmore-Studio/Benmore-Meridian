"""Prerequisite checks for bm setup."""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass, field


@dataclass
class Prereq:
    """A prerequisite tool or dependency for bm."""

    name: str
    check_cmd: str
    install_commands: dict[str, str] = field(default_factory=dict)
    required: bool = False

    def is_installed(self) -> bool:
        """Return True if the prerequisite's binary is on PATH."""
        return shutil.which(self.check_cmd) is not None

    def get_install_command(self) -> str | None:
        """Return the install command for the current platform, or None."""
        return self.install_commands.get(sys.platform)


def _get_package_manager_prereq() -> Prereq:
    """Return the appropriate package-manager prereq for the current platform."""
    if sys.platform == "darwin":
        return Prereq(
            name="Homebrew",
            check_cmd="brew",
            install_commands={
                "darwin": '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"',
            },
            required=False,
        )
    if sys.platform == "win32":
        return Prereq(
            name="winget",
            check_cmd="winget",
            install_commands={
                "win32": "Pre-installed on Windows 11+",
            },
            required=False,
        )
    # linux / other
    return Prereq(
        name="apt-get",
        check_cmd="apt-get",
        install_commands={
            "linux": "Pre-installed on Debian/Ubuntu",
        },
        required=False,
    )


PREREQS: list[Prereq] = [
    Prereq(
        name="Python 3.11+",
        check_cmd="python3",
        install_commands={
            "darwin": "Already running Python",
            "linux": "sudo apt-get install python3.11",
            "win32": "winget install Python.Python.3.11",
        },
        required=True,
    ),
    Prereq(
        name="uv",
        check_cmd="uv",
        install_commands={
            "darwin": "brew install uv",
            "linux": "curl -LsSf https://astral.sh/uv/install.sh | sh",
            "win32": "winget install astral-sh.uv",
        },
        required=False,
    ),
    _get_package_manager_prereq(),
    Prereq(
        name="Claude Code CLI",
        check_cmd="claude",
        install_commands={
            "darwin": "brew install claude-code",
            "linux": "npm install -g @anthropic-ai/claude-code",
            "win32": "npm install -g @anthropic-ai/claude-code",
        },
        required=False,
    ),
    Prereq(
        name="Git",
        check_cmd="git",
        install_commands={
            "darwin": "brew install git",
            "linux": "sudo apt-get install git",
            "win32": "winget install Git.Git",
        },
        required=True,
    ),
]


def check_prereqs() -> list[tuple[Prereq, bool]]:
    """Return all prereqs paired with their installed status."""
    return [(p, p.is_installed()) for p in PREREQS]
