"""Tests for bm prompt discovery, rendering, and export."""

from pathlib import Path

import pytest

from bm.prompts import create_prompt, discover_prompts, export_prompt, render_prompt, unexport_prompt


@pytest.fixture
def tmp_prompts_dir(tmp_path: Path) -> Path:
    """Create a temporary prompts directory with test prompts."""
    prompts = tmp_path / "prompts"
    prompts.mkdir()

    # General prompt
    p1 = prompts / "test-prompt"
    p1.mkdir()
    (p1 / "PROMPT.md").write_text(
        "---\n"
        "name: test-prompt\n"
        "description: A test prompt\n"
        "tags: [test, demo]\n"
        "scope: general\n"
        "---\n\n"
        "Do something with $1 and $ARGUMENTS\n"
    )

    # Project container
    proj = prompts / "myproject"
    proj.mkdir()
    p2 = proj / "proj-prompt"
    p2.mkdir()
    (p2 / "PROMPT.md").write_text(
        "---\n"
        "name: proj-prompt\n"
        "description: Project prompt\n"
        "tags: [project]\n"
        "scope: project\n"
        "project: myproject\n"
        "---\n\n"
        "Project-specific instructions.\n"
    )

    return prompts


def test_discover_prompts(tmp_prompts_dir: Path) -> None:
    prompts = discover_prompts(tmp_prompts_dir)
    names = [p.name for p in prompts]
    assert "test-prompt" in names
    assert "proj-prompt" in names


def test_discover_prompts_empty(tmp_path: Path) -> None:
    prompts = discover_prompts(tmp_path / "nonexistent")
    assert prompts == []


def test_discover_general_prompt_metadata(tmp_prompts_dir: Path) -> None:
    prompts = discover_prompts(tmp_prompts_dir)
    p = next(p for p in prompts if p.name == "test-prompt")
    assert p.description == "A test prompt"
    assert p.tags == ["test", "demo"]
    assert p.scope == "general"
    assert not p.is_project_prompt


def test_discover_project_prompt_metadata(tmp_prompts_dir: Path) -> None:
    prompts = discover_prompts(tmp_prompts_dir)
    p = next(p for p in prompts if p.name == "proj-prompt")
    assert p.scope == "project"
    assert p.project == "myproject"
    assert p.is_project_prompt


def test_render_prompt_no_args(tmp_prompts_dir: Path) -> None:
    prompts = discover_prompts(tmp_prompts_dir)
    p = next(p for p in prompts if p.name == "test-prompt")
    body = render_prompt(p)
    assert "$1" in body
    assert "$ARGUMENTS" in body


def test_render_prompt_with_args(tmp_prompts_dir: Path) -> None:
    prompts = discover_prompts(tmp_prompts_dir)
    p = next(p for p in prompts if p.name == "test-prompt")
    body = render_prompt(p, args=["myapp", "extra"])
    assert "myapp" in body
    assert "myapp extra" in body
    assert "$1" not in body
    assert "$ARGUMENTS" not in body


def test_export_prompt(tmp_prompts_dir: Path, tmp_path: Path) -> None:
    commands_dir = tmp_path / "commands"
    prompts = discover_prompts(tmp_prompts_dir)
    p = next(p for p in prompts if p.name == "test-prompt")
    result = export_prompt(p, commands_dir)
    assert result is True
    assert (commands_dir / "test-prompt.md").exists()


def test_unexport_prompt(tmp_prompts_dir: Path, tmp_path: Path) -> None:
    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()
    (commands_dir / "test-prompt.md").write_text("test")
    assert unexport_prompt("test-prompt", commands_dir) is True
    assert not (commands_dir / "test-prompt.md").exists()


def test_unexport_nonexistent(tmp_path: Path) -> None:
    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()
    assert unexport_prompt("nope", commands_dir) is False


def test_create_prompt(tmp_path: Path) -> None:
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    dest = create_prompt("my-new-prompt", prompts_dir, description="Test", tags=["a", "b"])
    assert (dest / "PROMPT.md").exists()
    content = (dest / "PROMPT.md").read_text()
    assert "my-new-prompt" in content
    assert "tags: [a, b]" in content


def test_create_project_prompt(tmp_path: Path) -> None:
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    dest = create_prompt("proj-thing", prompts_dir, project="pcs")
    assert dest == prompts_dir / "pcs" / "proj-thing"
    assert (dest / "PROMPT.md").exists()
