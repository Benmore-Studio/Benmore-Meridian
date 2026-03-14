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


_UPDATE_CACHE_FILE = Path.home() / ".bm" / "update_check_cache"
_UPDATE_CACHE_TTL_HOURS = 24


def _parse_semver(tag: str) -> tuple[int, ...]:
    """Parse a semver tag string like 'v1.2.3' into a tuple of ints."""
    return tuple(int(x) for x in tag.lstrip("v").split("."))


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
                semver = _parse_semver(tag)
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
    """Return True if remote has a newer tag than local HEAD.

    Result is cached in ~/.bm/update_check_cache for 24 hours to avoid
    a network round-trip on every `bm` invocation.
    """
    import time

    # Check TTL cache
    if _UPDATE_CACHE_FILE.exists():
        try:
            cached = _UPDATE_CACHE_FILE.read_text().strip().split(":")
            if len(cached) == 2:
                ts, result = float(cached[0]), cached[1] == "1"
                if time.time() - ts < _UPDATE_CACHE_TTL_HOURS * 3600:
                    return result
        except (ValueError, OSError):
            pass

    local_tag = get_current_tag(repo_root)
    remote_tag = get_remote_tag(repo_root)

    if remote_tag is None:
        return False

    try:
        available = _parse_semver(remote_tag) > _parse_semver(local_tag or "v0.0.0")
    except ValueError:
        return False

    # Persist result with timestamp
    try:
        _UPDATE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _UPDATE_CACHE_FILE.write_text(f"{time.time()}:{'1' if available else '0'}")
    except OSError:
        pass

    return available


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
