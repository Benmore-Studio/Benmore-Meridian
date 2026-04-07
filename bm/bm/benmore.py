"""Benmore API integration for bm CLI.

Provides subcommands for interacting with the Benmore project management API:
- bm benmore list — Numbered project list grouped by phase
- bm benmore overview — Single-command dashboard
- bm benmore lookup — Resolve BEN numbers to project IDs
- bm benmore summary — Time-scoped channel summaries
- bm benmore workflows — Available workflow prompts
- bm benmore projects/channels/context/status/team — Core CRUD
"""

from __future__ import annotations

import asyncio
import json
import sys
from functools import wraps
from pathlib import Path
from typing import Any, Callable

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

# Try importing from benmore_client, fall back gracefully
try:
    from benmore_client import BenmoreClient as _BenmoreClient
    BenmoreClient: Any = _BenmoreClient  # type: ignore[no-redef]
except ImportError:
    BenmoreClient = None  # type: ignore[assignment]

app = typer.Typer(help="Benmore API integration")
console = Console()

# Phase display colors
PHASE_COLORS: dict[str, str] = {
    "implementation": "green",
    "discovery": "yellow",
    "stalled": "red",
    "completed": "dim",
    "unknown": "white",
}


async def _fetch_project_enrichment(client: Any, project: Any) -> dict[str, Any]:
    """Fetch team + channel data for a single project (used with asyncio.gather).

    Catches httpx.HTTPStatusError specifically so 401/403/429 surface to caller,
    but treats 404 (no channel connected) as an empty result.
    """
    import httpx  # noqa: F401  (used in except clause below)

    entry: dict[str, Any] = {
        "id": project.id,
        "title": project.title,
        "phase": project.phase or "unknown",
        "status": project.status,
        "team": [],
        "channel": None,
        "messages": 0,
        "last_activity": None,
        "working_on": None,
    }

    # Get team
    try:
        members = await client.team_list(project.id)
        entry["team"] = [{"name": m.name, "username": m.username, "role": m.role} for m in members]
    except httpx.HTTPStatusError as e:
        if e.response.status_code not in (404,):
            raise  # Re-raise auth/rate-limit/server errors

    # Get channel
    try:
        raw = await client.comms_raw(project.id)
        entry["channel"] = raw.get("channel_id")
        entry["messages"] = raw.get("total_messages", 0)
        entry["last_activity"] = raw.get("last_message_at")
    except httpx.HTTPStatusError as e:
        if e.response.status_code not in (404,):
            raise

    return entry


async def _enrich_projects_parallel(client: Any, projects: list[Any]) -> list[dict[str, Any]]:
    """Fetch enrichment data for many projects in parallel using asyncio.gather.

    Replaces the N+1 sequential pattern. With 20 projects, drops latency from
    ~10s (40 sequential calls) to ~1s (40 parallel calls).
    """
    return await asyncio.gather(*[_fetch_project_enrichment(client, p) for p in projects])


def _require_client(func: Callable[..., None]) -> Callable[..., None]:
    """Decorator that checks BenmoreClient is available and gets API key."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        if BenmoreClient is None:
            console.print("[red]Error: benmore_client package not installed[/red]")
            sys.exit(1)
        try:
            api_key = _get_api_key()
        except typer.BadParameter as e:
            console.print(f"[red]Error: {escape(str(e))}[/red]")
            sys.exit(1)
        kwargs["_api_key"] = api_key
        return func(*args, **kwargs)

    return wrapper

# Workflow prompts — suggested when running bm benmore
WORKFLOW_PROMPTS = {
    "pr-review": {
        "name": "Full PR Review Audit",
        "skill": "/full-pr-review-audit",
        "description": "Deep PR review with security, performance, and code quality checks",
        "prompt_path": "prompts/full-pr-review-audit/PROMPT.md",
    },
    "qa": {
        "name": "QA Test Plan",
        "skill": "/qa-plan",
        "description": "Generate comprehensive QA test plan for features",
        "prompt_path": "prompts/qa-plan/PROMPT.md" if Path("prompts/qa-plan").exists() else None,
    },
    "quick-review": {
        "name": "Quick PR Review",
        "skill": "/quick-pr-review",
        "description": "Fast code review for smaller changes",
        "prompt_path": "prompts/quick-pr-review/PROMPT.md",
    },
    "value": {
        "name": "Client Value Maximizer",
        "skill": "/client-value-maximizer",
        "description": "Find high-impact quick wins — bugs, UX issues, performance",
        "prompt_path": None,
    },
    "edge-cases": {
        "name": "Edge Cases & User Flows",
        "skill": "/user-flows-with-edge-cases",
        "description": "Map user flows and discover edge cases",
        "prompt_path": "prompts/user-flows-with-edge-cases/PROMPT.md",
    },
    "tickets": {
        "name": "Create Project Tickets",
        "skill": "/create-project-tickets",
        "description": "Break work into actionable GitHub issues",
        "prompt_path": "prompts/create-project-tickets/PROMPT.md",
    },
    "kickoff": {
        "name": "Client Kickoff",
        "skill": "/client-kickoff",
        "description": "Generate client kickoff documentation and onboarding",
        "prompt_path": "prompts/client-kickoff/PROMPT.md",
    },
}


def _get_api_key() -> str:
    """Get Benmore API key from environment or config.

    Looks for BM_API_KEY env var, then ~/.benmore/config
    """
    import os

    # Try environment variable
    if api_key := os.environ.get("BM_API_KEY"):
        return api_key

    # Try config file
    config_path = Path.home() / ".benmore" / "config"
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
            if api_key := config.get("api_key"):
                return api_key
        except json.JSONDecodeError:
            raise typer.BadParameter(f"Malformed JSON in {config_path}. Fix the file or delete it.")
        except PermissionError:
            raise typer.BadParameter(f"Cannot read {config_path}. Check file permissions.")

    raise typer.BadParameter(
        "No API key found. Set BM_API_KEY env var or create ~/.benmore/config with api_key"
    )


@app.command()
def channels(
    ctx: typer.Context,
    project_ids: str = typer.Option(
        None,
        "--projects",
        help="Comma-separated project IDs (default: all assigned)",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List all Slack channels across projects.

    Shows channel name, member count, last activity, and connected projects.

    Examples:
        bm benmore channels
        bm benmore channels --projects proj1,proj2
        bm benmore channels --json | jq
    """
    if BenmoreClient is None:
        console.print("[red]Error: benmore_client package not installed[/red]")
        sys.exit(1)
    try:
        api_key = _get_api_key()
    except typer.BadParameter as e:
        console.print(f"[red]Error: {escape(str(e))}[/red]")
        sys.exit(1)

    # Parse project IDs
    proj_ids = None
    if project_ids:
        proj_ids = [p.strip() for p in project_ids.split(",")]

    asyncio.run(_channels_impl(api_key, proj_ids, json_output))


async def _channels_impl(api_key: str, project_ids: list[str] | None, json_output: bool) -> None:
    """Implementation of channels command."""
    async with BenmoreClient(api_key=api_key) as client:
        try:
            channels_by_project = await client.get_team_channels(project_ids)

            if json_output:
                output = {
                    project_id: [
                        {
                            "name": ch.name,
                            "id": ch.id,
                            "members": ch.member_count,
                            "archived": ch.is_archived,
                        }
                        for ch in channels
                    ]
                    for project_id, channels in channels_by_project.items()
                }
                console.print(json.dumps(output, indent=2))
            else:
                # Pretty print table
                table = Table(title="Slack Channels by Project")
                table.add_column("Project", style="cyan")
                table.add_column("Channel", style="green")
                table.add_column("Members", justify="right")
                table.add_column("Last Message")
                table.add_column("Archived", justify="center")

                for project_id, channels in sorted(channels_by_project.items()):
                    if not channels:
                        table.add_row(project_id, "[dim]No channels[/dim]", "", "", "")
                    for channel in channels:
                        table.add_row(
                            project_id,
                            f"#{channel.name}",
                            str(channel.member_count or "?"),
                            channel.last_message_ts or "—",
                            "✓" if channel.is_archived else "—",
                        )

                console.print(table)

        except Exception as e:
            console.print(f"[red]Error: {escape(str(e))}[/red]")
            sys.exit(1)


@app.command()
def projects(
    ctx: typer.Context,
    search: str = typer.Option(None, "--search", "-q", help="Search query"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List assigned projects or search all projects.

    Examples:
        bm benmore projects
        bm benmore projects --search "api redesign"
        bm benmore projects --json
    """
    if BenmoreClient is None:
        console.print("[red]Error: benmore_client package not installed[/red]")
        sys.exit(1)
    try:
        api_key = _get_api_key()
    except typer.BadParameter as e:
        console.print(f"[red]Error: {escape(str(e))}[/red]")
        sys.exit(1)

    asyncio.run(_projects_impl(api_key, search, json_output))


async def _projects_impl(api_key: str, search: str | None, json_output: bool) -> None:
    """Implementation of projects command."""
    async with BenmoreClient(api_key=api_key) as client:
        try:
            if search:
                response = await client.projects_search(search)
            else:
                response = await client.projects_list()

            if json_output:
                output = [
                    {
                        "id": p.id,
                        "title": p.title,
                        "status": p.status,
                        "phase": p.phase,
                        "team_size": p.team_size,
                    }
                    for p in response.results
                ]
                console.print(json.dumps(output, indent=2))
            else:
                table = Table(title=f"Projects ({response.count})")
                table.add_column("ID", style="cyan")
                table.add_column("Title", style="green")
                table.add_column("Status")
                table.add_column("Phase")
                table.add_column("Team", justify="right")

                for project in response.results:
                    table.add_row(
                        project.id,
                        project.title,
                        project.status or "—",
                        project.phase or "—",
                        str(project.team_size or "?"),
                    )

                console.print(table)

        except Exception as e:
            console.print(f"[red]Error: {escape(str(e))}[/red]")
            sys.exit(1)


@app.command()
def context(
    project_id: str = typer.Argument(..., help="Project ID"),
    full: bool = typer.Option(False, "--full", help="Include full meeting transcripts"),
    days: int = typer.Option(None, "--days", help="Look back N days"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Get complete project context in one call.

    Includes project info, team, meetings, Slack, GitHub, blockers, financials.

    Examples:
        bm benmore context proj123
        bm benmore context proj123 --full --days 30
        bm benmore context proj123 --json
    """
    if BenmoreClient is None:
        console.print("[red]Error: benmore_client package not installed[/red]")
        sys.exit(1)
    try:
        api_key = _get_api_key()
    except typer.BadParameter as e:
        console.print(f"[red]Error: {escape(str(e))}[/red]")
        sys.exit(1)

    asyncio.run(_context_impl(api_key, project_id, full, days, json_output))


async def _context_impl(
    api_key: str, project_id: str, full: bool, days: int | None, json_output: bool
) -> None:
    """Implementation of context command."""
    async with BenmoreClient(api_key=api_key) as client:
        try:
            ctx = await client.projects_context(project_id, full=full, days=days)

            if json_output:
                console.print(json.dumps(ctx.model_dump(), indent=2, default=str))
            else:
                console.print(f"\n[bold cyan]{ctx.title}[/bold cyan]")
                console.print(f"ID: {ctx.id}")
                console.print(f"Phase: {ctx.phase} | Status: {ctx.status}")
                console.print(f"Description: {ctx.description or '—'}\n")

                if ctx.team:
                    console.print("[bold]Team ({}):[/bold]".format(len(ctx.team)))
                    for member in ctx.team:
                        console.print(f"  • {member.name} ({member.username}) - {member.role or 'member'}")

                if ctx.channels:
                    console.print(f"\n[bold]Slack Channels ({len(ctx.channels)}):[/bold]")
                    for channel in ctx.channels:
                        console.print(f"  • #{channel.name} ({channel.member_count or '?'} members)")

                if ctx.meetings:
                    console.print(f"\n[bold]Recent Meetings ({len(ctx.meetings)}):[/bold]")
                    for meeting in ctx.meetings[:5]:
                        console.print(f"  • {meeting.title} ({meeting.date.strftime('%Y-%m-%d')})")
                        if meeting.summary:
                            console.print(f"    {meeting.summary[:100]}...")

                if ctx.blockers:
                    console.print(f"\n[bold yellow]Blockers ({len(ctx.blockers)}):[/bold yellow]")
                    for blocker in ctx.blockers:
                        console.print(f"  • {blocker}")

                if ctx.github_repos:
                    console.print(f"\n[bold]GitHub Repos ({len(ctx.github_repos)}):[/bold]")
                    for repo in ctx.github_repos:
                        console.print(f"  • {repo.get('name', '?')}")

        except Exception as e:
            console.print(f"[red]Error: {escape(str(e))}[/red]")
            sys.exit(1)


@app.command()
def status(
    project_id: str = typer.Argument(..., help="Project ID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Get detailed project status with health indicators.

    Shows completion percentage, blockers, team capacity, financials.

    Examples:
        bm benmore status proj123
        bm benmore status proj123 --json
    """
    if BenmoreClient is None:
        console.print("[red]Error: benmore_client package not installed[/red]")
        sys.exit(1)
    try:
        api_key = _get_api_key()
    except typer.BadParameter as e:
        console.print(f"[red]Error: {escape(str(e))}[/red]")
        sys.exit(1)

    asyncio.run(_status_impl(api_key, project_id, json_output))


async def _status_impl(api_key: str, project_id: str, json_output: bool) -> None:
    """Implementation of status command."""
    async with BenmoreClient(api_key=api_key) as client:
        try:
            status = await client.projects_status(project_id)

            if json_output:
                console.print(json.dumps(status.model_dump(), indent=2, default=str))
            else:
                console.print(f"\n[bold cyan]Project {status.id}[/bold cyan]")
                console.print(f"Phase: {status.phase}")
                console.print(f"Health: {status.health}")
                console.print(f"Completion: {status.completion_percentage or '?'}%")

                if status.blockers:
                    console.print(f"\n[bold yellow]Blockers ({len(status.blockers)}):[/bold yellow]")
                    for blocker in status.blockers:
                        console.print(f"  • {blocker}")

                if status.next_milestone:
                    console.print(f"\n[bold]Next Milestone:[/bold] {status.next_milestone}")

        except Exception as e:
            console.print(f"[red]Error: {escape(str(e))}[/red]")
            sys.exit(1)


@app.command()
def team(
    project_id: str = typer.Argument(..., help="Project ID"),
    role: str = typer.Option(None, "--role", help="Filter by role"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List project team members.

    Examples:
        bm benmore team proj123
        bm benmore team proj123 --role lead
        bm benmore team proj123 --json
    """
    if BenmoreClient is None:
        console.print("[red]Error: benmore_client package not installed[/red]")
        sys.exit(1)
    try:
        api_key = _get_api_key()
    except typer.BadParameter as e:
        console.print(f"[red]Error: {escape(str(e))}[/red]")
        sys.exit(1)

    asyncio.run(_team_impl(api_key, project_id, role, json_output))


async def _team_impl(api_key: str, project_id: str, role: str | None, json_output: bool) -> None:
    """Implementation of team command."""
    async with BenmoreClient(api_key=api_key) as client:
        try:
            members = await client.get_project_team_by_role(project_id, role)

            if json_output:
                output = [
                    {
                        "name": m.name,
                        "username": m.username,
                        "email": m.email,
                        "role": m.role,
                    }
                    for m in members
                ]
                console.print(json.dumps(output, indent=2))
            else:
                table = Table(title=f"Team Members ({len(members)})")
                table.add_column("Name", style="green")
                table.add_column("Username", style="cyan")
                table.add_column("Email")
                table.add_column("Role")

                for member in members:
                    table.add_row(
                        member.name,
                        member.username,
                        member.email,
                        member.role or "—",
                    )

                console.print(table)

        except Exception as e:
            console.print(f"[red]Error: {escape(str(e))}[/red]")
            sys.exit(1)


@app.command(name="list")
def list_projects(
    phase: str = typer.Option(None, "--phase", "-p", help="Filter by phase (implementation, discovery, stalled, completed)"),
    mine: bool = typer.Option(False, "--mine", help="Only show projects you're assigned to"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    working_on: str = typer.Option(None, "--set-working-on", help="Set 'working on' for a project (format: BEN-123:description)"),
    set_phase: str = typer.Option(None, "--set-phase", help="Set phase for a project (format: BEN-123:phase)"),
) -> None:
    """Numbered project list grouped by phase — like the team Slack format.

    Shows all projects grouped by phase (Implementation, Discovery, Stalled,
    Completed) with numbered entries, team members, and channel status.

    Supports updating project metadata inline:
        bm benmore list --set-working-on "BEN-185:Building onboarding flow"
        bm benmore list --set-phase "BEN-166:implementation"

    Examples:
        bm benmore list                         # Full list grouped by phase
        bm benmore list --phase implementation   # Only implementation projects
        bm benmore list --mine                   # Only your assigned projects
        bm benmore list --json                   # JSON output
        bm benmore list --set-working-on "BEN-185:Building API client"
    """
    if BenmoreClient is None:
        console.print("[red]Error: benmore_client package not installed[/red]")
        sys.exit(1)
    try:
        api_key = _get_api_key()
    except typer.BadParameter as e:
        console.print(f"[red]Error: {escape(str(e))}[/red]")
        sys.exit(1)

    asyncio.run(_list_impl(api_key, phase, mine, json_output, working_on, set_phase))


async def _list_impl(
    api_key: str,
    phase_filter: str | None,
    mine: bool,
    json_output: bool,
    working_on: str | None,
    set_phase: str | None,
) -> None:
    """Implementation of list command."""
    from rich.markup import escape

    async with BenmoreClient(api_key=api_key) as client:
        try:
            # Handle inline updates first
            if working_on:
                ben_part, _, description = working_on.partition(":")
                ben_num = ben_part.strip().replace("BEN-", "").replace("ben-", "")
                results = await client.projects_search(f"BEN-{ben_num}")
                if results.results:
                    p = results.results[0]
                    await client.projects_update(p.id, working_on=description.strip())
                    console.print(f"[green]✓ Updated working_on for {p.title}: {description.strip()}[/green]\n")
                else:
                    console.print(f"[yellow]⚠ BEN-{ben_num} not found[/yellow]\n")

            if set_phase:
                ben_part, _, new_phase = set_phase.partition(":")
                ben_num = ben_part.strip().replace("BEN-", "").replace("ben-", "")
                results = await client.projects_search(f"BEN-{ben_num}")
                if results.results:
                    p = results.results[0]
                    await client.projects_update(p.id, phase=new_phase.strip())
                    console.print(f"[green]✓ Updated phase for {p.title}: {new_phase.strip()}[/green]\n")
                else:
                    console.print(f"[yellow]⚠ BEN-{ben_num} not found[/yellow]\n")

            # Get all projects (mine or search all)
            projects = await client.projects_list()
            all_projects = list(projects.results)

            # Enrich with team + channel data — parallel via asyncio.gather (H4)
            enriched = await _enrich_projects_parallel(client, all_projects)
            # The helper returns dicts with team as list of {name, username, role};
            # _list_impl just needs the names list for display.
            for entry in enriched:
                entry["team"] = [m["name"] if isinstance(m, dict) else m for m in entry["team"]]

            # Apply phase filter
            if phase_filter:
                enriched = [e for e in enriched if e["phase"].lower() == phase_filter.lower()]

            # Group by phase
            phase_order = ["implementation", "discovery", "stalled", "completed", "unknown"]
            grouped: dict[str, list[dict]] = {}
            for e in enriched:
                ph = e["phase"]
                if ph not in grouped:
                    grouped[ph] = []
                grouped[ph].append(e)

            if json_output:
                console.print(json.dumps({"projects": enriched, "by_phase": grouped}, indent=2, default=str))
                return

            # Pretty print like Richard's Slack format
            global_num = 0
            total = len(enriched)

            console.print(f"\n[bold cyan]Your Projects ({total})[/bold cyan]\n")

            for phase_name in phase_order:
                if phase_name not in grouped:
                    continue

                items = grouped[phase_name]
                phase_display = phase_name.capitalize()
                phase_color = PHASE_COLORS.get(phase_name, "white")

                console.print(f"[bold {phase_color}]{phase_display} ({len(items)}):[/bold {phase_color}]")

                for entry in sorted(items, key=lambda x: x["title"]):
                    global_num += 1
                    title = escape(entry["title"])
                    team_str = ", ".join(entry["team"][:3])
                    if len(entry["team"]) > 3:
                        team_str += f" +{len(entry['team']) - 3}"

                    # Channel indicator
                    ch_indicator = ""
                    if entry["channel"]:
                        ch_indicator = f" [cyan]💬 {entry['messages']}[/cyan]"

                    console.print(f"  {global_num:>3}. {title}{ch_indicator}")

                    # Show team on second line
                    if team_str:
                        console.print(f"       [dim]{team_str}[/dim]")

                console.print()  # Blank line between phases

            # Print any phases not in our order
            for phase_name, items in grouped.items():
                if phase_name not in phase_order:
                    console.print(f"[bold]{escape(phase_name.capitalize())} ({len(items)}):[/bold]")
                    for entry in sorted(items, key=lambda x: x["title"]):
                        global_num += 1
                        console.print(f"  {global_num:>3}. {escape(entry['title'])}")
                    console.print()

            # Footer with quick actions + workflow prompts
            console.print("[dim]──────────────────────────────────────────────────────[/dim]")
            console.print("[dim]Quick actions:[/dim]")
            console.print("[dim]  bm benmore list --phase implementation     # Filter by phase[/dim]")
            console.print('[dim]  bm benmore list --set-working-on "BEN-185:Building API"[/dim]')
            console.print('[dim]  bm benmore list --set-phase "BEN-166:implementation"[/dim]')
            console.print("[dim]  bm benmore summary $(bm benmore lookup 185 --id) --days 7[/dim]")
            console.print()
            console.print("[dim]Workflow prompts (use in Claude Code):[/dim]")
            for key, wf in list(WORKFLOW_PROMPTS.items())[:5]:
                console.print(f"[dim]  {wf['skill']:32} {wf['description']}[/dim]")

        except Exception as e:
            console.print(f"[red]Error: {escape(str(e))}[/red]")
            sys.exit(1)


@app.command()
def workflows() -> None:
    """Show available workflow prompts for project management.

    Lists all available Claude Code skills and prompts for:
    - PR review (full audit and quick review)
    - QA test planning
    - Finding bugs and valuable additions (client value maximizer)
    - Edge case discovery and user flows
    - Ticket creation and project kickoff

    Examples:
        bm benmore workflows
    """
    console.print("\n[bold cyan]Available Workflow Prompts[/bold cyan]\n")

    table = Table(show_header=True)
    table.add_column("Skill", style="green", min_width=30)
    table.add_column("Description")
    table.add_column("Prompt File", style="dim")

    for key, wf in WORKFLOW_PROMPTS.items():
        prompt_file = wf.get("prompt_path") or "—"
        table.add_row(wf["skill"], wf["description"], prompt_file)

    console.print(table)

    console.print("\n[bold]Usage in Claude Code:[/bold]")
    console.print("  Type the skill name directly (e.g. [green]/full-pr-review-audit[/green])")
    console.print("  Or: [green]/client-value-maximizer[/green] to find quick wins")
    console.print("  Or: [green]/qa-plan[/green] to generate test plans")
    console.print()
    console.print("[bold]Common workflows:[/bold]")
    console.print("  1. Start a project  → [green]/client-kickoff[/green]")
    console.print("  2. Plan features    → [green]/create-project-tickets[/green]")
    console.print("  3. Find edge cases  → [green]/user-flows-with-edge-cases[/green]")
    console.print("  4. Find quick wins  → [green]/client-value-maximizer[/green]")
    console.print("  5. Review code      → [green]/full-pr-review-audit[/green]")
    console.print("  6. QA planning      → [green]/qa-plan[/green]")
    console.print()


@app.command()
def overview(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Single-command dashboard — all projects, teams, channels, health.

    Shows everything at a glance: project list with phase, team members,
    connected Slack channels with message counts, and activity indicators.

    Examples:
        bm benmore overview
        bm benmore overview --json
        bm benmore overview --json | jq '.[] | select(.channel != null)'
    """
    if BenmoreClient is None:
        console.print("[red]Error: benmore_client package not installed[/red]")
        sys.exit(1)
    try:
        api_key = _get_api_key()
    except typer.BadParameter as e:
        console.print(f"[red]Error: {escape(str(e))}[/red]")
        sys.exit(1)

    asyncio.run(_overview_impl(api_key, json_output))


async def _overview_impl(api_key: str, json_output: bool) -> None:
    """Implementation of overview command."""
    import httpx

    async with BenmoreClient(api_key=api_key) as client:
        try:
            projects = await client.projects_list()

            results = []
            for project in projects.results:
                entry: dict[str, Any] = {
                    "id": project.id,
                    "title": project.title,
                    "phase": project.phase,
                    "team": [],
                    "channel": None,
                    "messages": 0,
                    "last_activity": None,
                }

                # Get team
                try:
                    members = await client.team_list(project.id)
                    entry["team"] = [
                        {"name": m.name, "username": m.username, "role": m.role}
                        for m in members
                    ]
                except Exception:
                    pass

                # Get channel
                try:
                    raw = await client.comms_raw(project.id)
                    entry["channel"] = raw.get("channel_id")
                    entry["messages"] = raw.get("total_messages", 0)
                    entry["last_activity"] = raw.get("last_message_at")
                except Exception:
                    pass

                results.append(entry)

            if json_output:
                console.print(json.dumps(results, indent=2, default=str))
            else:
                # Pretty dashboard
                console.print(f"\n[bold cyan]Benmore Dashboard[/bold cyan] — {len(results)} projects\n")

                for entry in results:
                    phase_color = PHASE_COLORS.get(entry["phase"] or "", "white")
                    title = escape(entry["title"])
                    phase = entry["phase"] or "unknown"
                    team_count = len(entry["team"])
                    team_names = ", ".join(m["name"] for m in entry["team"][:4])
                    if team_count > 4:
                        team_names += f" +{team_count - 4}"

                    ch_str = ""
                    if entry["channel"]:
                        ch_str = f" | #{entry['channel']} ({entry['messages']} msgs)"
                    else:
                        ch_str = " | [dim]no channel[/dim]"

                    console.print(
                        f"  [{phase_color}]●[/{phase_color}] "
                        f"[bold]{title}[/bold] "
                        f"[dim]({phase})[/dim]"
                    )
                    console.print(
                        f"    Team: {team_names}{ch_str}"
                    )

                # Summary
                active = sum(1 for r in results if r["phase"] in ("implementation", "discovery"))
                with_channels = sum(1 for r in results if r["channel"])
                total_msgs = sum(r["messages"] for r in results)
                console.print(
                    f"\n  [bold]Summary:[/bold] {active} active, "
                    f"{with_channels} with channels, "
                    f"{total_msgs} total messages"
                )

        except Exception as e:
            console.print(f"[red]Error: {escape(str(e))}[/red]")
            sys.exit(1)


@app.command()
def lookup(
    query: str = typer.Argument(..., help="BEN number (e.g. BEN-166), project name, or partial match"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    id_only: bool = typer.Option(False, "--id", help="Print only the project ID (for piping)"),
) -> None:
    """Resolve a BEN number or project name to a project ID.

    Searches by BEN number, title, or partial match. Returns the project ID
    that can be piped to other commands.

    Examples:
        bm benmore lookup BEN-166
        bm benmore lookup "Jason Steele"
        bm benmore lookup 185
        bm benmore summary $(bm benmore lookup BEN-166 --id) --days 7
    """
    if BenmoreClient is None:
        console.print("[red]Error: benmore_client package not installed[/red]")
        sys.exit(1)
    try:
        api_key = _get_api_key()
    except typer.BadParameter as e:
        console.print(f"[red]Error: {escape(str(e))}[/red]")
        sys.exit(1)

    asyncio.run(_lookup_impl(api_key, query, json_output, id_only))


async def _lookup_impl(api_key: str, query: str, json_output: bool, id_only: bool) -> None:
    """Implementation of lookup command."""
    async with BenmoreClient(api_key=api_key) as client:
        try:
            # Normalize query: "185" → "BEN-185", "BEN-185" stays
            search_q = query.strip()
            if search_q.isdigit():
                search_q = f"BEN-{search_q}"

            results = await client.projects_search(search_q)

            if not results.results:
                # Try original query if BEN-prefix didn't match
                if search_q != query.strip():
                    results = await client.projects_search(query.strip())

            if not results.results:
                console.print(f"[yellow]No projects found for '{query}'[/yellow]")
                sys.exit(1)

            if id_only:
                # Print just the first match ID for piping
                print(results.results[0].id)
                return

            if json_output:
                output = [
                    {"id": p.id, "title": p.title, "phase": p.phase}
                    for p in results.results
                ]
                console.print(json.dumps(output, indent=2, default=str))
            else:
                if len(results.results) == 1:
                    p = results.results[0]
                    console.print(f"[bold green]{p.title}[/bold green]")
                    console.print(f"  ID: [cyan]{p.id}[/cyan]")
                    console.print(f"  Phase: {p.phase or '—'}")
                    console.print(f"\n  [dim]Tip: bm benmore summary {p.id} --days 7[/dim]")
                else:
                    table = Table(title=f"Results for '{query}' ({len(results.results)} matches)")
                    table.add_column("ID", style="cyan")
                    table.add_column("Title", style="green")
                    table.add_column("Phase")

                    for p in results.results:
                        table.add_row(p.id, p.title, p.phase or "—")

                    console.print(table)

        except Exception as e:
            console.print(f"[red]Error: {escape(str(e))}[/red]")
            sys.exit(1)


@app.command()
def summary(
    project_id: str = typer.Argument(..., help="Project ID (use 'bm benmore lookup' to find it)"),
    days: int = typer.Option(7, "--days", "-d", help="Number of days to look back (default: 7)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Get channel summary for a project over a time period.

    Shows Slack channel activity, message counts, active participants,
    and message previews over the specified number of days.

    Examples:
        bm benmore summary proj123 --days 7
        bm benmore summary $(bm benmore lookup 185 --id) --days 30
        bm benmore summary proj123 --days 14 --json
    """
    if BenmoreClient is None:
        console.print("[red]Error: benmore_client package not installed[/red]")
        sys.exit(1)
    try:
        api_key = _get_api_key()
    except typer.BadParameter as e:
        console.print(f"[red]Error: {escape(str(e))}[/red]")
        sys.exit(1)

    asyncio.run(_summary_impl(api_key, project_id, days, json_output))


async def _summary_impl(api_key: str, project_id: str, days: int, json_output: bool) -> None:
    """Implementation of summary command."""
    from datetime import datetime, timedelta, timezone

    async with BenmoreClient(api_key=api_key) as client:
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            # Get project info
            projects = await client.projects_list()
            project_title = project_id
            for p in projects.results:
                if p.id == project_id:
                    project_title = p.title
                    break

            # If not found in assigned, try search
            if project_title == project_id:
                try:
                    search = await client.projects_search(project_id[:8])
                    for p in search.results:
                        if p.id == project_id:
                            project_title = p.title
                            break
                except Exception:
                    pass

            # Get channel data
            try:
                raw = await client.comms_raw(project_id)
            except Exception:
                console.print(f"[yellow]No Slack channel connected to {project_title}[/yellow]")
                return

            channel_id = raw.get("channel_id")
            total_messages = raw.get("total_messages", 0)
            last_message_at = raw.get("last_message_at")
            recent = raw.get("recent_messages", [])

            # Filter messages by date
            filtered = []
            for msg in recent:
                msg_time = msg.get("timestamp")
                if msg_time:
                    try:
                        dt = datetime.fromisoformat(msg_time)
                        if dt >= cutoff:
                            filtered.append(msg)
                    except (ValueError, TypeError):
                        filtered.append(msg)  # Include if can't parse date
                else:
                    filtered.append(msg)

            # Get team
            members: list[Any] = []
            try:
                members = await client.team_list(project_id)
                team_names = {m.username: m.name for m in members}
            except Exception:
                team_names = {}

            # Build participants from messages
            participants = {}
            for msg in filtered:
                user = msg.get("user", "Unknown")
                if user not in participants:
                    participants[user] = 0
                participants[user] += 1

            # Get meetings
            meetings = []
            try:
                meetings_data = await client.comms_meetings(project_id)
                for m in meetings_data:
                    if m.date >= cutoff:
                        meetings.append(m)
            except Exception:
                pass

            if json_output:
                output = {
                    "project_id": project_id,
                    "project_title": project_title,
                    "channel_id": channel_id,
                    "period_days": days,
                    "total_messages": total_messages,
                    "messages_in_period": len(filtered),
                    "last_message_at": last_message_at,
                    "participants": participants,
                    "team": [{"name": m.name, "username": m.username, "role": m.role} for m in (members if team_names else [])],
                    "meetings_in_period": len(meetings),
                    "messages": [
                        {
                            "user": msg.get("user"),
                            "text": msg.get("text"),
                            "timestamp": msg.get("timestamp"),
                            "replies": msg.get("reply_count", 0),
                        }
                        for msg in filtered
                    ],
                }
                console.print(json.dumps(output, indent=2, default=str))
            else:
                console.print(f"\n[bold cyan]{project_title}[/bold cyan]")
                console.print(f"Channel: {channel_id or '(not connected)'}")
                console.print(f"Period: last {days} days")
                console.print(f"Total messages (all time): {total_messages}")
                console.print(f"Messages in period: {len(filtered)}")

                if last_message_at:
                    console.print(f"Last activity: {last_message_at}")

                if team_names:
                    console.print(f"\n[bold]Team ({len(team_names)}):[/bold]")
                    for username, name in team_names.items():
                        msg_count = participants.get(name, 0)
                        activity = f" ({msg_count} msgs)" if msg_count > 0 else ""
                        console.print(f"  • {name} (@{username}){activity}")

                if participants:
                    console.print(f"\n[bold]Active Participants ({len(participants)}):[/bold]")
                    for user, count in sorted(participants.items(), key=lambda x: -x[1]):
                        console.print(f"  • {user}: {count} messages")

                if meetings:
                    console.print(f"\n[bold]Meetings ({len(meetings)}):[/bold]")
                    for m in meetings:
                        console.print(f"  • {m.title} ({m.date.strftime('%Y-%m-%d')})")
                        if m.summary:
                            console.print(f"    {m.summary[:120]}...")

                if filtered:
                    console.print(f"\n[bold]Recent Messages:[/bold]")
                    for msg in filtered[:10]:
                        user = msg.get("user", "?")
                        text = msg.get("text", "")[:100]
                        ts = msg.get("timestamp", "")[:10]
                        replies = msg.get("reply_count", 0)
                        reply_str = f" ({replies} replies)" if replies else ""
                        console.print(f"  [{ts}] {user}: {text}{reply_str}")

                    if len(filtered) > 10:
                        console.print(f"  [dim]... and {len(filtered) - 10} more messages[/dim]")

                if not filtered and not meetings:
                    console.print(f"\n[yellow]No activity in the last {days} days.[/yellow]")

        except Exception as e:
            console.print(f"[red]Error: {escape(str(e))}[/red]")
            sys.exit(1)


if __name__ == "__main__":
    app()
