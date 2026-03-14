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
from bm.dryrun import DryRunContext
from bm.installer import discover_skills, install_skill, remove_skill
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
from bm.tools import TOOLS, install_tool
from bm.debrief import run_debrief
from bm.skill_matcher import SkillMatcher
from bm.updater import get_changelog_section, git_pull, is_update_available

app = typer.Typer(name="bm", help="Benmore skill manager", add_completion=False)
skill_app = typer.Typer(help="Manage individual skills")
registry_app = typer.Typer(help="Manage skill registry")
tools_app = typer.Typer(help="Install developer CLI tools")
app.add_typer(skill_app, name="skill")
app.add_typer(registry_app, name="registry")
app.add_typer(tools_app, name="tools")

console = Console()


# ── Dashboard (no-subcommand handler) ────────────────────────────────────────


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Benmore skill manager for Claude Code."""
    if ctx.invoked_subcommand is not None:
        return
    _render_dashboard()


def _render_dashboard() -> None:
    """Render the Rich-formatted bm dashboard."""
    from bm import __version__

    # ── Gather stats ──────────────────────────────────────────────────────────
    skills = discover_skills(SKILLS_DIR)
    skill_statuses = [check_skill_status(s, CLAUDE_SKILLS_DIR) for s in skills]
    installed_skills = sum(
        1
        for st in skill_statuses
        if st in (SkillStatus.SYMLINKED, SkillStatus.COPIED)
    )
    total_skills = len(skills)

    total_tools = len(TOOLS)
    missing_tools = [name for name, tool in TOOLS.items() if not tool.is_installed()]
    installed_tools = total_tools - len(missing_tools)

    plugin_status = get_plugin_status()
    total_plugins = len(plugin_status)
    installed_plugins = sum(1 for ok in plugin_status.values() if ok)

    # ── Header panel ──────────────────────────────────────────────────────────
    skill_icon = "\u2705" if installed_skills == total_skills else "\u26a0"
    tool_icon = "\u2705" if not missing_tools else "\u26a0"
    plugin_icon = "\u2705" if installed_plugins == total_plugins else "\u26a0"

    header = (
        f"  Skills: {installed_skills}/{total_skills} {skill_icon}   "
        f"\u2502   Tools: {installed_tools}/{total_tools} {tool_icon}   "
        f"\u2502   Plugins: {installed_plugins}/{total_plugins} {plugin_icon}"
    )
    console.print(
        Panel(
            header,
            title=f"[bold]bm \u00b7 Benmore Skill Manager v{__version__}[/bold]",
            border_style="cyan",
        )
    )

    # ── Update check ─────────────────────────────────────────────────────────
    try:
        if is_update_available():
            console.print(
                "\n[bold yellow]⚠ update available[/bold yellow] — run [bold]bm update[/bold]"
            )
    except Exception:
        pass  # never crash the dashboard on network issues

    # ── Warnings ──────────────────────────────────────────────────────────────
    if missing_tools:
        names = ", ".join(missing_tools)
        console.print(
            f"\n[yellow]\u26a0  {len(missing_tools)} tools missing:[/yellow] {names}"
        )
        console.print("   [dim]\u2192 bm tools install[/dim]")

    missing_plugins = [name for name, ok in plugin_status.items() if not ok]
    if missing_plugins:
        names = ", ".join(missing_plugins)
        console.print(
            f"\n[yellow]\u26a0  {len(missing_plugins)} plugins missing:[/yellow] {names}"
        )
        console.print("   [dim]\u2192 bm plugins[/dim]")

    missing_skill_count = total_skills - installed_skills
    if missing_skill_count > 0:
        console.print(
            f"\n[yellow]\u26a0  {missing_skill_count} skills not installed[/yellow]"
        )
        console.print("   [dim]\u2192 bm install[/dim]")

    # ── Command reference sections ────────────────────────────────────────────
    def _cmd(command: str, description: str) -> None:
        console.print(f"  [cyan]{command:<30}[/cyan] [dim]{description}[/dim]")

    console.print()
    console.rule("[bold]Getting Started[/bold]")
    console.print()
    _cmd("bm setup", "Install everything: skills, tools, plugins")
    _cmd("bm doctor", "Full health check \u2014 find and fix problems")
    _cmd("bm update", "Git pull latest + reinstall all skills")

    console.print()
    console.rule("[bold]Skills[/bold]")
    console.print()
    _cmd("bm install", "Symlink all skills \u2192 ~/.claude/skills/")
    _cmd("bm skill list", "Browse all available skills")
    _cmd("bm skill info <name>", "Details on a specific skill")
    _cmd("bm skill add <name>", "Create a new skill from scratch")
    _cmd("bm skill write <name>", "Interactive skill builder with prompts")
    _cmd("bm skill remove <name>", "Uninstall a skill")
    _cmd("bm skill generalize <name>", "Promote project skill \u2192 general")

    console.print()
    console.rule("[bold]Tools[/bold]")
    console.print()
    _cmd("bm tools list", "Show dev tools (ripgrep, bat, fzf, etc.)")
    _cmd("bm tools install", "Install all missing tools via brew/apt")
    _cmd("bm tools install <name>", "Install a specific tool")

    console.print()
    console.rule("[bold]Plugins[/bold]")
    console.print()
    _cmd("bm plugins", "Check Superpowers + Double Shot Latte")

    console.print()
    console.rule("[bold]Registry[/bold]")
    console.print()
    _cmd("bm registry list", "Show all tracked skills")
    _cmd("bm registry sync", "Detect externally installed skills")

    console.print()
    console.rule("[bold]Options[/bold]")
    console.print()
    _cmd("--json", "Machine-readable output (status, skill list)")
    _cmd("--dry-run", "Preview changes without writing")
    _cmd("--rsync", "Force file copy instead of symlinks")
    console.print()


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
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be installed without writing"
    ),
) -> None:
    """Symlink all repo skills into ~/.claude/skills/ (idempotent)."""
    CLAUDE_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    skills = discover_skills(SKILLS_DIR)
    reg = Registry(REGISTRY_FILE)
    ctx = DryRunContext(dry_run=dry_run)

    title = "Installing Skills" + (" [dim](dry-run)[/]" if dry_run else "")
    table = Table(title=title, box=box.ROUNDED)
    table.add_column("Skill", style="cyan")
    table.add_column("Scope")
    table.add_column("Result", justify="center")

    new_entries: list[RegistryEntry] = []
    for skill in skills:
        result = install_skill(skill, CLAUDE_SKILLS_DIR, force_copy=rsync, ctx=ctx)
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

    console.print(table)
    reg.batch_add(new_entries, ctx=ctx)

    if dry_run:
        ctx.render(console)
    else:
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
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be updated without writing"
    ),
) -> None:
    """Pull latest and reinstall one or all skills."""
    ctx = DryRunContext(dry_run=dry_run)

    if not dry_run:
        console.print("[bold]Pulling latest changes...[/]")
        ok, output = git_pull()
        if not ok:
            console.print(f"[red]git pull failed:[/]\n{output}")
            raise typer.Exit(1)
        console.print(f"[green]{output.strip()}[/]")

        # Show changelog if version advanced
        changelog = get_changelog_section()
        if changelog.strip():
            console.print(
                Panel(
                    changelog,
                    title="[bold]What's new[/bold]",
                    border_style="green",
                )
            )
    else:
        console.print("[dim]Dry-run: skipping git pull[/]")

    reg = Registry(REGISTRY_FILE)
    if name:
        skill = _find_skill(name)
        if not skill:
            console.print(f"[red]Skill '{name}' not found in repo.[/]")
            raise typer.Exit(1)
        result = install_skill(skill, CLAUDE_SKILLS_DIR, force_copy=rsync, ctx=ctx)
        icon = _RESULT_ICON[result]
        console.print(f"{icon} {name}: {result.value}")
        if result != InstallResult.FAILED and not dry_run:
            reg.add(
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
            reg.save()
    else:
        skills = discover_skills(SKILLS_DIR)
        new_entries: list[RegistryEntry] = []
        for skill in skills:
            result = install_skill(skill, CLAUDE_SKILLS_DIR, force_copy=rsync, ctx=ctx)
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
        reg.batch_add(new_entries, ctx=ctx)
        if not dry_run:
            linked = sum(
                1 for e in new_entries if e.install_method == InstallMethod.SYMLINK
            )
            copied = sum(
                1 for e in new_entries if e.install_method == InstallMethod.COPY
            )
            console.print(f"✅ {linked} linked  ⚙️  {copied} copied")

    if dry_run:
        ctx.render(console)


@app.command("suggest")
def suggest(
    path: Path = typer.Argument(Path("."), help="Project directory to scan"),
    top: int = typer.Option(8, "--top", "-n", help="Number of suggestions to show"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Scan a project and suggest relevant skills based on detected stack."""
    matcher = SkillMatcher(SKILLS_DIR, CLAUDE_SKILLS_DIR)
    suggestions = matcher.scan(path.resolve(), top=top)

    if not suggestions:
        console.print("[dim]No matching skills detected for this project.[/dim]")
        raise typer.Exit(0)

    if json_output:
        import json as _json
        console.print(_json.dumps([{"name": s.name, "reason": s.reason, "status": s.status, "score": s.score} for s in suggestions]))
        return

    table = Table(title=f"Skill Suggestions for [cyan]{path}[/cyan]", box=box.ROUNDED)
    table.add_column("Rank", style="dim", width=5)
    table.add_column("Skill", style="bold cyan")
    table.add_column("Why")
    table.add_column("Status")

    for i, s in enumerate(suggestions, 1):
        status_str = "[green]installed ✓[/green]" if s.status == "installed" else "[dim]bm install[/dim]"
        table.add_row(str(i), s.name, s.reason, status_str)

    console.print(table)


@app.command("context")
def context(
    path: Path = typer.Argument(Path("."), help="Project directory to scan"),
    copy: bool = typer.Option(False, "--copy", "-c", help="Copy output to clipboard"),
) -> None:
    """Generate a CLAUDE.md snippet with detected stack and recommended skills."""
    matcher = SkillMatcher(SKILLS_DIR, CLAUDE_SKILLS_DIR)
    suggestions = matcher.scan(path.resolve(), top=5)
    summary = matcher.stack_summary(path.resolve())

    skill_names = ", ".join(s.name for s in suggestions) if suggestions else "none detected"

    snippet = f"""## Project Stack (auto-detected by bm context)
- {summary}
- Recommended skills: {skill_names}
"""

    console.print(snippet)

    if copy:
        import platform
        import subprocess as _sp
        cmd = {"Darwin": "pbcopy", "Linux": "xclip -selection clipboard", "Windows": "clip"}.get(platform.system())
        if cmd:
            _sp.run(cmd.split(), input=snippet.encode(), check=False)
            console.print("[green]✓ Copied to clipboard[/green]")
        else:
            console.print("[yellow]Clipboard not supported on this platform[/yellow]")


@app.command("explore")
def explore(
    path: Path = typer.Argument(Path("."), help="Project directory to scan"),
    output: Path = typer.Option(Path("docs/bm-suggestions.md"), "--output", "-o", help="Output file path"),
) -> None:
    """Deep project scan — writes a skill suggestion report to docs/bm-suggestions.md."""
    from bm.config import REPO_ROOT
    matcher = SkillMatcher(SKILLS_DIR, CLAUDE_SKILLS_DIR)
    suggestions = matcher.scan(path.resolve(), top=20)
    summary = matcher.stack_summary(path.resolve())

    lines = [
        f"# bm explore — Skill Suggestions",
        f"",
        f"**Scanned:** `{path.resolve()}`  ",
        f"**Date:** {__import__('datetime').date.today()}  ",
        f"**Detected stack:** {summary}",
        f"",
        f"## Ranked Suggestions",
        f"",
        f"| Rank | Skill | Reason | Status |",
        f"|------|-------|--------|--------|",
    ]
    for i, s in enumerate(suggestions, 1):
        lines.append(f"| {i} | `{s.name}` | {s.reason} | {s.status} |")

    installed = [s for s in suggestions if s.status == "installed"]
    available = [s for s in suggestions if s.status == "available"]

    if available:
        lines += ["", "## Install Commands", ""]
        lines += [f"```bash"] + [f"bm install  # then symlink {s.name}" for s in available[:5]] + ["```"]

    if installed:
        lines += ["", "## Already Installed", ""]
        lines += [f"- `{s.name}`" for s in installed]

    report = "\n".join(lines)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report)

    console.print(f"[green]✓ Report written to[/green] [cyan]{output}[/cyan]")
    console.print(f"  Detected: [bold]{summary}[/bold]")
    console.print(f"  Suggestions: {len(suggestions)} skills ({len(installed)} installed, {len(available)} available)")


@app.command("debrief")
def debrief_cmd(
    limit: int = typer.Option(15, "--limit", "-n", help="Number of commits to scan"),
    since: str = typer.Option("", "--since", help="Look back to this git ref or ISO date"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Scan recent git history and surface candidate skills worth codifying."""
    from bm.config import REPO_ROOT
    candidates = run_debrief(REPO_ROOT, limit=limit, since=since or None)

    if not candidates:
        console.print("[dim]No reusable patterns detected in recent commits.[/dim]")
        raise typer.Exit(0)

    if json_output:
        import json as _json
        console.print(_json.dumps([{"name": c.name, "rationale": c.rationale, "score": c.score, "command": c.command} for c in candidates]))
        return

    rows = "\n".join(
        f"  [bold cyan]{i}. {c.name}[/bold cyan]  [dim]score: {c.score}[/dim]\n"
        f"     {c.rationale}\n"
        f"     [dim]→ {c.command}[/dim]"
        for i, c in enumerate(candidates, 1)
    )
    console.print(
        Panel(
            rows,
            title=f"[bold]bm debrief[/bold] — {len(candidates)} skill candidate(s) from last {limit} commits",
            border_style="cyan",
        )
    )


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
def doctor(
    yes: bool = typer.Option(False, "--yes", "-y", help="Auto-fix without prompting"),
) -> None:
    """Full health check — find and fix problems."""
    issues = 0

    # ── Skills ────────────────────────────────────────────────────────────────
    console.rule("[bold]Skills[/]")
    skills = discover_skills(SKILLS_DIR)
    total = len(skills)
    broken: list[SkillEntry] = []
    for skill in skills:
        st = check_skill_status(skill, CLAUDE_SKILLS_DIR)
        if st in (SkillStatus.MISSING, SkillStatus.BROKEN):
            broken.append(skill)

    healthy = total - len(broken)
    console.print(f"  {healthy}/{total} installed")

    if broken:
        names = [s.name for s in broken]
        console.print(f"  [yellow]⚠  {len(broken)} broken:[/] {', '.join(names)}")
        do_fix = yes or typer.confirm("  Fix?", default=True)
        if do_fix:
            CLAUDE_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
            reg = Registry(REGISTRY_FILE)
            new_entries: list[RegistryEntry] = []
            for skill in broken:
                result = install_skill(skill, CLAUDE_SKILLS_DIR)
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
            fixed = [e.name for e in new_entries]
            if fixed:
                console.print(f"  [green]✅ Reinstalled {', '.join(fixed)}[/]")
            failed = [s.name for s in broken if s.name not in fixed]
            if failed:
                console.print(f"  [red]❌ Failed: {', '.join(failed)}[/]")
                issues += len(failed)
        else:
            issues += len(broken)
    else:
        console.print(f"  [green]✅ All {total} skills healthy[/]")

    # ── Tools ─────────────────────────────────────────────────────────────────
    console.rule("[bold]Tools[/]")
    all_tools = list(TOOLS.values())
    missing_tools = [t for t in all_tools if not t.is_installed()]
    installed_count = len(all_tools) - len(missing_tools)

    console.print(f"  {installed_count}/{len(all_tools)} installed")

    if missing_tools:
        names_t = [t.name for t in missing_tools]
        console.print(f"  [yellow]⚠  Missing:[/] {', '.join(names_t)}")
        do_install = yes or typer.confirm("  Install?", default=True)
        if do_install:
            fixed_tools: list[str] = []
            for tool in missing_tools:
                console.print(f"  [bold]Installing {tool.name}...[/]")
                success, msg = install_tool(tool)
                if success:
                    fixed_tools.append(tool.name)
                else:
                    console.print(f"  [red]❌ {tool.name}:[/] {msg}")
                    issues += 1
            if fixed_tools:
                console.print(f"  [green]✅ Installed {', '.join(fixed_tools)}[/]")
        else:
            issues += len(missing_tools)
    else:
        console.print(f"  [green]✅ All {len(all_tools)} tools installed[/]")

    # ── Plugins ───────────────────────────────────────────────────────────────
    console.rule("[bold]Plugins[/]")
    plugin_status = get_plugin_status()
    for pname, ok in plugin_status.items():
        if ok:
            console.print(f"  [green]✅ {pname}[/]")
        else:
            console.print(f"  [yellow]⚠  {pname}[/]")
            guide = format_install_guide(pname)
            for line in guide.splitlines():
                console.print(f"     → {line}")
            issues += 1

    # ── Summary ───────────────────────────────────────────────────────────────
    console.print()
    if issues == 0:
        console.print("[bold green]Everything looks great! 🎉[/]")
    else:
        console.print(f"[yellow]⚠  {issues} issue(s) remaining[/]")


@app.command()
def setup(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without changes"),
) -> None:
    """Install everything: skills, tools, and check plugins (one-shot setup)."""
    ctx = DryRunContext(dry_run=dry_run)

    if dry_run:
        console.print("[bold]bm setup[/] [dim](dry-run)[/]\n")
    else:
        console.print("[bold]bm setup[/]\n")

    # ── 1. Prerequisites ─────────────────────────────────────────────────────
    try:
        from bm.prereqs import check_prereqs

        prereqs = check_prereqs()
        console.print("[bold]📋 Prerequisites[/]")
        for prereq, installed in prereqs:
            if installed:
                console.print(f"  ✅ {prereq.name}")
            else:
                cmd = prereq.get_install_command()
                console.print(f"  ⚠️  {prereq.name}")
                if cmd:
                    console.print(f"     → {cmd}")
        console.print()
    except ImportError:
        pass

    # ── 2. Install skills ─────────────────────────────────────────────────────
    console.print("[bold]📦 Installing skills...[/]")
    CLAUDE_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    skills = discover_skills(SKILLS_DIR)
    reg = Registry(REGISTRY_FILE)

    new_entries: list[RegistryEntry] = []
    success_count = 0
    for skill in skills:
        result = install_skill(skill, CLAUDE_SKILLS_DIR, ctx=ctx)
        if result != InstallResult.FAILED:
            success_count += 1
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
    reg.batch_add(new_entries, ctx=ctx)
    console.print(f"  ✅ {success_count} skills → {CLAUDE_SKILLS_DIR}")
    console.print()

    # ── 3. Install missing tools ──────────────────────────────────────────────
    console.print("[bold]🛠  Installing missing tools...[/]")
    missing_tools_list = [t for t in TOOLS.values() if not t.is_installed()]

    if not missing_tools_list:
        console.print("  ✅ All tools installed")
    else:
        if dry_run:
            for tool in missing_tools_list:
                ctx.record("install_tool", tool.name)
            console.print(f"  [dim]Would install {len(missing_tools_list)} tools[/]")
        else:
            if not yes:
                names_list = ", ".join(t.name for t in missing_tools_list)
                console.print(f"  Missing: {names_list}")
                typer.confirm(f"Install {len(missing_tools_list)} missing tools?", abort=True)
            for tool in missing_tools_list:
                success, msg = install_tool(tool)
                if success:
                    console.print(f"  ✅ {tool.name} installed")
                else:
                    console.print(f"  ❌ {tool.name}: {msg}")
    console.print()

    # ── 4. Check plugins ──────────────────────────────────────────────────────
    console.print("[bold]🔌 Plugins:[/]")
    plugin_status = get_plugin_status()
    for pname, installed in plugin_status.items():
        if installed:
            console.print(f"  ✅ {pname}")
        else:
            console.print(f"  ⚠️  {pname}")
            guide = format_install_guide(pname)
            for line in guide.splitlines():
                if line.strip().startswith("claude "):
                    console.print(f"     → {line.strip()}")
                    break
    console.print()

    # ── 5. Summary ────────────────────────────────────────────────────────────
    total_tools = len(TOOLS)
    installed_tools = sum(1 for t in TOOLS.values() if t.is_installed())

    if dry_run:
        ctx.render(console)
    else:
        console.print(
            f"[bold green]✅ Setup complete![/] "
            f"{success_count} skills, {installed_tools}/{total_tools} tools"
        )


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


@skill_app.command("remove")
def skill_remove(
    name: str = typer.Argument(..., help="Skill name to remove"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be removed without writing"
    ),
) -> None:
    """Remove an installed skill from ~/.claude/skills/ and the registry."""
    reg = Registry(REGISTRY_FILE)
    entry = reg.get(name)

    if not entry:
        console.print(f"[red]Skill '{name}' not found in registry.[/]")
        raise typer.Exit(1)

    ctx = DryRunContext(dry_run=dry_run)
    try:
        remove_skill(name, CLAUDE_SKILLS_DIR, reg, ctx)
    except ValueError as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1) from e

    if dry_run:
        ctx.render(console)
    else:
        console.print(f"[green]Removed skill '{name}'[/]")


# ── registry sub-commands ──────────────────────────────────────────────────────


@registry_app.command("sync")
def registry_sync(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would sync without writing"
    ),
) -> None:
    """Scan ~/.claude/skills/ and update registry (detects externally installed skills)."""
    reg = Registry(REGISTRY_FILE)
    before = len(reg.list_all())
    ctx = DryRunContext(dry_run=dry_run)
    reg.sync(CLAUDE_SKILLS_DIR, SKILLS_DIR, ctx=ctx)

    if dry_run:
        ctx.render(console)
    else:
        after = len(reg.list_all())
        added = after - before
        console.print(
            f"[green]Registry synced.[/] {before} → {after} entries ({added:+d} new)"
        )


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


# ── tools sub-commands ─────────────────────────────────────────────────────────


@tools_app.command("list")
def tools_list() -> None:
    """List available developer tools to install."""
    table = Table(title="Developer Tools", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Installed", justify="center")
    table.add_column("URL", style="dim")
    for tool in TOOLS.values():
        installed_icon = "✅" if tool.is_installed() else "❌"
        table.add_row(tool.name, tool.description, installed_icon, tool.url)
    console.print(table)


@tools_app.command("install")
def tools_install(
    names: list[str] = typer.Argument(None, help="Tool names (omit for all)"),  # noqa: B008
) -> None:
    """Install developer CLI tools via Homebrew (macOS) or apt (Linux)."""
    targets: list[str] = list(names) if names else list(TOOLS.keys())

    unknown = [n for n in targets if n not in TOOLS]
    if unknown:
        console.print(f"[red]Unknown tools: {', '.join(unknown)}[/]")
        console.print(f"[dim]Available: {', '.join(TOOLS.keys())}[/]")
        raise typer.Exit(1)

    for name in targets:
        tool = TOOLS[name]
        if tool.is_installed():
            console.print(f"[dim]⏭️  {name} already installed[/]")
            continue
        console.print(f"[bold]Installing {name}...[/]")
        success, msg = install_tool(tool)
        if success:
            console.print(f"[green]✅ {name}[/] installed")
        else:
            console.print(f"[red]❌ {name}:[/] {msg}")


# ── skill write ────────────────────────────────────────────────────────────────


@skill_app.command("write")
def skill_write(
    name: str = typer.Argument(..., help="Skill name (e.g. my-skill)"),
    project: str = typer.Option("", "--project", "-p", help="Project scope (e.g. pcs)"),
) -> None:
    """Interactively create a SKILL.md stub for a new skill."""
    scope = SkillScope.PROJECT if project else SkillScope.GENERAL
    dest_dir = SKILLS_DIR / project / name if project else SKILLS_DIR / name

    if dest_dir.exists():
        console.print(f"[yellow]Skill '{name}' already exists at {dest_dir}[/]")
        raise typer.Exit(1)

    console.print(f"[bold]Creating skill:[/] [cyan]{name}[/]")

    description = typer.prompt("  Description (one line)")
    triggers_raw = typer.prompt(
        "  Triggers (comma-separated phrases that invoke this skill)",
        default="",
    )
    triggers = [t.strip() for t in triggers_raw.split(",") if t.strip()]

    trigger_lines = "\n".join(f"  - {t}" for t in triggers) if triggers else "  - TODO: add trigger"
    trigger_block = f"triggers:\n{trigger_lines}"

    skill_md_content = (
        f"---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        f"{trigger_block}\n"
        f"---\n\n"
        f"# {name}\n\n"
        f"{description}\n\n"
        f"## Usage\n\n"
        f"TODO: Describe how to use this skill.\n\n"
        f"## Instructions\n\n"
        f"TODO: Write the skill instructions here.\n"
    )

    dest_dir.mkdir(parents=True)
    (dest_dir / "SKILL.md").write_text(skill_md_content)

    scope_label = f"project '{project}'" if project else "general"
    console.print(f"[green]✅ Created {scope_label} skill '[cyan]{name}[/cyan]'[/] at {dest_dir}")
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


# ── skill add-external (alias for installing external skills) ──────────────────


@skill_app.command("add-external")
def skills_add_external(
    source: str = typer.Argument(..., help="Source hint e.g. 'vercel/vercel --skill vercel-cli'"),
    skill: str = typer.Option("", "--skill", help="Skill name to look for in plugin directories"),
) -> None:
    """
    Attempt to install an external skill from ~/.claude/plugins or ~/.agents.
    If not found, prints installation guidance.
    """
    skill_name = skill
    if not skill_name and "--skill" in source:
        parts = source.split("--skill")
        if len(parts) > 1:
            skill_name = parts[1].strip().split()[0]
        source = parts[0].strip()

    if not skill_name:
        console.print(
            "[red]Provide a skill name via --skill <name> or embed '--skill <name>' in source.[/]"
        )
        raise typer.Exit(1)

    search_dirs = [
        Path.home() / ".claude" / "plugins",
        Path.home() / ".agents",
        Path.home() / ".claude" / "skills",
    ]

    found_path: Path | None = None
    for d in search_dirs:
        candidate = d / skill_name
        if candidate.exists():
            found_path = candidate
            break

    if found_path:
        target = CLAUDE_SKILLS_DIR / skill_name
        if target.exists() or target.is_symlink():
            console.print(f"[yellow]Skill '{skill_name}' already installed at {target}[/]")
            raise typer.Exit(0)
        try:
            target.symlink_to(found_path.resolve())
            console.print(f"[green]✅ Linked '{skill_name}'[/] from {found_path} → {target}")
        except OSError:
            shutil.copytree(str(found_path), str(target))
            console.print(f"[green]✅ Copied '{skill_name}'[/] from {found_path} → {target}")
    else:
        searched = "\n  ".join(str(d) for d in search_dirs)
        console.print(
            Panel(
                f"Skill '[cyan]{skill_name}[/cyan]' not found in:\n  {searched}\n\n"
                f"To install manually:\n"
                f"  1. Download or clone the skill directory\n"
                f"  2. Place it in [bold]~/.claude/skills/{skill_name}[/bold]\n"
                f"  3. Run [bold]bm registry sync[/bold] to register it\n\n"
                f"Source hint: [dim]{source}[/dim]",
                title="External Skill Not Found",
                border_style="yellow",
            )
        )
