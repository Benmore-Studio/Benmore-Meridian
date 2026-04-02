"""Tests for bm prompt registry (stars, usage tracking)."""

from pathlib import Path

from bm.prompt_registry import PromptRegistry


def test_star_and_unstar(tmp_path: Path) -> None:
    reg = PromptRegistry(tmp_path / "prompts.json")
    reg.star("my-prompt")
    assert reg.get("my-prompt").starred is True
    reg.unstar("my-prompt")
    assert reg.get("my-prompt").starred is False


def test_record_use(tmp_path: Path) -> None:
    reg = PromptRegistry(tmp_path / "prompts.json")
    reg.record_use("my-prompt")
    reg.record_use("my-prompt")
    assert reg.get("my-prompt").use_count == 2
    assert reg.get("my-prompt").last_used != ""


def test_list_starred(tmp_path: Path) -> None:
    reg = PromptRegistry(tmp_path / "prompts.json")
    reg.star("a")
    reg.star("b")
    starred = reg.list_starred()
    assert "a" in starred
    assert "b" in starred


def test_list_by_popularity(tmp_path: Path) -> None:
    reg = PromptRegistry(tmp_path / "prompts.json")
    reg.record_use("less-used")
    reg.record_use("more-used")
    reg.record_use("more-used")
    popular = reg.list_by_popularity()
    assert popular[0] == ("more-used", 2)
    assert popular[1] == ("less-used", 1)


def test_persistence(tmp_path: Path) -> None:
    path = tmp_path / "prompts.json"
    reg1 = PromptRegistry(path)
    reg1.star("saved")
    reg1.record_use("saved")

    reg2 = PromptRegistry(path)
    assert reg2.get("saved").starred is True
    assert reg2.get("saved").use_count == 1
