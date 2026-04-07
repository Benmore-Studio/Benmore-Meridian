#!/usr/bin/env python3
"""Benmore Team Channels Query

Fetch all Slack channels for specified team members from Benmore API.
Shows which channels each person is active in across all projects.

Usage:
    python3 scripts/benmore_team_channels.py --members arkashjain,connor,alex_dunne,alex_titov
    python3 scripts/benmore_team_channels.py --all  # All team members
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    from benmore_client import BenmoreClient
except ImportError:
    print("Error: benmore_client not installed. Install with: pip install -e .", file=sys.stderr)
    sys.exit(1)

# Team members to query
TEAM_MEMBERS = {
    "arkashjain": "Arkash Jain",
    "connor": "Connor",
    "alex_dunne": "Alex Dunne",
    "alex_titov": "Alex Titov",
}


async def get_api_key() -> str:
    """Get API key from environment or config."""
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
        except Exception as e:
            print(f"Warning: Could not read config file: {e}", file=sys.stderr)

    raise RuntimeError(
        "No API key found. Set BM_API_KEY env var or create ~/.benmore/config with api_key"
    )


async def get_all_projects(client: BenmoreClient) -> list[dict[str, Any]]:
    """Get all projects the authenticated user has access to."""
    response = await client.projects_list()
    return [
        {"id": p.id, "title": p.title, "team_size": p.team_size}
        for p in response.results
    ]


async def get_project_channels(
    client: BenmoreClient,
    project_id: str,
) -> tuple[str, dict[str, Any] | None]:
    """Get the Slack channel for a project.

    Returns: (project_id, channel_dict or None)
    """
    try:
        channel = await client.comms_channel_info(project_id)
        return (
            project_id,
            {
                "name": channel.name,
                "id": channel.id,
                "members": channel.member_count or 0,
                "archived": channel.is_archived,
                "last_message": channel.last_message_ts,
            },
        )
    except Exception:
        # Project may not have a connected channel
        return (project_id, None)


async def get_project_team(
    client: BenmoreClient,
    project_id: str,
) -> list[str]:
    """Get list of team member usernames in a project."""
    try:
        members = await client.team_list(project_id)
        return [m.username for m in members]
    except Exception:
        return []


async def main() -> None:
    """Main entry point."""
    try:
        api_key = await get_api_key()
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    async with BenmoreClient(api_key=api_key) as client:
        print("Fetching projects...")
        projects = await get_all_projects(client)
        print(f"Found {len(projects)} projects\n")

        # Get all channels in parallel
        print("Fetching Slack channels...")
        channel_tasks = [get_project_channels(client, p["id"]) for p in projects]
        channel_results = await asyncio.gather(*channel_tasks)
        channels_by_project = {proj_id: ch for proj_id, ch in channel_results}

        # Get all team rosters in parallel
        print("Fetching team rosters...")
        team_tasks = [get_project_team(client, p["id"]) for p in projects]
        team_results = await asyncio.gather(*team_tasks)
        teams_by_project = {p["id"]: team for p, team in zip(projects, team_results)}

        # Build channel -> members mapping
        channels_to_members: dict[str, set[str]] = {}
        project_names: dict[str, str] = {}

        for project in projects:
            proj_id = project["id"]
            channel = channels_by_project.get(proj_id)
            team = teams_by_project.get(proj_id, [])

            if channel:
                channel_name = channel["name"]
                key = f"#{channel_name}"
                if key not in channels_to_members:
                    channels_to_members[key] = set()
                channels_to_members[key].update(team)
                project_names[key] = project["title"]

        # Print results
        print("\n" + "=" * 80)
        print("CHANNELS YOUR TEAM IS IN".center(80))
        print("=" * 80 + "\n")

        # Group by team member
        member_channels: dict[str, set[str]] = {}
        for team_member_key in TEAM_MEMBERS:
            member_channels[team_member_key] = set()

        for channel, members in channels_to_members.items():
            for member_key, member_name in TEAM_MEMBERS.items():
                if member_key in members or member_name.lower() in str(members).lower():
                    member_channels[member_key].add(channel)

        # Print per-member summary
        for member_key, member_name in TEAM_MEMBERS.items():
            channels = sorted(member_channels[member_key])
            print(f"\n**{member_name}**  ({member_key})")
            print("  " + "─" * 70)
            if channels:
                for channel in channels:
                    project = project_names.get(channel, "Unknown")
                    print(f"  • {channel:30} → {project}")
            else:
                print("  (No channels found)")

        # Overall statistics
        print("\n" + "=" * 80)
        print("SUMMARY".center(80))
        print("=" * 80)
        print(f"\nTotal projects:     {len(projects)}")
        print(f"Total channels:     {len(channels_to_members)}")
        print(f"Channels:           {', '.join(sorted(channels_to_members.keys()))}\n")

        # All unique members across all channels
        all_members = set()
        for members in channels_to_members.values():
            all_members.update(members)

        print(f"Team members in channels: {len(all_members)}")
        for member in sorted(all_members):
            in_how_many = sum(1 for ch_members in channels_to_members.values() if member in ch_members)
            marker = " ← You" if member in TEAM_MEMBERS else ""
            print(f"  • {member:30} ({in_how_many} channels){marker}")

        # JSON output for scripting
        json_output = {
            "projects": {p["id"]: p["title"] for p in projects},
            "channels": {
                ch: {
                    "members": sorted(list(members)),
                    "project": project_names.get(ch),
                }
                for ch, members in channels_to_members.items()
            },
            "team_channels": {
                member_key: sorted(list(channels))
                for member_key, channels in member_channels.items()
            },
        }

        # Save JSON for reference
        output_file = Path(__file__).parent.parent / "benmore_team_channels.json"
        with output_file.open("w") as f:
            json.dump(json_output, f, indent=2)
        print(f"\nJSON output saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
