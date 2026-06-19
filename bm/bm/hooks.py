"""Git hook management for auto-registry updates."""

from __future__ import annotations

from pathlib import Path

BM_HOOK_MARKER = "# bm-auto-sync"

POST_MERGE_HOOK = f"""\
#!/bin/bash
{BM_HOOK_MARKER}
# Auto-sync bm registry after git pull brings new skills or prompts.
if git diff --name-only HEAD@{{1}} HEAD 2>/dev/null | grep -qE "^(skills|prompts)/"; then
  command -v bm &>/dev/null && bm install --quiet 2>/dev/null &
fi
"""

POST_CHECKOUT_HOOK = f"""\
#!/bin/bash
{BM_HOOK_MARKER}
# Auto-sync bm registry on branch switch.
CHECKOUT_TYPE=$3
if [ "$CHECKOUT_TYPE" = "1" ] && command -v bm &>/dev/null; then
  bm install --quiet 2>/dev/null &
fi
"""

HOOKS: dict[str, str] = {
    "post-merge": POST_MERGE_HOOK,
    "post-checkout": POST_CHECKOUT_HOOK,
}


def _find_git_hooks_dir(repo_root: Path) -> Path | None:
    """Find the .git/hooks directory, handling worktrees."""
    git_dir = repo_root / ".git"
    if git_dir.is_file():
        # worktree: .git is a file with "gitdir: <path>"
        text = git_dir.read_text(encoding="utf-8").strip()
        if text.startswith("gitdir:"):
            git_dir = Path(text.split(":", 1)[1].strip())
    if git_dir.is_dir():
        return git_dir / "hooks"
    return None


def install_hooks(repo_root: Path) -> list[str]:
    """Install bm git hooks. Returns list of installed hook names."""
    hooks_dir = _find_git_hooks_dir(repo_root)
    if hooks_dir is None:
        return []

    hooks_dir.mkdir(parents=True, exist_ok=True)
    installed: list[str] = []

    for hook_name, content in HOOKS.items():
        hook_path = hooks_dir / hook_name
        try:
            if hook_path.exists():
                existing = hook_path.read_text(encoding="utf-8")
                if BM_HOOK_MARKER in existing:
                    # Already installed — update in place
                    hook_path.write_text(content, encoding="utf-8")
                    hook_path.chmod(0o755)
                    installed.append(hook_name)
                    continue
                # Existing non-bm hook — append
                if not existing.endswith("\n"):
                    existing += "\n"
                hook_path.write_text(existing + "\n" + content, encoding="utf-8")
            else:
                hook_path.write_text(content, encoding="utf-8")

            hook_path.chmod(0o755)
            installed.append(hook_name)
        except (PermissionError, OSError):
            continue  # skip hooks we can't write — don't claim success

    return installed


def remove_hooks(repo_root: Path) -> list[str]:
    """Remove bm git hooks. Returns list of removed hook names."""
    hooks_dir = _find_git_hooks_dir(repo_root)
    if hooks_dir is None:
        return []

    removed: list[str] = []
    for hook_name in HOOKS:
        hook_path = hooks_dir / hook_name
        if not hook_path.exists():
            continue

        existing = hook_path.read_text(encoding="utf-8")
        if BM_HOOK_MARKER not in existing:
            continue

        lines = existing.splitlines(keepends=True)
        # Find the bm hook block boundaries
        marker_idx = next((i for i, line in enumerate(lines) if BM_HOOK_MARKER in line), -1)
        if marker_idx < 0:
            continue

        # Find where the bm block starts (include shebang if it's ours)
        bm_start = marker_idx
        if marker_idx > 0 and lines[marker_idx - 1].startswith("#!/"):
            bm_start = marker_idx - 1

        # Find where the bm block ends (next shebang or EOF)
        bm_end = len(lines)
        for i in range(marker_idx + 1, len(lines)):
            if lines[i].startswith("#!/"):
                bm_end = i
                break

        # Extract non-bm content
        before = lines[:bm_start]
        after = lines[bm_end:]
        remaining = before + after

        # If nothing left (or only whitespace), delete the file
        if not remaining or all(line.strip() == "" for line in remaining):
            hook_path.unlink()
        else:
            hook_path.write_text("".join(remaining), encoding="utf-8")

        removed.append(hook_name)

    return removed


def hooks_status(repo_root: Path) -> dict[str, bool]:
    """Check which bm hooks are installed."""
    hooks_dir = _find_git_hooks_dir(repo_root)
    if hooks_dir is None:
        return {name: False for name in HOOKS}

    return {
        hook_name: (hook_path.exists() and BM_HOOK_MARKER in hook_path.read_text(encoding="utf-8"))
        for hook_name, hook_path in ((name, hooks_dir / name) for name in HOOKS)
    }
