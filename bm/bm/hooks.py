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
        text = git_dir.read_text().strip()
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
        if hook_path.exists():
            existing = hook_path.read_text()
            if BM_HOOK_MARKER in existing:
                # Already installed — update in place
                hook_path.write_text(content)
                hook_path.chmod(0o755)
                installed.append(hook_name)
                continue
            # Existing non-bm hook — append
            if not existing.endswith("\n"):
                existing += "\n"
            hook_path.write_text(existing + "\n" + content)
        else:
            hook_path.write_text(content)

        hook_path.chmod(0o755)
        installed.append(hook_name)

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

        existing = hook_path.read_text()
        if BM_HOOK_MARKER not in existing:
            continue

        lines = existing.splitlines(keepends=True)
        # Find marker line and check if shebang precedes it
        marker_idx = next((i for i, l in enumerate(lines) if BM_HOOK_MARKER in l), -1)
        if marker_idx < 0:
            continue

        start_idx = max(0, marker_idx - 1) if marker_idx > 0 and lines[marker_idx - 1].startswith("#!/") else marker_idx

        # Check if entire file is just our hook
        if _is_only_bm_hook(lines, start_idx):
            hook_path.unlink()
        else:
            # Remove our hook block, keep other hooks
            remaining = [l for l in lines if BM_HOOK_MARKER not in l]
            hook_path.write_text("".join(remaining))

        removed.append(hook_name)

    return removed


def _is_only_bm_hook(lines: list[str], start_idx: int) -> bool:
    """Check if hook file contains only bm hook content (no other hooks)."""
    if start_idx != 0:
        return False
    bm_keywords = {"#", "", "if", "fi", "CHECKOUT", "command", "bm"}
    return all(
        line.strip() in bm_keywords or any(kw in line for kw in bm_keywords)
        for line in lines
    )


def hooks_status(repo_root: Path) -> dict[str, bool]:
    """Check which bm hooks are installed."""
    hooks_dir = _find_git_hooks_dir(repo_root)
    if hooks_dir is None:
        return {name: False for name in HOOKS}

    return {
        hook_name: (
            hook_path.exists() and BM_HOOK_MARKER in hook_path.read_text()
        )
        for hook_name, hook_path in (
            (name, hooks_dir / name) for name in HOOKS
        )
    }
