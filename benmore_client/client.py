"""Benmore API v2 Client - Main async HTTP client.

Type-safe, comprehensive client for the Benmore project management platform.
Supports projects, communications, planning, and team management.

Base URL: https://client.benmore.tech/api/v1/
Auth: X-API-KEY header
"""

from __future__ import annotations

from typing import Any, Optional

import httpx

from benmore_client.models import (
    Channel,
    Document,
    GitHubBoard,
    Meeting,
    Project,
    ProjectContext,
    ProjectListResponse,
    ProjectStatus,
    TeamMember,
)


class BenmoreClient:
    """Async HTTP client for Benmore API v2.

    Example:
        async with BenmoreClient(api_key="bpk_...") as client:
            projects = await client.projects_list()
            context = await client.projects_context("project-id")

    Scopes:
        - projects:read — List projects, view context, team
        - projects:write — Update project status, create items
        - flash-documents:read — List flash documents
        - flash-documents:write — Create/edit flash documents
    """

    BASE_URL = "https://client.benmore.tech/api/v1"

    def __init__(
        self,
        api_key: str,
        base_url: str = BASE_URL,
        timeout: float = 30.0,
        verify_ssl: bool = True,
    ):
        """Initialize Benmore API client.

        Args:
            api_key: Benmore API key (format: bpk_*)
            base_url: API base URL (defaults to production)
            timeout: Request timeout in seconds
            verify_ssl: Verify SSL certificates
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> BenmoreClient:
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            verify=self.verify_ssl,
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _headers(self) -> dict[str, str]:
        """Get request headers with authentication."""
        return {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Make an API request.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            path: URL path (appended to BASE_URL)
            params: Query parameters
            json: Request body (JSON)

        Returns:
            Response data (dict or parsed model)

        Raises:
            httpx.HTTPError: Network or HTTP error
        """
        if self._client is None:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        url = f"{self.base_url}{path}"
        response = await self._client.request(
            method,
            url,
            params=params,
            json=json,
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _validate_path_param(value: str, name: str) -> None:
        """Validate a URL path parameter is safe to interpolate.

        Args:
            value: The parameter value to validate
            name: Parameter name (for error messages)

        Raises:
            ValueError: If value is empty or contains /, ?, or #
        """
        if not value:
            raise ValueError(f"{name} must not be empty")
        if any(ch in value for ch in ("/"  , "?", "#")):
            raise ValueError(f"{name} contains invalid characters: {value!r}")

    @staticmethod
    def _unwrap_results(data: Any, key: str = "results") -> list[Any]:
        """Extract a list from a paginated response or bare list.

        Args:
            data: Raw API response (dict with key, or bare list)
            key: Dict key to look up (default "results")

        Returns:
            List of items
        """
        if isinstance(data, list):
            return data
        return data.get(key, data)

    # ─── Projects ───────────────────────────────────────────────────

    async def projects_list(self) -> ProjectListResponse:
        """GET /projects/ — List your assigned projects.

        Returns paginated list of projects with summary info.
        """
        data = await self._request("GET", "/projects/")
        # Handle both list and dict responses
        if isinstance(data, list):
            return ProjectListResponse(results=[Project(**p) for p in data], count=len(data))
        return ProjectListResponse(**data)

    async def projects_search(self, q: str) -> ProjectListResponse:
        """GET /projects/search/?q=QUERY — Search all projects.

        Search by title or description. Full-text search across project metadata.

        Args:
            q: Search query

        Returns:
            ProjectListResponse with matching projects
        """
        data = await self._request("GET", "/projects/search/", params={"q": q})
        # Handle both list and dict responses
        if isinstance(data, list):
            return ProjectListResponse(results=[Project(**p) for p in data], count=len(data))
        return ProjectListResponse(**data)

    async def projects_summary(self) -> dict[str, Any]:
        """GET /projects/summary/ — Get active projects overview.

        Returns health indicators, active count, blockers, team capacity summary.
        Useful for dashboards and at-a-glance project health.
        """
        return await self._request("GET", "/projects/summary/")

    # ─── Project Context ────────────────────────────────────────────

    async def projects_context(
        self,
        project_id: str,
        full: bool = False,
        days: Optional[int] = None,
    ) -> ProjectContext:
        """GET /projects/<id>/context/ — Get full project context in one call.

        The "golden record" endpoint that combines:
        - Project info, team, meetings, Slack, GitHub, blockers, financials

        Args:
            project_id: Project ID
            full: Include raw meeting transcripts (default: False, summaries only)
            days: Look back N days in history (default: no limit)

        Returns:
            ProjectContext with all nested data
        """
        self._validate_path_param(project_id, "project_id")
        params = {}
        if full:
            params["full"] = "true"
        if days is not None:
            params["days"] = days

        data = await self._request("GET", f"/projects/{project_id}/context/", params=params)
        return ProjectContext(**data)

    async def projects_status(self, project_id: str) -> ProjectStatus:
        """GET /projects/<id>/status/ — Get detailed project status.

        Includes kanban board state, financial metrics, health indicators.
        """
        self._validate_path_param(project_id, "project_id")
        data = await self._request("GET", f"/projects/{project_id}/status/")
        return ProjectStatus(**data)

    async def projects_assets(self, project_id: str) -> dict[str, Any]:
        """GET /projects/<id>/assets/ — Get all project assets in one response.

        Returns documents, diagrams, dynamic assets, signature docs.
        """
        self._validate_path_param(project_id, "project_id")
        return await self._request("GET", f"/projects/{project_id}/assets/")

    async def projects_update(
        self,
        project_id: str,
        phase: Optional[str] = None,
        working_on: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Project:
        """PATCH /projects/<id>/update/ — Update project metadata.

        Args:
            project_id: Project ID
            phase: New phase (discovery, planning, development, etc.)
            working_on: What the team is currently working on
            description: Updated description

        Returns:
            Updated Project model
        """
        self._validate_path_param(project_id, "project_id")
        json_data = {}
        if phase is not None:
            json_data["phase"] = phase
        if working_on is not None:
            json_data["working_on"] = working_on
        if description is not None:
            json_data["description"] = description

        data = await self._request("PATCH", f"/projects/{project_id}/update/", json=json_data)
        return Project(**data)

    # ─── Team ──────────────────────────────────────────────────────

    async def team_list(self, project_id: str) -> list[TeamMember]:
        """GET /projects/<id>/team/ — List project team members.

        Returns all team members with roles and contact info.
        API returns: {project_id, project_title, team_members: [{username, name, title}]}
        """
        self._validate_path_param(project_id, "project_id")
        data = await self._request("GET", f"/projects/{project_id}/team/")
        # API returns {team_members: [...]} with username/name/title fields
        members_raw = data.get("team_members", data.get("results", data))
        if isinstance(members_raw, list):
            result = []
            for m in members_raw:
                if isinstance(m, str):
                    result.append(TeamMember(id=m, username=m, name=m, email=""))
                elif isinstance(m, dict):
                    result.append(TeamMember(
                        id=m.get("username", ""),
                        username=m.get("username", ""),
                        name=m.get("name", ""),
                        email=m.get("email", ""),
                        role=m.get("title", m.get("role")),
                    ))
            return result
        return []

    async def team_add(
        self,
        project_id: str,
        usernames: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """POST /projects/<id>/team/ — Add team member(s).

        If usernames is empty, adds the authenticated user.
        If usernames is provided (superuser only), adds those users.

        Args:
            project_id: Project ID
            usernames: Usernames to add (optional)

        Returns:
            Success response
        """
        self._validate_path_param(project_id, "project_id")
        json_data = {}
        if usernames:
            json_data["usernames"] = usernames

        return await self._request("POST", f"/projects/{project_id}/team/", json=json_data)

    async def team_remove(
        self,
        project_id: str,
        usernames: list[str],
    ) -> dict[str, Any]:
        """DELETE /projects/<id>/team/ — Remove team members.

        Args:
            project_id: Project ID
            usernames: Usernames to remove

        Returns:
            Success response
        """
        self._validate_path_param(project_id, "project_id")
        return await self._request(
            "DELETE",
            f"/projects/{project_id}/team/",
            json={"usernames": usernames},
        )

    # ─── Communications (Slack) ────────────────────────────────────

    async def comms_channel_info(self, project_id: str) -> Channel:
        """GET /projects/<id>/comms/ — Get Slack channel info.

        API returns: {channel_id, total_messages, last_message_at, recent_messages, source}
        or {error: "No Slack channel connected..."} with 404.
        """
        self._validate_path_param(project_id, "project_id")
        data = await self._request("GET", f"/projects/{project_id}/comms/")
        # Map API fields to Channel model
        return Channel(
            id=data.get("channel_id", ""),
            name=data.get("channel_name", data.get("channel_id", "")),
            total_messages=data.get("total_messages"),
            last_message_ts=data.get("last_message_at"),
            is_archived=False,
        )

    async def comms_raw(self, project_id: str) -> dict[str, Any]:
        """GET /projects/<id>/comms/ — Get raw Slack channel data.

        Returns the raw API response including recent_messages.
        """
        self._validate_path_param(project_id, "project_id")
        return await self._request("GET", f"/projects/{project_id}/comms/")

    async def comms_channel_connect(
        self,
        project_id: str,
        channel_id: str,
    ) -> Channel:
        """PATCH /projects/<id>/comms/ — Connect Slack channel.

        Bot automatically joins the channel and starts syncing.

        Args:
            project_id: Project ID
            channel_id: Slack channel ID

        Returns:
            Updated channel info
        """
        self._validate_path_param(project_id, "project_id")
        data = await self._request(
            "PATCH",
            f"/projects/{project_id}/comms/",
            json={"channel_id": channel_id},
        )
        return Channel(**data)

    async def comms_messages(
        self,
        project_id: str,
        limit: int = 50,
        before: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """GET /projects/<id>/comms/messages/ — Get Slack message history.

        Paginated message history for the project's connected Slack channel.

        Args:
            project_id: Project ID
            limit: Message limit per page
            before: Message timestamp (for pagination)

        Returns:
            List of message objects
        """
        self._validate_path_param(project_id, "project_id")
        params: dict[str, Any] = {"limit": limit}
        if before:
            params["before"] = before

        data = await self._request("GET", f"/projects/{project_id}/comms/messages/", params=params)
        return self._unwrap_results(data)

    async def comms_message_post(
        self,
        project_id: str,
        text: str,
    ) -> dict[str, Any]:
        """POST /projects/<id>/comms/messages/ — Post message to Slack.

        Posts to the project's connected Slack channel.

        Args:
            project_id: Project ID
            text: Message text (Slack markdown supported)

        Returns:
            Posted message details
        """
        self._validate_path_param(project_id, "project_id")
        return await self._request(
            "POST",
            f"/projects/{project_id}/comms/messages/",
            json={"text": text},
        )

    async def comms_thread_read(
        self,
        project_id: str,
        ts: str,
    ) -> list[dict[str, Any]]:
        """GET /projects/<id>/comms/thread/<ts>/ — Get thread replies.

        Args:
            project_id: Project ID
            ts: Parent message timestamp

        Returns:
            List of thread replies
        """
        self._validate_path_param(project_id, "project_id")
        data = await self._request("GET", f"/projects/{project_id}/comms/thread/{ts}/")
        return self._unwrap_results(data)

    async def comms_meetings(
        self,
        project_id: str,
        full: bool = False,
    ) -> list[Meeting]:
        """GET /projects/<id>/comms/meetings/ — Get project meetings.

        Returns meetings with AI-generated summaries. Pass full=true for transcripts.

        Args:
            project_id: Project ID
            full: Include raw transcripts

        Returns:
            List of Meeting models
        """
        self._validate_path_param(project_id, "project_id")
        params = {}
        if full:
            params["full"] = "true"

        data = await self._request("GET", f"/projects/{project_id}/comms/meetings/", params=params)
        results = self._unwrap_results(data)
        return [Meeting(**m) for m in results] if isinstance(results, list) else []

    async def comms_meeting_create(
        self,
        project_id: str,
        title: str,
        date: str,
        duration_minutes: Optional[int] = None,
        attendees: Optional[list[str]] = None,
    ) -> Meeting:
        """POST /projects/<id>/comms/meetings/ — Create meeting record.

        Args:
            project_id: Project ID
            title: Meeting title
            date: Meeting date (ISO 8601 format)
            duration_minutes: Duration in minutes
            attendees: List of attendee names

        Returns:
            Created Meeting model
        """
        self._validate_path_param(project_id, "project_id")
        json_data: dict[str, Any] = {
            "title": title,
            "date": date,
        }
        if duration_minutes is not None:
            json_data["duration_minutes"] = duration_minutes
        if attendees is not None:
            json_data["attendees"] = attendees

        data = await self._request(
            "POST",
            f"/projects/{project_id}/comms/meetings/",
            json=json_data,
        )
        return Meeting(**data)

    # ─── Planning (GitHub Projects) ─────────────────────────────────

    async def github_board(self, project_id: str) -> GitHubBoard:
        """GET /projects/<id>/github/ — Get GitHub Project board data.

        Returns items, status counts, iterations, team capacity.
        """
        self._validate_path_param(project_id, "project_id")
        data = await self._request("GET", f"/projects/{project_id}/github/")
        return GitHubBoard(**data)

    async def github_connect(
        self,
        project_id: str,
        github_project_id: str,
    ) -> GitHubBoard:
        """PATCH /projects/<id>/github/ — Connect GitHub Project.

        Links a GitHub Project to this project for board tracking.

        Args:
            project_id: Project ID
            github_project_id: GitHub Project ID (numeric)

        Returns:
            Connected board data
        """
        self._validate_path_param(project_id, "project_id")
        data = await self._request(
            "PATCH",
            f"/projects/{project_id}/github/",
            json={"github_project_id": github_project_id},
        )
        return GitHubBoard(**data)

    async def github_item_create(
        self,
        project_id: str,
        title: str,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        size: Optional[str] = None,
    ) -> dict[str, Any]:
        """POST /projects/<id>/github/items/ — Create ticket.

        Creates a GitHub Project ticket with status, priority, size estimates.

        Args:
            project_id: Project ID
            title: Ticket title
            status: Ticket status (e.g., "Todo", "In Progress", "Done")
            priority: Priority (critical, high, medium, low)
            size: Story size (xs, s, m, l, xl, xxl)

        Returns:
            Created item details
        """
        self._validate_path_param(project_id, "project_id")
        json_data = {"title": title}
        if status:
            json_data["status"] = status
        if priority:
            json_data["priority"] = priority
        if size:
            json_data["size"] = size

        return await self._request(
            "POST",
            f"/projects/{project_id}/github/items/",
            json=json_data,
        )

    async def github_item_update(
        self,
        project_id: str,
        item_id: str,
        field: str,
        value: str,
    ) -> dict[str, Any]:
        """PATCH /projects/<id>/github/items/ — Update item field.

        Args:
            project_id: Project ID
            item_id: GitHub item ID
            field: Field to update (status, priority, size, etc.)
            value: New value

        Returns:
            Updated item details
        """
        self._validate_path_param(project_id, "project_id")
        return await self._request(
            "PATCH",
            f"/projects/{project_id}/github/items/",
            json={"item_id": item_id, "field": field, "value": value},
        )

    async def github_item_delete(
        self,
        project_id: str,
        item_id: str,
    ) -> dict[str, Any]:
        """DELETE /projects/<id>/github/items/ — Remove item.

        Args:
            project_id: Project ID
            item_id: GitHub item ID

        Returns:
            Success response
        """
        self._validate_path_param(project_id, "project_id")
        return await self._request(
            "DELETE",
            f"/projects/{project_id}/github/items/",
            json={"item_id": item_id},
        )

    async def github_repos(self, project_id: str) -> list[dict[str, Any]]:
        """GET /projects/<id>/github/repos/ — List linked repos.

        Returns commits, lines of code, PRs, contributors per repo.
        """
        self._validate_path_param(project_id, "project_id")
        data = await self._request("GET", f"/projects/{project_id}/github/repos/")
        return self._unwrap_results(data)

    async def github_repo_link(
        self,
        project_id: str,
        repo_url: str,
    ) -> dict[str, Any]:
        """POST /projects/<id>/github/repos/ — Link a repo.

        Args:
            project_id: Project ID
            repo_url: GitHub repo URL

        Returns:
            Linked repo details
        """
        return await self._request(
            "POST",
            f"/projects/{project_id}/github/repos/",
            json={"url": repo_url},
        )

    async def github_repo_unlink(
        self,
        project_id: str,
        repo_id: str,
    ) -> dict[str, Any]:
        """DELETE /projects/<id>/github/repos/ — Unlink a repo.

        Args:
            project_id: Project ID
            repo_id: Repository ID to unlink

        Returns:
            Success response
        """
        return await self._request(
            "DELETE",
            f"/projects/{project_id}/github/repos/",
            json={"repo_id": repo_id},
        )

    # ─── Flash Documents (Global) ───────────────────────────────────

    async def flash_documents_list(self) -> list[Document]:
        """GET /flash-documents/ — List your flash documents.

        Flash documents are global (not project-scoped).

        Returns:
            List of Document models
        """
        data = await self._request("GET", "/flash-documents/")
        # Handle both list and dict responses
        if isinstance(data, list):
            results = data
        else:
            results = data.get("results", [])
        return [Document(**d) for d in results] if isinstance(results, list) else []

    async def flash_documents_create(
        self,
        title: str,
        content: Optional[str] = None,
        doc_type: Optional[str] = None,
    ) -> Document:
        """POST /flash-documents/ — Create a flash document.

        Args:
            title: Document title
            content: Document content
            doc_type: Document type (specification, proposal, etc.)

        Returns:
            Created Document model
        """
        json_data = {"title": title}
        if content:
            json_data["content"] = content
        if doc_type:
            json_data["type"] = doc_type

        data = await self._request("POST", "/flash-documents/", json=json_data)
        return Document(**data)

    async def flash_documents_get(self, slug: str) -> Document:
        """GET /flash-documents/<slug>/ — Get a flash document.

        Args:
            slug: Document slug

        Returns:
            Document model
        """
        data = await self._request("GET", f"/flash-documents/{slug}/")
        return Document(**data)

    async def flash_documents_update(
        self,
        slug: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
    ) -> Document:
        """PATCH /flash-documents/<slug>/ — Update a flash document.

        Args:
            slug: Document slug
            title: New title
            content: New content

        Returns:
            Updated Document model
        """
        json_data = {}
        if title:
            json_data["title"] = title
        if content:
            json_data["content"] = content

        data = await self._request("PATCH", f"/flash-documents/{slug}/", json=json_data)
        return Document(**data)

    async def flash_documents_delete(self, slug: str) -> dict[str, Any]:
        """DELETE /flash-documents/<slug>/ — Delete a flash document.

        Args:
            slug: Document slug

        Returns:
            Success response
        """
        return await self._request("DELETE", f"/flash-documents/{slug}/")

    # ─── Convenience Methods ────────────────────────────────────────

    async def get_team_channels(
        self,
        project_ids: Optional[list[str]] = None,
    ) -> dict[str, list[Channel]]:
        """Get all Slack channels for specified projects.

        Convenience method to fetch channels across multiple projects.

        Args:
            project_ids: Project IDs (if None, fetches all assigned projects)

        Returns:
            Dict mapping project_id -> list of channels
        """
        if project_ids is None:
            projects = await self.projects_list()
            project_ids = [p.id for p in projects.results]

        channels_by_project: dict[str, list[Channel]] = {}
        for project_id in project_ids:
            try:
                channel = await self.comms_channel_info(project_id)
                channels_by_project[project_id] = [channel]
            except Exception:
                # Project may not have a connected channel
                channels_by_project[project_id] = []

        return channels_by_project

    async def get_project_team_by_role(
        self,
        project_id: str,
        role: Optional[str] = None,
    ) -> list[TeamMember]:
        """Get project team members, optionally filtered by role.

        Args:
            project_id: Project ID
            role: Filter by role (optional)

        Returns:
            List of TeamMember models
        """
        members = await self.team_list(project_id)
        if role:
            return [m for m in members if m.role == role]
        return members
