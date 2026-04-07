"""Pydantic models for Benmore API responses.

Type-safe data structures with validation for all Benmore API entities:
- Projects and project context
- Team members and communication channels
- Meetings, documents, and GitHub planning
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, HttpUrl


class TeamMember(BaseModel):
    """Project team member with role and contact info.

    Attributes:
        id: Unique member identifier
        username: Benmore username
        name: Full name
        email: Email address
        role: Role in project (e.g., "lead", "developer", "designer")
        joined_at: When member was added to project
    """

    id: str
    username: str
    name: str
    email: str
    role: Optional[str] = None
    joined_at: Optional[datetime] = None

    class Config:
        extra = "allow"


class Channel(BaseModel):
    """Slack channel linked to a project.

    Attributes:
        id: Slack channel ID
        name: Channel name (without #)
        topic: Channel topic/description
        purpose: Channel purpose (Slack field)
        member_count: Number of members
        last_message_ts: Timestamp of last message
        is_archived: Whether channel is archived
        members: List of usernames in channel (if full=true)
    """

    id: str
    name: str
    topic: Optional[str] = None
    purpose: Optional[str] = None
    member_count: Optional[int] = None
    last_message_ts: Optional[str] = None
    is_archived: bool = False
    members: Optional[list[str]] = None

    class Config:
        extra = "allow"


class Meeting(BaseModel):
    """Meeting record with optional transcript.

    Attributes:
        id: Unique meeting identifier
        title: Meeting title
        date: Meeting date/time
        duration_minutes: Duration in minutes
        summary: AI-generated meeting summary
        transcript: Full transcript (if full=true in request)
        attendees: List of attendee names
        recording_url: Link to recording if available
    """

    id: str
    title: str
    date: datetime
    duration_minutes: Optional[int] = None
    summary: Optional[str] = None
    transcript: Optional[str] = None
    attendees: list[str] = Field(default_factory=list)
    recording_url: Optional[HttpUrl] = None

    class Config:
        extra = "allow"


class Document(BaseModel):
    """Project document or asset.

    Attributes:
        id: Document identifier
        title: Document title
        type: Document type (spec, proposal, contract, etc.)
        content: Document content (if applicable)
        url: URL to document if external
        created_at: Creation timestamp
        updated_at: Last update timestamp
        owner: Creator/owner username
    """

    id: str
    title: str
    type: Optional[str] = None
    content: Optional[str] = None
    url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    owner: Optional[str] = None

    class Config:
        extra = "allow"


class ProjectStatus(BaseModel):
    """Detailed project status with metrics and health.

    Attributes:
        id: Project ID
        phase: Current lifecycle phase
        health: Health indicator (green/yellow/red)
        completion_percentage: Overall completion %
        blockers: List of current blockers
        next_milestone: Next scheduled milestone
        finances: Financial metrics (if available)
        team_capacity: Team capacity info
    """

    id: str
    phase: Optional[str] = None
    health: Optional[str] = None
    completion_percentage: Optional[float] = None
    blockers: list[str] = Field(default_factory=list)
    next_milestone: Optional[str] = None
    finances: Optional[dict[str, Any]] = None
    team_capacity: Optional[dict[str, Any]] = None

    class Config:
        extra = "allow"


class ProjectContext(BaseModel):
    """Complete project context in one response.

    This is the "golden record" endpoint that returns project info, team,
    meetings, Slack, GitHub, blockers, and financials together.

    Attributes:
        id: Project ID
        title: Project title
        description: Project description
        status: Current project status
        phase: Lifecycle phase
        team: List of team members
        channels: Slack channels
        meetings: Recent meetings with summaries
        blockers: Current blockers
        github_repos: Linked GitHub repositories
        documents: Project documents
        financials: Financial metrics if available
    """

    id: str
    title: str
    description: Optional[str] = None
    status: Optional[str] = None
    phase: Optional[str] = None
    team: list[TeamMember] = Field(default_factory=list)
    channels: list[Channel] = Field(default_factory=list)
    meetings: list[Meeting] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    github_repos: list[dict[str, Any]] = Field(default_factory=list)
    documents: list[Document] = Field(default_factory=list)
    financials: Optional[dict[str, Any]] = None

    class Config:
        extra = "allow"


class Project(BaseModel):
    """Project summary with key metadata.

    Attributes:
        id: Unique project identifier
        title: Project title
        description: Project description
        status: Current status (active, completed, etc.)
        phase: Lifecycle phase
        owner: Project owner username
        team_size: Number of team members
        created_at: Creation date
        updated_at: Last update date
        url: Project URL in Benmore
    """

    id: str
    title: str
    description: Optional[str] = None
    status: Optional[str] = None
    phase: Optional[str] = None
    owner: Optional[str] = None
    team_size: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    url: Optional[str] = None

    class Config:
        extra = "allow"


class ProjectListResponse(BaseModel):
    """Paginated list of projects.

    Attributes:
        results: List of projects
        count: Total count
        next: URL to next page if available
        previous: URL to previous page if available
    """

    results: list[Project] = Field(default_factory=list)
    count: int = 0
    next: Optional[str] = None
    previous: Optional[str] = None


class GitHubBoard(BaseModel):
    """GitHub Project board with items and status.

    Attributes:
        id: GitHub Project ID
        title: Project title
        items: List of board items
        status_counts: Count of items by status
        iterations: Sprint/iteration info if any
    """

    id: str
    title: Optional[str] = None
    items: list[dict[str, Any]] = Field(default_factory=list)
    status_counts: Optional[dict[str, int]] = None
    iterations: list[dict[str, Any]] = Field(default_factory=list)

    class Config:
        extra = "allow"
