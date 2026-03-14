"""git pull + reinstall."""

from __future__ import annotations

import subprocess
from pathlib import Path

from bm.config import CLAUDE_SKILLS_DIR, REPO_ROOT, SKILLS_DIR
from bm.installer import discover_skills, install_skill
from bm.models import InstallResult


def git_pull(repo_root: Path = REPO_ROOT) -> tuple[bool, str]:
    r = subprocess.run(
        ["git", "pull", "--ff-only"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    return r.returncode == 0, r.stdout + r.stderr


def reinstall_all(
    skills_dir: Path = SKILLS_DIR,
    claude_skills_dir: Path = CLAUDE_SKILLS_DIR,
    force_copy: bool = False,
) -> dict[str, InstallResult]:
    return {
        skill.name: install_skill(skill, claude_skills_dir, force_copy=force_copy)
        for skill in discover_skills(skills_dir)
    }


def get_current_tag(repo_root: Path = REPO_ROOT) -> str | None:
    """Return the current git tag (e.g. 'v1.2.0'), or None if no tags exist."""
    try:
        r = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if r.returncode == 0:
            return r.stdout.strip() or None
        return None
    except (subprocess.CalledProcessError, OSError):
        return None


def get_remote_tag(repo_root: Path = REPO_ROOT) -> str | None:
    """Fetch remote tags and return the latest tag on origin/main, or None."""
    try:
        r = subprocess.run(
            ["git", "ls-remote", "--tags", "origin"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=3,
        )
        if r.returncode != 0:
            return None

        tags: list[tuple[int, ...]] = []
        tag_strings: dict[tuple[int, ...], str] = {}

        for line in r.stdout.splitlines():
            # Lines look like: <sha>\trefs/tags/v1.2.0
            # Skip peeled tag refs (refs/tags/v1.2.0^{})
            if "\t" not in line or "^{}" in line:
                continue
            ref = line.split("\t", 1)[1].strip()
            if not ref.startswith("refs/tags/"):
                continue
            tag = ref[len("refs/tags/"):]
            raw = tag.lstrip("v")
            parts = raw.split(".")
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                semver = tuple(int(p) for p in parts)
                tags.append(semver)
                tag_strings[semver] = tag

        if not tags:
            return None

        latest = max(tags)
        return tag_strings[latest]

    except subprocess.TimeoutExpired:
        return None
    except (subprocess.CalledProcessError, OSError):
        return None


def is_update_available(repo_root: Path = REPO_ROOT) -> bool:
    """Return True if remote has a newer tag than local HEAD."""
    local_tag = get_current_tag(repo_root)
    remote_tag = get_remote_tag(repo_root)

    if remote_tag is None:
        return False

    local_raw = (local_tag or "v0.0.0").lstrip("v")
    remote_raw = remote_tag.lstrip("v")

    try:
        local_tuple = tuple(int(x) for x in local_raw.split("."))
        remote_tuple = tuple(int(x) for x in remote_raw.split("."))
    except ValueError:
        return False

    return remote_tuple > local_tuple


def get_changelog_section(
    repo_root: Path = REPO_ROOT,
    from_tag: str = "",
    to_tag: str = "",
) -> str:
    """Extract CHANGELOG.md section between two tags. Falls back to git log if not found."""
    if to_tag:
        changelog_path = repo_root / "CHANGELOG.md"
        try:
            text = changelog_path.read_text(encoding="utf-8")
            header = f"## {to_tag}"
            start = text.find(header)
            if start != -1:
                # Move past the header line
                content_start = start + len(header)
                # Find the next ## header
                next_header = text.find("\n## ", content_start)
                if next_header != -1:
                    section = text[content_start:next_header]
                else:
                    section = text[content_start:]
                return section.strip()
        except (OSError, UnicodeDecodeError):
            pass

    # Fall back to git log
    if from_tag and to_tag:
        log_range = f"{from_tag}..{to_tag}"
    elif to_tag:
        log_range = to_tag
    elif from_tag:
        log_range = f"{from_tag}..HEAD"
    else:
        return ""

    try:
        r = subprocess.run(
            ["git", "log", log_range, "--oneline", "--no-merges"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if r.returncode == 0:
            return r.stdout.strip()
        return ""
    except (subprocess.CalledProcessError, OSError):
        return ""
