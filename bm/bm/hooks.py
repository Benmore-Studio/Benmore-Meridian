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

        # If the whole file is our hook, remove it
        lines = existing.splitlines(keepends=True)
        bm_start = None
        for i, line in enumerate(lines):
            if BM_HOOK_MARKER in line:
                # Back up to the shebang if our hook starts the file
                bm_start = max(0, i - 1) if i > 0 and lines[i - 1].startswith("#!/") else i
                break

        if bm_start == 0 and all(
            line.strip() == "" or line.startswith("#") or "bm" in line or line.startswith("if ")
            or line.startswith("fi") or line.startswith("CHECKOUT") or line.startswith("command")
            for line in lines
        ):
            # Entire file is our hook — remove
            hook_path.unlink()
        else:
            # Extract our portion and leave the rest
            remaining = [l for l in lines if BM_HOOK_MARKER not in l]
            hook_path.write_text("".join(remaining))

        removed.append(hook_name)

    return removed


def hooks_status(repo_root: Path) -> dict[str, bool]:
    """Check which bm hooks are installed."""
    hooks_dir = _find_git_hooks_dir(repo_root)
    if hooks_dir is None:
        return {name: False for name in HOOKS}

    result: dict[str, bool] = {}
    for hook_name in HOOKS:
        hook_path = hooks_dir / hook_name
        if hook_path.exists() and BM_HOOK_MARKER in hook_path.read_text():
            result[hook_name] = True
        else:
            result[hook_name] = False
    return result
