"""Prompt discovery, rendering, and export for bm."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from bm.dryrun import DryRunContext


@dataclass
class PromptEntry:
    """A prompt discovered in the repository."""

    name: str
    path: Path
    description: str = ""
    tags: list[str] = field(default_factory=list)
    scope: str = "general"
    project: str = ""
    version: str = "1.0.0"

    @property
    def is_project_prompt(self) -> bool:
        return self.scope == "project"


def _parse_frontmatter(text: str) -> dict[str, str | list[str]]:
    """Parse YAML-ish frontmatter from PROMPT.md."""
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}

    result: dict[str, str | list[str]] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()

        if val.startswith("[") and val.endswith("]"):
            items = [t.strip().strip("'\"") for t in val[1:-1].split(",") if t.strip()]
            result[key] = items
        else:
            result[key] = val

    return result


def _get_prompt_body(text: str) -> str:
    """Extract the body (after frontmatter) from PROMPT.md."""
    match = re.match(r"^---\s*\n.*?\n---\s*\n?", text, re.DOTALL)
    if match:
        return text[match.end() :]
    return text


def discover_prompts(prompts_dir: Path) -> list[PromptEntry]:
    """Discover all prompts under prompts/."""
    if not prompts_dir.is_dir():
        return []

    entries: list[PromptEntry] = []
    for child in sorted(prompts_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue

        prompt_file = child / "PROMPT.md"
        if prompt_file.exists():
            # General prompt
            try:
                fm = _parse_frontmatter(prompt_file.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError):
                continue  # skip broken prompts gracefully
            tags = fm.get("tags", [])
            entries.append(
                PromptEntry(
                    name=child.name,
                    path=child,
                    description=str(fm.get("description", "")),
                    tags=tags if isinstance(tags, list) else [],
                    scope="general",
                )
            )
        else:
            # Project container: look for subdirs with PROMPT.md
            for sub in sorted(child.iterdir()):
                if not sub.is_dir():
                    continue
                sub_prompt = sub / "PROMPT.md"
                if sub_prompt.exists():
                    try:
                        fm = _parse_frontmatter(sub_prompt.read_text(encoding="utf-8"))
                    except (OSError, UnicodeDecodeError):
                        continue
                    tags = fm.get("tags", [])
                    entries.append(
                        PromptEntry(
                            name=sub.name,
                            path=sub,
                            description=str(fm.get("description", "")),
                            tags=tags if isinstance(tags, list) else [],
                            scope="project",
                            project=child.name,
                        )
                    )
    return entries


def render_prompt(prompt: PromptEntry, args: list[str] | None = None) -> str:
    """Render a prompt body with argument substitution."""
    text = (prompt.path / "PROMPT.md").read_text(encoding="utf-8")
    body = _get_prompt_body(text)

    if args:
        # Replace $1, $2, etc.
        for i, arg in enumerate(args, 1):
            body = body.replace(f"${i}", arg)
        # Replace $ARGUMENTS with all args joined
        body = body.replace("$ARGUMENTS", " ".join(args))

    return body.strip()


def export_prompt(
    prompt: PromptEntry,
    commands_dir: Path,
    ctx: DryRunContext | None = None,
) -> bool:
    """Symlink a prompt into ~/.claude/commands/ as a slash command."""
    _ctx = ctx or DryRunContext()
    commands_dir.mkdir(parents=True, exist_ok=True)
    target = commands_dir / f"{prompt.name}.md"

    _ctx.record("export_prompt", str(target), str(prompt.path / "PROMPT.md"))
    if _ctx.dry_run:
        return True

    if target.exists() or target.is_symlink():
        target.unlink()

    try:
        target.symlink_to((prompt.path / "PROMPT.md").resolve())
        return True
    except OSError:
        try:
            shutil.copy2(prompt.path / "PROMPT.md", target)
            return True
        except (OSError, FileNotFoundError):
            return False


def unexport_prompt(
    name: str,
    commands_dir: Path,
    ctx: DryRunContext | None = None,
) -> bool:
    """Remove a prompt from ~/.claude/commands/."""
    _ctx = ctx or DryRunContext()
    target = commands_dir / f"{name}.md"

    if not target.exists() and not target.is_symlink():
        return False

    _ctx.record("unexport_prompt", str(target))
    if not _ctx.dry_run:
        target.unlink()
    return True


def create_prompt(
    name: str,
    prompts_dir: Path,
    description: str = "",
    tags: list[str] | None = None,
    project: str = "",
) -> Path:
    """Create a new prompt stub."""
    dest = prompts_dir / project / name if project else prompts_dir / name

    dest.mkdir(parents=True, exist_ok=True)

    tag_str = ", ".join(tags) if tags else ""
    content = (
        f"---\n"
        f"name: {name}\n"
        f"description: {description or 'TODO: describe this prompt'}\n"
        f"tags: [{tag_str}]\n"
        f"scope: {'project' if project else 'general'}\n"
        f"project: {project}\n"
        f"---\n\n"
        f"$ARGUMENTS\n"
    )
    (dest / "PROMPT.md").write_text(content, encoding="utf-8")
    return dest
