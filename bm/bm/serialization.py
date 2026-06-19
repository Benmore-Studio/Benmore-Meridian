"""Stable JSON serialization helpers for public bm command output."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from bm.models import RegistryEntry, SkillEntry, SkillStatus
from bm.prompt_registry import PromptRegistry
from bm.prompts import PromptEntry

JsonValue = dict[str, Any] | list[Any] | str | int | float | bool | None


def _json_default(value: Any) -> JsonValue:
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def print_json_payload(payload: Any, *, indent: int | None = 2) -> None:
    """Print JSON directly to stdout with no Rich markup or warning channel."""
    print(json.dumps(payload, indent=indent, default=_json_default))


def skill_status_payload(statuses: list[tuple[SkillEntry, SkillStatus]]) -> list[dict[str, str]]:
    return [
        {
            "name": skill.name,
            "status": status.value,
            "scope": skill.scope.value,
            "project": skill.project,
        }
        for skill, status in statuses
    ]


def skill_list_payload(skills: list[SkillEntry]) -> list[dict[str, str]]:
    return [
        {
            "name": skill.name,
            "scope": skill.scope.value,
            "project": skill.project,
            "path": str(skill.path),
        }
        for skill in skills
    ]


def registry_list_payload(entries: list[RegistryEntry]) -> list[dict[str, Any]]:
    return [asdict(entry) for entry in entries]


def prompt_list_payload(
    prompts: list[PromptEntry], prompt_registry: PromptRegistry
) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for prompt in prompts:
        state = prompt_registry.get(prompt.name)
        payload.append(
            {
                "name": prompt.name,
                "description": prompt.description,
                "tags": prompt.tags,
                "scope": prompt.scope,
                "project": prompt.project,
                "starred": state.starred,
                "use_count": state.use_count,
            }
        )
    return payload


def suggestion_payload(suggestions: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": suggestion.name,
            "reason": suggestion.reason,
            "status": suggestion.status,
            "score": suggestion.score,
        }
        for suggestion in suggestions
    ]


def debrief_payload(candidates: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": candidate.name,
            "rationale": candidate.rationale,
            "score": candidate.score,
            "command": candidate.command,
        }
        for candidate in candidates
    ]
