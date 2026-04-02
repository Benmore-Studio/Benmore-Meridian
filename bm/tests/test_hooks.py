"""Tests for bm git hook management."""

from pathlib import Path

import pytest

from bm.hooks import BM_HOOK_MARKER, hooks_status, install_hooks, remove_hooks


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """Create a fake git repo with .git/hooks/."""
    git_dir = tmp_path / ".git" / "hooks"
    git_dir.mkdir(parents=True)
    return tmp_path


def test_install_hooks(tmp_repo: Path) -> None:
    installed = install_hooks(tmp_repo)
    assert "post-merge" in installed
    assert "post-checkout" in installed
    hook = tmp_repo / ".git" / "hooks" / "post-merge"
    assert hook.exists()
    assert BM_HOOK_MARKER in hook.read_text()


def test_install_hooks_idempotent(tmp_repo: Path) -> None:
    install_hooks(tmp_repo)
    install_hooks(tmp_repo)
    hook = tmp_repo / ".git" / "hooks" / "post-merge"
    content = hook.read_text()
    assert content.count(BM_HOOK_MARKER) == 1


def test_install_hooks_preserves_existing(tmp_repo: Path) -> None:
    hook = tmp_repo / ".git" / "hooks" / "post-merge"
    hook.write_text("#!/bin/bash\necho existing\n")
    install_hooks(tmp_repo)
    content = hook.read_text()
    assert "echo existing" in content
    assert BM_HOOK_MARKER in content


def test_remove_hooks(tmp_repo: Path) -> None:
    install_hooks(tmp_repo)
    removed = remove_hooks(tmp_repo)
    assert "post-merge" in removed
    assert "post-checkout" in removed


def test_hooks_status(tmp_repo: Path) -> None:
    status = hooks_status(tmp_repo)
    assert status["post-merge"] is False
    install_hooks(tmp_repo)
    status = hooks_status(tmp_repo)
    assert status["post-merge"] is True


def test_no_git_dir(tmp_path: Path) -> None:
    assert install_hooks(tmp_path) == []
    assert remove_hooks(tmp_path) == []
    status = hooks_status(tmp_path)
    assert all(v is False for v in status.values())
