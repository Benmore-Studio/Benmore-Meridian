"""bm — Benmore skill manager for Claude Code."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from bm.config import (
    AGENTS_SKILLS_DIR,
    CLAUDE_SKILLS_DIR,
    PLUGINS_DIR,
    REGISTRY_FILE,
    SKILLS_DIR,
    REPO_ROOT,
)
from bm.installer import discover_skills, install_skill
from bm.models import InstallResult, RegistryEntry, SkillScope, SkillSource, SkillStatus
from bm.plugins import format_install_guide, get_plugin_status
from bm.registry import Registry
from bm.status import check_plugins, check_skill_status
from bm.updater import git_pull, reinstall_all

app = typer.Typer(name="bm", help="Benmore skill manager", add_completion=False)
skill_app = typer.Typer(help="Manage individual skills")
registry_app = typer.Typer(help="Manage skill registry")
app.add_typer(skill_app, name="skill")
app.add_typer(registry_app, name="registry")

console = Console()

_STATUS_ICON = {
    SkillStatus.SYMLINKED: "✅",
    SkillStatus.COPIED: "⚙️ ",
    SkillStatus.MISSING: "❌",
    SkillStatus.BROKEN: "🔗",
}


# ── Core Commands ─────────────────────────────────────────────────────────────

@app.command()
def install(
    rsync: bool = typer.Option(False, "--rsync", help="Force file copy instead of symlinks"),
) -> None:
    """Install all skills from this repo into ~/.claude/skills/."""
    CLAUDE_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    skills = discover_skills(SKILLS_DIR)
    reg = Registry(REGISTRY_FILE)

    table = Table(title="Installing Skills", box=box.ROUNDED)
    table.add_column("Skill", style="cyan")
    table.add_column("Scope")
    table.add_column("Result", justify="center")

    for skill in skills:
        result = install_skill(skill, CLAUDE_SKILLS_DIR, force_copy=rsync)
        if result == InstallResult.SYMLINKED:
            icon = "✅"
        elif result == InstallResult.COPIED:
            icon = "⚙️"
        else:
            icon = "❌"
        scope_label = f"[dim]{skill.project}[/]" if skill.is_project_skill else "general"
        table.add_row(skill.name, scope_label, f"{icon} {result.value}")
        reg.add(RegistryEntry(
            name=skill.name,
            installed_path=str(CLAUDE_SKILLS_DIR / skill.name),
            source=skill.source,
            scope=skill.scope,
            project=skill.project,
            install_method="symlink" if result == InstallResult.SYMLINKED else "copy",
        ))

    console.print(table)
    console.print(f"\n[bold green]Done![/] {len(skills)} skills → {CLAUDE_SKILLS_DIR}")
    console.print("[dim]Run [bold]bm plugins[/] to verify plugin requirements.[/]")


@app.command()
def status(
    json_output: bool = typer.Option(False, "--json", help="Machine-readable JSON output"),
) -> None:
    """Show status of all skills and plugins."""
    skills = discover_skills(SKILLS_DIR)
    rows = []
    for skill in skills:
        s = check_skill_status(skill, CLAUDE_SKILLS_DIR)
        rows.append({
            "name": skill.name,
            "status": s.value,
            "scope": skill.scope.value,
            "project": skill.project,
        })

    if json_output:
        console.print(json.dumps(rows, indent=2))
        return

    table = Table(title="Skill Status", box=box.ROUNDED)
    table.add_column("Skill", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Scope")
    for row in rows:
        s = SkillStatus(row["status"])
        scope = f"[dim]{row['project']}[/]" if row["scope"] == "project" else "general"
        table.add_row(row["name"], _STATUS_ICON[s], scope)

    plugin_status = check_plugins(PLUGINS_DIR, AGENTS_SKILLS_DIR)
    console.print(table)
    lines = [f"  {'✅' if ok else '⚠️ '} {name}" for name, ok in plugin_status.items()]
    console.print(Panel("\n".join(lines), title="Plugins", border_style="blue"))


@app.command()
def update(
    name: Optional[str] = typer.Argument(None, help="Skill name to update (omit for all)"),
    rsync: bool = typer.Option(False, "--rsync"),
) -> None:
    """Pull latest and reinstall one or all skills."""
    console.print("[bold]Pulling latest changes...[/]")
    ok, output = git_pull()
    if not ok:
        console.print(f"[red]git pull failed:[/]\n{output}")
        raise typer.Exit(1)
    console.print(f"[green]{output.strip()}[/]")

    if name:
        skills = [s for s in discover_skills(SKILLS_DIR) if s.name == name]
        if not skills:
            console.print(f"[red]Skill '{name}' not found in repo.[/]")
            raise typer.Exit(1)
        result = install_skill(skills[0], CLAUDE_SKILLS_DIR, force_copy=rsync)
        console.print(f"{'✅' if result != InstallResult.FAILED else '❌'} {name}: {result.value}")
    else:
        results = reinstall_all(force_copy=rsync)
        linked = sum(1 for r in results.values() if r == InstallResult.SYMLINKED)
        copied = sum(1 for r in results.values() if r == InstallResult.COPIED)
        console.print(f"✅ {linked} linked  ⚙️  {copied} copied")


@app.command()
def plugins() -> None:
    """Check and guide Superpowers + Double Shot Latte installation."""
    plugin_status = get_plugin_status()
    all_ok = True
    for name, installed in plugin_status.items():
        if installed:
            console.print(f"[green]✅ {name}[/] — installed")
        else:
            all_ok = False
            console.print(Panel(format_install_guide(name), title=f"Install {name}", border_style="yellow"))
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
    plugin_status = check_plugins(PLUGINS_DIR, AGENTS_SKILLS_DIR)
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
    from_path: Optional[Path] = typer.Option(None, "--from", help="Copy from existing directory"),
) -> None:
    """Add a new skill (general or project-scoped)."""
    import shutil

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
            f"---\nname: {name}\ndescription: TODO: describe this skill\n---\n\n# {name}\n\nTODO: write skill instructions.\n"
        )

    scope_label = f"project '{project}'" if project else "general"
    console.print(f"[green]✅ Created {scope_label} skill '{name}'[/] at {dest_dir}")
    console.print(f"[dim]Edit {dest_dir}/SKILL.md, then run [bold]bm install[/bold] to activate.[/]")

    reg = Registry(REGISTRY_FILE)
    reg.add(RegistryEntry(
        name=name,
        installed_path=str(dest_dir),
        source=SkillSource.REPO,
        scope=scope,
        project=project,
        install_method="none",
    ))


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
        console.print(json.dumps([
            {"name": s.name, "scope": s.scope.value, "project": s.project, "path": str(s.path)}
            for s in skills
        ], indent=2))
        return

    table = Table(box=box.SIMPLE)
    table.add_column("Skill", style="cyan")
    table.add_column("Scope")
    table.add_column("Description")
    for s in skills:
        scope = f"[dim]{s.project}[/]" if s.is_project_skill else "general"
        table.add_row(s.name, scope, s.description[:60] or "[dim]—[/]")
    console.print(table)


@skill_app.command("generalize")
def skill_generalize(
    name: str = typer.Argument(..., help="Project skill name to promote"),
) -> None:
    """Promote a project-specific skill to general (moves it out of skills/pcs/)."""
    import shutil

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

    from bm.models import SkillEntry
    updated = SkillEntry(name=name, path=dest, scope=SkillScope.GENERAL, source=SkillSource.REPO)
    result = install_skill(updated, CLAUDE_SKILLS_DIR)
    console.print(f"[green]Reinstalled:[/] {result.value}")

    reg = Registry(REGISTRY_FILE)
    entry = reg.get(name)
    if entry:
        entry.scope = SkillScope.GENERAL
        entry.project = ""
        reg.add(entry)


@skill_app.command("info")
def skill_info(name: str = typer.Argument(..., help="Skill name")) -> None:
    """Show details for a skill."""
    skills = discover_skills(SKILLS_DIR)
    skill = next((s for s in skills if s.name == name), None)
    if not skill:
        console.print(f"[red]Skill '{name}' not found in repo.[/]")
        raise typer.Exit(1)
    s = check_skill_status(skill, CLAUDE_SKILLS_DIR)
    reg = Registry(REGISTRY_FILE)
    entry = reg.get(name)
    lines = [
        f"[cyan]{name}[/]",
        f"  Path:    {skill.path}",
        f"  Scope:   {skill.scope.value}" + (f" (project: {skill.project})" if skill.project else ""),
        f"  Status:  {_STATUS_ICON[s]} {s.value}",
        f"  Source:  {entry.source.value if entry else 'unknown'}",
        f"  Version: {entry.version if entry else skill.version}",
    ]
    if skill.description:
        lines.append(f"  Desc:    {skill.description}")
    console.print("\n".join(lines))


# ── registry sub-commands ──────────────────────────────────────────────────────

@registry_app.command("sync")
def registry_sync() -> None:
    """Scan ~/.claude/skills/ and update registry."""
    reg = Registry(REGISTRY_FILE)
    before = len(reg.list_all())
    reg.sync(CLAUDE_SKILLS_DIR, SKILLS_DIR)
    after = len(reg.list_all())
    console.print(f"[green]Registry synced.[/] {before} → {after} entries ({after - before:+d} new)")


@registry_app.command("list")
def registry_list(
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """List all registered skills."""
    reg = Registry(REGISTRY_FILE)
    entries = reg.list_all()
    if json_output:
        from dataclasses import asdict
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
