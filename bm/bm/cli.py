"""bm — Benmore skill manager for Claude Code."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from pathlib import Path

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from bm.config import (
    CLAUDE_SKILLS_DIR,
    REGISTRY_FILE,
    SKILLS_DIR,
)
from bm.installer import discover_skills, install_skill
from bm.models import (
    InstallMethod,
    InstallResult,
    RegistryEntry,
    SkillEntry,
    SkillScope,
    SkillSource,
    SkillStatus,
)
from bm.plugins import format_install_guide, get_plugin_status
from bm.registry import Registry
from bm.status import check_skill_status
from bm.updater import git_pull, reinstall_all

app = typer.Typer(name="bm", help="Benmore skill manager", add_completion=False)
skill_app = typer.Typer(help="Manage individual skills")
registry_app = typer.Typer(help="Manage skill registry")
app.add_typer(skill_app, name="skill")
app.add_typer(registry_app, name="registry")

console = Console()

_STATUS_ICON: dict[SkillStatus, str] = {
    SkillStatus.SYMLINKED: "✅",
    SkillStatus.COPIED: "⚙️ ",
    SkillStatus.MISSING: "❌",
    SkillStatus.BROKEN: "🔗",
}

_RESULT_ICON: dict[InstallResult, str] = {
    InstallResult.SYMLINKED: "✅",
    InstallResult.COPIED: "⚙️ ",
    InstallResult.FAILED: "❌",
    InstallResult.SKIPPED: "⏭️ ",
}


def _scope_label(skill: SkillEntry) -> str:
    """Rich-formatted scope label for table display."""
    return f"[dim]{skill.project}[/]" if skill.is_project_skill else "general"


def _find_skill(name: str) -> SkillEntry | None:
    """Find a skill by name from the repo."""
    return next((s for s in discover_skills(SKILLS_DIR) if s.name == name), None)


# ── Core Commands ─────────────────────────────────────────────────────────────


@app.command()
def install(
    rsync: bool = typer.Option(False, "--rsync", help="Force file copy instead of symlinks"),
) -> None:
    """Symlink all repo skills into ~/.claude/skills/ (idempotent)."""
    CLAUDE_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    skills = discover_skills(SKILLS_DIR)
    reg = Registry(REGISTRY_FILE)

    table = Table(title="Installing Skills", box=box.ROUNDED)
    table.add_column("Skill", style="cyan")
    table.add_column("Scope")
    table.add_column("Result", justify="center")

    new_entries: list[RegistryEntry] = []
    for skill in skills:
        result = install_skill(skill, CLAUDE_SKILLS_DIR, force_copy=rsync)
        icon = _RESULT_ICON[result]
        table.add_row(skill.name, _scope_label(skill), f"{icon} {result.value}")
        if result != InstallResult.FAILED:
            new_entries.append(
                RegistryEntry(
                    name=skill.name,
                    installed_path=str(CLAUDE_SKILLS_DIR / skill.name),
                    source=skill.source,
                    scope=skill.scope,
                    project=skill.project,
                    install_method=(
                        InstallMethod.SYMLINK
                        if result == InstallResult.SYMLINKED
                        else InstallMethod.COPY
                    ),
                )
            )

    reg.batch_add(new_entries)
    console.print(table)
    console.print(f"\n[bold green]Done![/] {len(skills)} skills → {CLAUDE_SKILLS_DIR}")
    console.print("[dim]Run [bold]bm plugins[/] to verify plugin requirements.[/]")


@app.command()
def status(
    json_output: bool = typer.Option(False, "--json", help="Machine-readable JSON output"),
) -> None:
    """Show status of all repo skills."""
    skills = discover_skills(SKILLS_DIR)
    statuses = [(skill, check_skill_status(skill, CLAUDE_SKILLS_DIR)) for skill in skills]

    if json_output:
        console.print(
            json.dumps(
                [
                    {
                        "name": sk.name,
                        "status": st.value,
                        "scope": sk.scope.value,
                        "project": sk.project,
                    }
                    for sk, st in statuses
                ],
                indent=2,
            )
        )
        return

    table = Table(title="Skill Status", box=box.ROUNDED)
    table.add_column("Skill", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Scope")
    for skill, st in statuses:
        table.add_row(skill.name, _STATUS_ICON[st], _scope_label(skill))

    plugin_status = get_plugin_status()
    console.print(table)
    lines = [f"  {'✅' if ok else '⚠️ '} {name}" for name, ok in plugin_status.items()]
    console.print(Panel("\n".join(lines), title="Plugins", border_style="blue"))


@app.command()
def update(
    name: str | None = typer.Argument(None, help="Skill name to update (omit for all)"),
    rsync: bool = typer.Option(False, "--rsync"),
) -> None:
    """Pull latest and reinstall one or all skills."""
    console.print("[bold]Pulling latest changes...[/]")
    ok, output = git_pull()
    if not ok:
        console.print(f"[red]git pull failed:[/]\n{output}")
        raise typer.Exit(1)
    console.print(f"[green]{output.strip()}[/]")

    reg = Registry(REGISTRY_FILE)
    if name:
        skill = _find_skill(name)
        if not skill:
            console.print(f"[red]Skill '{name}' not found in repo.[/]")
            raise typer.Exit(1)
        result = install_skill(skill, CLAUDE_SKILLS_DIR, force_copy=rsync)
        icon = _RESULT_ICON[result]
        console.print(f"{icon} {name}: {result.value}")
        if result != InstallResult.FAILED:
            reg.add(RegistryEntry(
                name=skill.name,
                installed_path=str(CLAUDE_SKILLS_DIR / skill.name),
                source=skill.source,
                scope=skill.scope,
                project=skill.project,
                install_method=(
                    InstallMethod.SYMLINK
                    if result == InstallResult.SYMLINKED
                    else InstallMethod.COPY
                ),
            ))
            reg.save()
    else:
        results = reinstall_all(force_copy=rsync)
        linked = sum(1 for r in results.values() if r == InstallResult.SYMLINKED)
        copied = sum(1 for r in results.values() if r == InstallResult.COPIED)
        console.print(f"✅ {linked} linked  ⚙️  {copied} copied")
        # Sync registry to reflect updated install state
        reg.sync(CLAUDE_SKILLS_DIR, SKILLS_DIR)


@app.command()
def plugins() -> None:
    """Check and guide Superpowers + Double Shot Latte installation."""
    plugin_status = get_plugin_status()
    all_ok = True
    for pname, installed in plugin_status.items():
        if installed:
            console.print(f"[green]✅ {pname}[/] — installed")
        else:
            all_ok = False
            console.print(
                Panel(format_install_guide(pname), title=f"Install {pname}", border_style="yellow")
            )
    if all_ok:
        console.print("\n[bold green]All plugins ready![/]")


@app.command()
def doctor() -> None:
    """Full health check: skills + plugins + registry."""
    console.rule("[bold]bm doctor[/]")
    skills = discover_skills(SKILLS_DIR)
    counts: dict[SkillStatus, int] = {s: 0 for s in SkillStatus}
    for skill in skills:
        counts[check_skill_status(skill, CLAUDE_SKILLS_DIR)] += 1
    total = len(skills)
    healthy = counts[SkillStatus.SYMLINKED] + counts[SkillStatus.COPIED]
    console.print(f"Skills: [bold]{healthy}/{total}[/] installed")
    if counts[SkillStatus.MISSING] or counts[SkillStatus.BROKEN]:
        console.print(
            f"  [yellow]→ run [bold]bm install[/bold] to fix "
            f"{counts[SkillStatus.MISSING]} missing, {counts[SkillStatus.BROKEN]} broken[/]"
        )
    plugin_status = get_plugin_status()
    for pname, ok in plugin_status.items():
        console.print(f"Plugin {'✅' if ok else '⚠️ '} {pname}")
    if not all(plugin_status.values()):
        console.print("  [yellow]→ run [bold]bm plugins[/bold] for instructions[/]")
    if healthy == total and all(plugin_status.values()):
        console.print("\n[bold green]Everything looks great! 🎉[/]")


# ── skill sub-commands ─────────────────────────────────────────────────────────


@skill_app.command("add")
def skill_add(
    name: str = typer.Argument(..., help="Skill name"),
    project: str = typer.Option("", "--project", "-p", help="Project scope (e.g. pcs)"),
    from_path: Path | None = typer.Option(None, "--from", help="Copy from existing directory"),  # noqa: B008
) -> None:
    """Add a new skill (general or project-scoped)."""
    scope = SkillScope.PROJECT if project else SkillScope.GENERAL
    dest_dir = SKILLS_DIR / project / name if project else SKILLS_DIR / name

    if dest_dir.exists():
        console.print(f"[yellow]Skill '{name}' already exists at {dest_dir}[/]")
        raise typer.Exit(1)

    if from_path:
        shutil.copytree(from_path, dest_dir)
    else:
        dest_dir.mkdir(parents=True)
        (dest_dir / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: TODO: describe this skill\n---\n\n"
            f"# {name}\n\nTODO: write skill instructions.\n"
        )

    scope_label = f"project '{project}'" if project else "general"
    console.print(f"[green]✅ Created {scope_label} skill '{name}'[/] at {dest_dir}")
    console.print(
        f"[dim]Edit {dest_dir}/SKILL.md, then run [bold]bm install[/bold] to activate.[/]"
    )

    reg = Registry(REGISTRY_FILE)
    reg.add(
        RegistryEntry(
            name=name,
            installed_path=str(dest_dir),
            source=SkillSource.REPO,
            scope=scope,
            project=project,
            install_method=InstallMethod.NONE,
        )
    )
    reg.save()


@skill_app.command("list")
def skill_list(
    project: str = typer.Option("", "--project", "-p", help="Filter by project"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """List skills, optionally filtered by project."""
    skills = discover_skills(SKILLS_DIR)
    if project:
        skills = [s for s in skills if s.project == project]

    if json_output:
        console.print(
            json.dumps(
                [
                    {
                        "name": s.name,
                        "scope": s.scope.value,
                        "project": s.project,
                        "path": str(s.path),
                    }
                    for s in skills
                ],
                indent=2,
            )
        )
        return

    table = Table(box=box.SIMPLE)
    table.add_column("Skill", style="cyan")
    table.add_column("Scope")
    table.add_column("Description")
    for s in skills:
        table.add_row(s.name, _scope_label(s), s.description[:60] or "[dim]—[/]")
    console.print(table)


@skill_app.command("generalize")
def skill_generalize(
    name: str = typer.Argument(..., help="Project skill name to promote"),
) -> None:
    """Promote a project-specific skill to general (moves it out of its project folder)."""
    skills = discover_skills(SKILLS_DIR)
    skill = next((s for s in skills if s.name == name and s.is_project_skill), None)
    if not skill:
        console.print(f"[red]No project-scoped skill named '{name}' found.[/]")
        raise typer.Exit(1)

    dest = SKILLS_DIR / name
    if dest.exists():
        console.print(f"[yellow]A general skill '{name}' already exists at {dest}.[/]")
        raise typer.Exit(1)

    shutil.move(str(skill.path), str(dest))
    console.print(f"[green]✅ Moved '{name}'[/] from {skill.path.parent} → {dest}")

    updated = SkillEntry(name=name, path=dest, scope=SkillScope.GENERAL, source=SkillSource.REPO)
    result = install_skill(updated, CLAUDE_SKILLS_DIR)
    console.print(f"[green]Reinstalled:[/] {result.value}")

    reg = Registry(REGISTRY_FILE)
    entry = reg.get(name)
    if entry:
        entry.scope = SkillScope.GENERAL
        entry.project = ""
        reg.add(entry)
        reg.save()


@skill_app.command("info")
def skill_info(name: str = typer.Argument(..., help="Skill name")) -> None:
    """Show details for a skill."""
    skill = _find_skill(name)
    if not skill:
        console.print(f"[red]Skill '{name}' not found in repo.[/]")
        raise typer.Exit(1)
    st = check_skill_status(skill, CLAUDE_SKILLS_DIR)
    reg = Registry(REGISTRY_FILE)
    entry = reg.get(name)
    lines = [
        f"[cyan]{name}[/]",
        f"  Path:    {skill.path}",
        f"  Scope:   {skill.scope.value}"
        + (f" (project: {skill.project})" if skill.project else ""),
        f"  Status:  {_STATUS_ICON[st]} {st.value}",
        f"  Source:  {entry.source.value if entry else 'unknown'}",
        f"  Version: {entry.version if entry else skill.version}",
    ]
    if skill.description:
        lines.append(f"  Desc:    {skill.description}")
    console.print("\n".join(lines))


# ── registry sub-commands ──────────────────────────────────────────────────────


@registry_app.command("sync")
def registry_sync() -> None:
    """Scan ~/.claude/skills/ and update registry (detects externally installed skills)."""
    reg = Registry(REGISTRY_FILE)
    before = len(reg.list_all())
    reg.sync(CLAUDE_SKILLS_DIR, SKILLS_DIR)
    after = len(reg.list_all())
    added = after - before
    console.print(f"[green]Registry synced.[/] {before} → {after} entries ({added:+d} new)")


@registry_app.command("list")
def registry_list(
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """List all registered skills."""
    reg = Registry(REGISTRY_FILE)
    entries = reg.list_all()
    if json_output:
        console.print(json.dumps([asdict(e) for e in entries], indent=2, default=str))
        return
    table = Table(title=f"Registry ({len(entries)} skills)", box=box.SIMPLE)
    table.add_column("Name", style="cyan")
    table.add_column("Source")
    table.add_column("Scope")
    table.add_column("Install")
    for e in entries:
        table.add_row(e.name, e.source.value, e.scope.value, e.install_method)
    console.print(table)
