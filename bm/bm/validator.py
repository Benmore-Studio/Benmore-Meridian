"""SKILL.md frontmatter validation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from bm.models import SkillEntry


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return len(self.errors) == 0


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Extract key: value pairs from the first YAML frontmatter block."""
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip().strip('"')
    return result


def validate_skill(skill: SkillEntry) -> ValidationResult:
    """
    Validate a skill's SKILL.md frontmatter.

    Required (errors block installation):
      - name: present, non-empty, matches directory name
      - description: present, non-empty

    Optional (missing → warning only, install continues):
      - version, author, tags
    """
    result = ValidationResult()
    skill_md = skill.path / "SKILL.md"

    if not skill_md.exists():
        result.errors.append(f"SKILL.md missing in {skill.path}")
        return result

    fm = _parse_frontmatter(skill_md.read_text(encoding="utf-8"))

    # Required: name
    name_val = fm.get("name", "")
    if not name_val:
        result.errors.append(
            f"'{skill.name}': frontmatter missing required field 'name'"
        )
    elif name_val != skill.name:
        result.errors.append(
            f"'{skill.name}': frontmatter name '{name_val}' does not match"
            f" directory name '{skill.name}'"
        )

    # Required: description
    desc_val = fm.get("description", "")
    if not desc_val:
        result.errors.append(
            f"'{skill.name}': frontmatter missing or empty 'description'"
        )

    # Optional: version, author, tags
    for optional in ("version", "author", "tags"):
        if optional not in fm:
            result.warnings.append(
                f"'{skill.name}': optional field '{optional}' not set"
            )

    return result
