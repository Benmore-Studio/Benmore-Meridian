"""Tests for bm.config module."""

from pathlib import Path

from bm.config import BM_DIR, CLAUDE_SKILLS_DIR, PLUGIN_MARKERS, SKILLS_DIR


def test_skills_dir_exists() -> None:
    assert SKILLS_DIR.exists(), f"skills/ dir missing at {SKILLS_DIR}"


def test_claude_skills_under_home() -> None:
    assert str(CLAUDE_SKILLS_DIR).startswith(str(Path.home()))


def test_bm_dir_under_home() -> None:
    assert str(BM_DIR).startswith(str(Path.home()))


def test_plugin_markers_are_paths() -> None:
    for name, path in PLUGIN_MARKERS.items():
        assert isinstance(path, Path), f"{name} should be a Path"


def test_plugin_markers_have_expected_keys() -> None:
    assert "Superpowers" in PLUGIN_MARKERS
    assert "Double Shot Latte" in PLUGIN_MARKERS
