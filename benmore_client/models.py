"""Pydantic models for Benmore API responses.

Type-safe data structures with validation for all Benmore API entities:
- Projects and project context
- Team members and communication channels
- Meetings, documents, and GitHub planning

All models use ``extra="allow"`` and have nullable fields by default. The
Benmore API has historically returned slightly different shapes per endpoint
(some wrap responses in ``{"project": {...}}``, some return ``{"error": "..."}``
with HTTP 200 instead of 404, some use ``title`` where the model expects
``role``). Defensive defaults let the client tolerate that drift without
crashing on a Pydantic ``ValidationError``.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TeamMember(BaseModel):
    """Project team member.

    The Benmore API team endpoints return ``{username, name, title}`` —
    no ``id`` and no ``email``. We coerce ``title`` → ``role`` and fall
    back to ``username`` for ``id`` so callers can address members by a
    stable identifier.
    """

    id: Optional[str] = None
    username: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    joined_at: Optional[datetime] = None

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="before")
    @classmethod
    def _coerce_api_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        coerced = dict(data)
        # API uses `title` for role string (e.g., "Senior Fullstack Developer").
        if coerced.get("role") is None and coerced.get("title") is not None:
            coerced["role"] = coerced["title"]
        # API never returns `id`; fall back to `username`.
        if coerced.get("id") is None and coerced.get("username"):
            coerced["id"] = coerced["username"]
        return coerced


class Channel(BaseModel):
    """Slack channel linked to a project.

    The comms endpoint returns ``{channel_id, total_messages, last_message_at,
    recent_messages}`` — different field names than what early versions of
    this client expected. We accept either spelling.
    """

    id: Optional[str] = None
    name: Optional[str] = None
    topic: Optional[str] = None
    purpose: Optional[str] = None
    member_count: Optional[int] = None
    last_message_ts: Optional[str] = None
    is_archived: bool = False
    total_messages: Optional[int] = None
    members: Optional[list[str]] = None

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="before")
    @classmethod
    def _coerce_api_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        coerced = dict(data)
        if coerced.get("id") is None and coerced.get("channel_id"):
            coerced["id"] = coerced["channel_id"]
        if coerced.get("name") is None:
            coerced["name"] = coerced.get("channel_name") or coerced.get("channel_id")
        if coerced.get("last_message_ts") is None and coerced.get("last_message_at"):
            coerced["last_message_ts"] = coerced["last_message_at"]
        return coerced


class Meeting(BaseModel):
    """Meeting record with optional transcript.

    The API sometimes returns ``id`` as an integer (e.g. ``1639``) and uses
    ``date_time``/``overview`` instead of ``date``/``summary``. The validator
    coerces integer ids to strings and maps the alternate field names so
    callers don't have to juggle multiple shapes.
    """

    id: Optional[str] = None
    title: Optional[str] = None
    date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    summary: Optional[str] = None
    transcript: Optional[str] = None
    attendees: list[str] = Field(default_factory=list)
    recording_url: Optional[str] = None
    has_transcript: Optional[bool] = None
    keywords: list[str] = Field(default_factory=list)
    action_items: Optional[str] = None

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="before")
    @classmethod
    def _coerce_api_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        coerced = dict(data)
        # API returns id as an integer (e.g. 1639); coerce to string
        if coerced.get("id") is not None and not isinstance(coerced["id"], str):
            coerced["id"] = str(coerced["id"])
        # API uses `date_time` instead of `date`
        if coerced.get("date") is None:
            for alt in ("date_time", "meeting_date", "scheduled_at", "started_at", "created_at"):
                if coerced.get(alt):
                    coerced["date"] = coerced[alt]
                    break
        # API uses `overview` instead of `summary`
        if coerced.get("summary") is None and coerced.get("overview"):
            coerced["summary"] = coerced["overview"]
        return coerced


class Document(BaseModel):
    """Project document or asset."""

    id: Optional[str] = None
    title: Optional[str] = None
    type: Optional[str] = None
    content: Optional[str] = None
    url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    owner: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class ProjectStatus(BaseModel):
    """Detailed project status.

    The /status/ endpoint returns ``{project: {...}, team_members: [...], ...}``;
    we flatten ``project`` into the top level via the validator below so callers
    can access ``status.id`` / ``status.title`` directly.
    """

    id: Optional[str] = None
    title: Optional[str] = None
    phase: Optional[str] = None
    phase_display: Optional[str] = None
    health: Optional[str] = None
    completion_percentage: Optional[float] = None
    # /status/ returns blockers as ``{unresolved: [...], total_unresolved: N}``
    # — a dict, not a list. /context/ returns blockers as a list. Accept Any
    # so both shapes round-trip cleanly; callers can introspect on type.
    blockers: Any = None
    next_milestone: Optional[str] = None
    team_members: list[TeamMember] = Field(default_factory=list)
    finances: Optional[dict[str, Any]] = None
    financials: Optional[dict[str, Any]] = None

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="before")
    @classmethod
    def _flatten_project(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "project" in data and isinstance(data["project"], dict):
            flat: dict[str, Any] = dict(data["project"])
            for k, v in data.items():
                if k != "project":
                    flat[k] = v
            return flat
        return data


class ProjectContext(BaseModel):
    """Complete project context (golden record).

    The /context/ endpoint returns:
        {
          "project":   {id, title, description, phase, ...},
          "team":      [{username, name, title}],
          "meetings":  {count_7d, count_total, items: [...]},
          "slack":     null | {...},
          "github":    null | {...},
          "blockers":  [{issue, owner, severity}],
          "open_questions": [{question, raised_by}],
          "financials": {overdue_count, total_invoices, total_outstanding}
        }

    The validator flattens ``project`` and unwraps ``meetings.items`` so
    callers can access fields directly on the model.
    """

    id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    phase: Optional[str] = None
    phase_display: Optional[str] = None
    working_on: Optional[str] = None
    kickoff_date: Optional[str] = None
    implementation_date: Optional[str] = None
    is_deployed: Optional[bool] = None

    team: list[TeamMember] = Field(default_factory=list)
    channels: list[Channel] = Field(default_factory=list)
    meetings: list[Meeting] = Field(default_factory=list)
    blockers: list[Any] = Field(default_factory=list)
    open_questions: list[Any] = Field(default_factory=list)
    github_repos: list[dict[str, Any]] = Field(default_factory=list)
    documents: list[Document] = Field(default_factory=list)

    slack: Optional[dict[str, Any]] = None
    github: Optional[dict[str, Any]] = None
    financials: Optional[dict[str, Any]] = None

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="before")
    @classmethod
    def _flatten_and_unwrap(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        flat: dict[str, Any] = {}

        # Promote project sub-object to top level
        project = data.get("project")
        if isinstance(project, dict):
            flat.update(project)

        # Carry over top-level keys (overriding any duplicates from project)
        for k, v in data.items():
            if k == "project":
                continue
            flat[k] = v

        # Meetings come back as {count_7d, count_total, items: [...]} OR
        # {count, meetings: [...]}; normalize to a flat list
        meetings_obj = flat.get("meetings")
        if isinstance(meetings_obj, dict):
            flat["meetings"] = (
                meetings_obj.get("items")
                or meetings_obj.get("meetings")
                or meetings_obj.get("results")
                or []
            )
        elif meetings_obj is None:
            flat["meetings"] = []

        return flat


class Project(BaseModel):
    """Project summary with key metadata.

    Mirrors the /projects/ list endpoint shape.
    """

    id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    phase: Optional[str] = None
    phase_display: Optional[str] = None
    working_on: Optional[str] = None
    kickoff_date: Optional[str] = None
    implementation_date: Optional[str] = None
    completion_date: Optional[str] = None
    is_deployed: Optional[bool] = None
    owner: Optional[str] = None
    team_size: Optional[int] = None
    team_members: list[TeamMember] = Field(default_factory=list)
    asset_counts: Optional[dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    url: Optional[str] = None

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="before")
    @classmethod
    def _derive_team_size(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        coerced = dict(data)
        if coerced.get("team_size") is None and isinstance(coerced.get("team_members"), list):
            coerced["team_size"] = len(coerced["team_members"])
        return coerced


class ProjectListResponse(BaseModel):
    """Paginated list of projects."""

    results: list[Project] = Field(default_factory=list)
    count: int = 0
    next: Optional[str] = None
    previous: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class GitHubBoard(BaseModel):
    """GitHub Project board with items and status."""

    id: Optional[str] = None
    title: Optional[str] = None
    items: list[dict[str, Any]] = Field(default_factory=list)
    status_counts: Optional[dict[str, int]] = None
    iterations: list[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")
