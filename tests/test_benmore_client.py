"""Comprehensive pytest test suite for the benmore_client package.

Tests cover:
- All enum classes (members, values, str behavior, iteration, invalid access)
- All Pydantic models (valid data, optional/required fields, extra="allow",
  serialization, validation errors, defaults, nested models, pagination)
- BenmoreClient async HTTP client (all 30+ public methods, auth headers,
  base URL, context manager, error handling, response format handling)

Run:
    pytest tests/test_benmore_client.py -v
"""

from __future__ import annotations

import httpx
import pytest
import pydantic
import respx

from benmore_client.client import BenmoreClient
from benmore_client.enums import (
    DocumentType,
    IterationStatus,
    Phase,
    Priority,
    Severity,
    Size,
    Status,
)
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


# ============================================================================
# 1. ENUM TESTS
# ============================================================================


class TestPhaseEnum:
    """Tests for the Phase str-enum."""

    def test_members_and_values(self):
        expected = {
            "DISCOVERY": "discovery",
            "PLANNING": "planning",
            "DEVELOPMENT": "development",
            "TESTING": "testing",
            "LAUNCH": "launch",
            "MAINTENANCE": "maintenance",
            "COMPLETED": "completed",
            "ON_HOLD": "on_hold",
        }
        for name, value in expected.items():
            member = Phase[name]
            assert member.value == value
            assert member.name == name

    def test_member_count(self):
        assert len(Phase) == 8

    def test_str_comparison(self):
        assert Phase.DISCOVERY == "discovery"
        assert Phase.PLANNING == "planning"

    def test_iteration(self):
        values = [p.value for p in Phase]
        assert "discovery" in values
        assert "completed" in values

    def test_invalid_member_raises(self):
        with pytest.raises(KeyError):
            Phase["NONEXISTENT"]


class TestStatusEnum:
    def test_members_and_values(self):
        expected = {
            "ACTIVE": "active",
            "INACTIVE": "inactive",
            "PAUSED": "paused",
            "COMPLETED": "completed",
            "BLOCKED": "blocked",
        }
        for name, value in expected.items():
            assert Status[name].value == value

    def test_member_count(self):
        assert len(Status) == 5

    def test_str_comparison(self):
        assert Status.ACTIVE == "active"
        assert Status.BLOCKED == "blocked"

    def test_iteration(self):
        names = [s.name for s in Status]
        assert "ACTIVE" in names
        assert "BLOCKED" in names

    def test_invalid_member_raises(self):
        with pytest.raises(KeyError):
            Status["UNKNOWN"]


class TestPriorityEnum:
    def test_members_and_values(self):
        expected = {
            "CRITICAL": "critical",
            "HIGH": "high",
            "MEDIUM": "medium",
            "LOW": "low",
        }
        for name, value in expected.items():
            assert Priority[name].value == value

    def test_member_count(self):
        assert len(Priority) == 4

    def test_str_comparison(self):
        assert Priority.CRITICAL == "critical"

    def test_invalid_member_raises(self):
        with pytest.raises(KeyError):
            Priority["URGENT"]


class TestSizeEnum:
    def test_members_and_values(self):
        expected = {
            "XS": "xs",
            "S": "small",
            "M": "medium",
            "L": "large",
            "XL": "xl",
            "XXL": "xxl",
        }
        for name, value in expected.items():
            assert Size[name].value == value

    def test_member_count(self):
        assert len(Size) == 6

    def test_str_comparison(self):
        assert Size.S == "small"
        assert Size.M == "medium"

    def test_iteration(self):
        values = [s.value for s in Size]
        assert values == ["xs", "small", "medium", "large", "xl", "xxl"]

    def test_invalid_member_raises(self):
        with pytest.raises(KeyError):
            Size["XXXL"]


class TestSeverityEnum:
    def test_members_and_values(self):
        expected = {
            "CRITICAL": "critical",
            "HIGH": "high",
            "MEDIUM": "medium",
            "LOW": "low",
            "INFO": "info",
        }
        for name, value in expected.items():
            assert Severity[name].value == value

    def test_member_count(self):
        assert len(Severity) == 5

    def test_str_comparison(self):
        assert Severity.INFO == "info"

    def test_invalid_member_raises(self):
        with pytest.raises(KeyError):
            Severity["WARNING"]


class TestDocumentTypeEnum:
    def test_members_and_values(self):
        expected = {
            "SPECIFICATION": "specification",
            "PROPOSAL": "proposal",
            "CONTRACT": "contract",
            "MEETING_NOTES": "meeting_notes",
            "DECISION_LOG": "decision_log",
            "ARCHITECTURE": "architecture",
            "ROADMAP": "roadmap",
            "OTHER": "other",
        }
        for name, value in expected.items():
            assert DocumentType[name].value == value

    def test_member_count(self):
        assert len(DocumentType) == 8

    def test_str_comparison(self):
        assert DocumentType.SPECIFICATION == "specification"

    def test_invalid_member_raises(self):
        with pytest.raises(KeyError):
            DocumentType["REPORT"]


class TestIterationStatusEnum:
    def test_members_and_values(self):
        expected = {
            "NOT_STARTED": "not_started",
            "IN_PROGRESS": "in_progress",
            "COMPLETED": "completed",
        }
        for name, value in expected.items():
            assert IterationStatus[name].value == value

    def test_member_count(self):
        assert len(IterationStatus) == 3

    def test_str_comparison(self):
        assert IterationStatus.IN_PROGRESS == "in_progress"

    def test_invalid_member_raises(self):
        with pytest.raises(KeyError):
            IterationStatus["CANCELLED"]


# ============================================================================
# 2. MODEL TESTS
# ============================================================================


class TestTeamMemberModel:
    """Tests for TeamMember Pydantic model."""

    def test_valid_creation(self):
        member = TeamMember(
            id="u1", username="jdoe", name="Jane Doe", email="j@example.com"
        )
        assert member.id == "u1"
        assert member.username == "jdoe"
        assert member.name == "Jane Doe"
        assert member.email == "j@example.com"

    def test_optional_fields_default_to_none(self):
        member = TeamMember(
            id="u1", username="jdoe", name="Jane Doe", email="j@example.com"
        )
        assert member.role is None
        assert member.joined_at is None

    def test_optional_fields_set(self):
        member = TeamMember(
            id="u1",
            username="jdoe",
            name="Jane Doe",
            email="j@example.com",
            role="lead",
            joined_at="2024-01-15T10:00:00",
        )
        assert member.role == "lead"
        assert member.joined_at is not None

    def test_extra_fields_allowed(self):
        member = TeamMember(
            id="u1",
            username="jdoe",
            name="Jane Doe",
            email="j@example.com",
            custom_field="custom_value",
        )
        assert member.custom_field == "custom_value"  # type: ignore[attr-defined]

    def test_model_dump(self):
        member = TeamMember(
            id="u1", username="jdoe", name="Jane Doe", email="j@example.com"
        )
        data = member.model_dump()
        assert data["id"] == "u1"
        assert data["username"] == "jdoe"
        assert "role" in data
        assert data["role"] is None

    def test_all_fields_optional(self):
        # After refactor, all TeamMember fields are Optional with None defaults.
        # The API often omits id/email, so constructing with only username must work.
        member = TeamMember(username="jdoe")
        assert member.username == "jdoe"
        assert member.id == "jdoe"  # id falls back to username via validator
        assert member.name is None
        assert member.email is None

    def test_title_maps_to_role(self):
        # API returns `title` (e.g. "Senior Fullstack Developer"); validator maps to `role`.
        member = TeamMember(
            username="jdoe", name="Jane", title="Senior Fullstack Developer"
        )
        assert member.role == "Senior Fullstack Developer"

    def test_wrong_type_raises(self):
        with pytest.raises(pydantic.ValidationError):
            TeamMember(
                id="u1",
                username="jdoe",
                name="Jane",
                email="j@x.com",
                joined_at="not-a-date",
            )


class TestChannelModel:
    def test_valid_creation(self):
        ch = Channel(id="C123", name="general")
        assert ch.id == "C123"
        assert ch.name == "general"

    def test_optional_fields_default(self):
        ch = Channel(id="C123", name="general")
        assert ch.topic is None
        assert ch.purpose is None
        assert ch.member_count is None
        assert ch.last_message_ts is None
        assert ch.is_archived is False
        assert ch.members is None

    def test_full_creation(self):
        ch = Channel(
            id="C123",
            name="dev",
            topic="Dev chat",
            purpose="Development discussions",
            member_count=5,
            last_message_ts="1234567890.123456",
            is_archived=True,
            members=["alice", "bob"],
        )
        assert ch.member_count == 5
        assert ch.is_archived is True
        assert len(ch.members) == 2

    def test_extra_fields_allowed(self):
        ch = Channel(id="C123", name="general", extra_attr="hello")
        assert ch.extra_attr == "hello"  # type: ignore[attr-defined]

    def test_model_dump(self):
        ch = Channel(id="C123", name="general")
        data = ch.model_dump()
        assert data["id"] == "C123"
        assert data["is_archived"] is False

    def test_all_fields_optional(self):
        # After refactor, Channel fields are all optional with defensive defaults.
        # API returns channel_id/channel_name; validator maps them to id/name.
        ch = Channel(channel_id="C123")
        assert ch.id == "C123"
        assert ch.name == "C123"  # falls back to channel_id when name missing

    def test_channel_field_alias_mapping(self):
        # Test that API field aliases are mapped correctly by the validator.
        ch = Channel(
            channel_id="C999",
            channel_name="dev",
            last_message_at="2024-01-01T00:00:00",
        )
        assert ch.id == "C999"
        assert ch.name == "dev"
        assert ch.last_message_ts == "2024-01-01T00:00:00"


class TestMeetingModel:
    def test_valid_creation(self):
        m = Meeting(id="m1", title="Standup", date="2024-03-01T09:00:00")
        assert m.id == "m1"
        assert m.title == "Standup"
        assert m.date is not None

    def test_optional_fields_default(self):
        m = Meeting(id="m1", title="Standup", date="2024-03-01T09:00:00")
        assert m.duration_minutes is None
        assert m.summary is None
        assert m.transcript is None
        assert m.attendees == []
        assert m.recording_url is None

    def test_full_creation(self):
        m = Meeting(
            id="m1",
            title="Standup",
            date="2024-03-01T09:00:00",
            duration_minutes=30,
            summary="Discussed blockers",
            transcript="Full text...",
            attendees=["Alice", "Bob"],
            recording_url="https://example.com/recording.mp4",
        )
        assert m.duration_minutes == 30
        assert len(m.attendees) == 2
        assert str(m.recording_url) == "https://example.com/recording.mp4"

    def test_extra_fields_allowed(self):
        # action_items is now a defined Optional[str] field on Meeting (refactor added it).
        # Use a genuinely-extra key to exercise extra="allow".
        m = Meeting(
            id="m1", title="Standup", date="2024-03-01T09:00:00", custom_tag="sync"
        )
        assert m.custom_tag == "sync"  # type: ignore[attr-defined]

    def test_model_dump(self):
        m = Meeting(id="m1", title="Standup", date="2024-03-01T09:00:00")
        data = m.model_dump()
        assert data["id"] == "m1"
        assert data["attendees"] == []

    def test_invalid_date_raises(self):
        with pytest.raises(pydantic.ValidationError):
            Meeting(id="m1", title="Standup", date="not-a-date")

    def test_recording_url_accepts_any_string(self):
        # After refactor, recording_url is Optional[str], not a pydantic URL type.
        # The Benmore API sometimes returns bare strings / relative paths, so we
        # intentionally no longer validate URL shape here.
        m = Meeting(
            id="m1",
            title="Standup",
            date="2024-03-01T09:00:00",
            recording_url="not-a-url",
        )
        assert m.recording_url == "not-a-url"


class TestDocumentModel:
    def test_valid_creation(self):
        doc = Document(id="d1", title="Spec Doc")
        assert doc.id == "d1"
        assert doc.title == "Spec Doc"

    def test_optional_fields_default(self):
        doc = Document(id="d1", title="Spec Doc")
        assert doc.type is None
        assert doc.content is None
        assert doc.url is None
        assert doc.created_at is None
        assert doc.updated_at is None
        assert doc.owner is None

    def test_full_creation(self):
        doc = Document(
            id="d1",
            title="Spec Doc",
            type="specification",
            content="# Spec",
            url="https://example.com/doc",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-02-01T00:00:00",
            owner="alice",
        )
        assert doc.type == "specification"
        assert doc.owner == "alice"

    def test_extra_fields_allowed(self):
        doc = Document(id="d1", title="Spec Doc", version=2)
        assert doc.version == 2  # type: ignore[attr-defined]

    def test_model_dump(self):
        doc = Document(id="d1", title="Spec Doc")
        data = doc.model_dump()
        assert data["title"] == "Spec Doc"
        assert data["type"] is None

    def test_all_fields_optional(self):
        # After refactor, Document fields are all optional with None defaults.
        doc = Document(id="d1")
        assert doc.id == "d1"
        assert doc.title is None


class TestProjectStatusModel:
    def test_valid_creation(self):
        ps = ProjectStatus(id="p1")
        assert ps.id == "p1"

    def test_optional_fields_default(self):
        ps = ProjectStatus(id="p1")
        assert ps.phase is None
        assert ps.health is None
        assert ps.completion_percentage is None
        # blockers is now typed Any (refactor) because /status/ returns a dict
        # {"unresolved": [...], "total_unresolved": N} while /context/ returns a list.
        # It defaults to None rather than [].
        assert ps.blockers is None
        assert ps.next_milestone is None
        assert ps.finances is None

    def test_full_creation(self):
        ps = ProjectStatus(
            id="p1",
            phase="development",
            health="green",
            completion_percentage=75.5,
            blockers=["API delay"],
            next_milestone="v2.0 release",
            finances={"budget": 100000, "spent": 50000},
            team_capacity={"available": 3, "total": 5},
        )
        assert ps.completion_percentage == 75.5
        assert len(ps.blockers) == 1
        assert ps.finances["budget"] == 100000

    def test_extra_fields_allowed(self):
        ps = ProjectStatus(id="p1", custom="extra")
        assert ps.custom == "extra"  # type: ignore[attr-defined]

    def test_model_dump(self):
        ps = ProjectStatus(id="p1", phase="development")
        data = ps.model_dump()
        assert data["phase"] == "development"
        # blockers is Any-typed and defaults to None (see test_optional_fields_default).
        assert data["blockers"] is None


class TestProjectContextModel:
    def test_valid_minimal(self):
        ctx = ProjectContext(id="p1", title="Project Alpha")
        assert ctx.id == "p1"
        assert ctx.title == "Project Alpha"

    def test_optional_fields_default(self):
        ctx = ProjectContext(id="p1", title="Alpha")
        assert ctx.description is None
        assert ctx.status is None
        assert ctx.phase is None
        assert ctx.team == []
        assert ctx.channels == []
        assert ctx.meetings == []
        assert ctx.blockers == []
        assert ctx.github_repos == []
        assert ctx.documents == []
        assert ctx.financials is None

    def test_nested_team_members(self):
        ctx = ProjectContext(
            id="p1",
            title="Alpha",
            team=[
                {"id": "u1", "username": "alice", "name": "Alice", "email": "a@x.com"},
                {"id": "u2", "username": "bob", "name": "Bob", "email": "b@x.com"},
            ],
        )
        assert len(ctx.team) == 2
        assert isinstance(ctx.team[0], TeamMember)
        assert ctx.team[0].username == "alice"

    def test_nested_channels(self):
        ctx = ProjectContext(
            id="p1",
            title="Alpha",
            channels=[{"id": "C1", "name": "general"}],
        )
        assert len(ctx.channels) == 1
        assert isinstance(ctx.channels[0], Channel)

    def test_nested_meetings(self):
        ctx = ProjectContext(
            id="p1",
            title="Alpha",
            meetings=[{"id": "m1", "title": "Standup", "date": "2024-03-01T09:00:00"}],
        )
        assert len(ctx.meetings) == 1
        assert isinstance(ctx.meetings[0], Meeting)

    def test_nested_documents(self):
        ctx = ProjectContext(
            id="p1",
            title="Alpha",
            documents=[{"id": "d1", "title": "Spec"}],
        )
        assert len(ctx.documents) == 1
        assert isinstance(ctx.documents[0], Document)

    def test_extra_fields_allowed(self):
        ctx = ProjectContext(id="p1", title="Alpha", custom_ctx="value")
        assert ctx.custom_ctx == "value"  # type: ignore[attr-defined]

    def test_model_dump(self):
        ctx = ProjectContext(id="p1", title="Alpha")
        data = ctx.model_dump()
        assert data["id"] == "p1"
        assert data["team"] == []

    def test_all_fields_optional(self):
        # After refactor, ProjectContext fields are all optional. The API sometimes
        # returns a bare {id, ...} without title, so we no longer treat title as required.
        ctx = ProjectContext(id="p1")
        assert ctx.id == "p1"
        assert ctx.title is None
        assert ctx.team == []
        assert ctx.meetings == []


class TestProjectModel:
    def test_valid_creation(self):
        p = Project(id="p1", title="My Project")
        assert p.id == "p1"
        assert p.title == "My Project"

    def test_optional_fields_default(self):
        p = Project(id="p1", title="My Project")
        assert p.description is None
        assert p.status is None
        assert p.phase is None
        assert p.owner is None
        assert p.team_size is None
        assert p.created_at is None
        assert p.updated_at is None
        assert p.url is None

    def test_full_creation(self):
        p = Project(
            id="p1",
            title="My Project",
            description="A project",
            status="active",
            phase="development",
            owner="alice",
            team_size=5,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-02-01T00:00:00",
            url="https://benmore.tech/p/p1",
        )
        assert p.status == "active"
        assert p.team_size == 5

    def test_extra_fields_allowed(self):
        p = Project(id="p1", title="My Project", tags=["web"])
        assert p.tags == ["web"]  # type: ignore[attr-defined]

    def test_model_dump(self):
        p = Project(id="p1", title="My Project")
        data = p.model_dump()
        assert data["title"] == "My Project"

    def test_all_fields_optional(self):
        # After refactor, Project fields are all optional. /projects/ occasionally
        # returns entries with id but no title, so title is no longer required.
        p = Project(id="p1")
        assert p.id == "p1"
        assert p.title is None

    def test_team_size_derived_from_members(self):
        # Validator derives team_size from team_members length when not provided.
        p = Project(
            id="p1",
            title="My Project",
            team_members=[
                {"username": "alice", "name": "Alice"},
                {"username": "bob", "name": "Bob"},
                {"username": "carol", "name": "Carol"},
            ],
        )
        assert p.team_size == 3


class TestProjectListResponseModel:
    def test_valid_creation(self):
        plr = ProjectListResponse(
            results=[{"id": "p1", "title": "A"}],
            count=1,
            next=None,
            previous=None,
        )
        assert len(plr.results) == 1
        assert isinstance(plr.results[0], Project)
        assert plr.count == 1

    def test_defaults(self):
        plr = ProjectListResponse()
        assert plr.results == []
        assert plr.count == 0
        assert plr.next is None
        assert plr.previous is None

    def test_pagination_fields(self):
        plr = ProjectListResponse(
            results=[],
            count=100,
            next="https://api.example.com/projects/?page=2",
            previous="https://api.example.com/projects/?page=0",
        )
        assert plr.next == "https://api.example.com/projects/?page=2"
        assert plr.previous == "https://api.example.com/projects/?page=0"
        assert plr.count == 100

    def test_model_dump(self):
        plr = ProjectListResponse(results=[{"id": "p1", "title": "A"}], count=1)
        data = plr.model_dump()
        assert data["count"] == 1
        assert len(data["results"]) == 1


class TestGitHubBoardModel:
    def test_valid_creation(self):
        board = GitHubBoard(id="gh1")
        assert board.id == "gh1"

    def test_optional_fields_default(self):
        board = GitHubBoard(id="gh1")
        assert board.title is None
        assert board.items == []
        assert board.status_counts is None
        assert board.iterations == []

    def test_full_creation(self):
        board = GitHubBoard(
            id="gh1",
            title="Sprint Board",
            items=[{"id": "i1", "title": "Task 1", "status": "Todo"}],
            status_counts={"Todo": 3, "In Progress": 2, "Done": 5},
            iterations=[{"name": "Sprint 1", "status": "in_progress"}],
        )
        assert board.title == "Sprint Board"
        assert len(board.items) == 1
        assert board.status_counts["Done"] == 5

    def test_extra_fields_allowed(self):
        board = GitHubBoard(id="gh1", org="benmore-studio")
        assert board.org == "benmore-studio"  # type: ignore[attr-defined]

    def test_model_dump(self):
        board = GitHubBoard(id="gh1", title="Board")
        data = board.model_dump()
        assert data["title"] == "Board"
        assert data["items"] == []


# ============================================================================
# 3. CLIENT TESTS
# ============================================================================

BASE_URL = "https://client.benmore.tech/api/v1"
API_KEY = "bpk_test_key_12345"
PROJECT_ID = "proj-abc-123"


@pytest.fixture
def client():
    """Create a BenmoreClient instance for testing.

    ``max_retries=0`` disables the retry-on-transient-failure loop so that
    mocked 5xx / network-error tests don't spend real seconds in exponential
    backoff and so respx call counts stay at 1 per request.
    """
    return BenmoreClient(api_key=API_KEY, max_retries=0)


@pytest.fixture
def custom_client():
    """Create a BenmoreClient with custom settings."""
    return BenmoreClient(
        api_key=API_KEY,
        base_url="https://custom.api.com/v2",
        timeout=60.0,
        verify_ssl=False,
        max_retries=0,
    )


class TestClientInit:
    """Tests for BenmoreClient initialization."""

    def test_default_initialization(self, client: BenmoreClient):
        assert client.api_key == API_KEY
        assert client.base_url == BASE_URL
        assert client.timeout == 30.0
        assert client.verify_ssl is True
        assert client._client is None

    def test_custom_initialization(self, custom_client: BenmoreClient):
        assert custom_client.api_key == API_KEY
        assert custom_client.base_url == "https://custom.api.com/v2"
        assert custom_client.timeout == 60.0
        assert custom_client.verify_ssl is False

    def test_base_url_trailing_slash_stripped(self):
        c = BenmoreClient(api_key=API_KEY, base_url="https://example.com/api/")
        assert c.base_url == "https://example.com/api"


class TestClientHeaders:
    """Tests for auth header construction."""

    def test_headers_contain_api_key(self, client: BenmoreClient):
        headers = client._headers()
        assert headers["X-API-KEY"] == API_KEY
        assert headers["Content-Type"] == "application/json"


class TestClientContextManager:
    """Tests for async context manager."""

    @pytest.mark.asyncio
    async def test_aenter_creates_client(self, client: BenmoreClient):
        async with client as c:
            assert c._client is not None
            assert isinstance(c._client, httpx.AsyncClient)
            assert c is client

    @pytest.mark.asyncio
    async def test_aexit_closes_client(self, client: BenmoreClient):
        async with client:
            assert client._client is not None
        # After exiting, _client is still set but httpx client is closed
        # (no assertion needed — just verify no exception)

    @pytest.mark.asyncio
    async def test_request_without_context_manager_raises(self, client: BenmoreClient):
        with pytest.raises(RuntimeError, match="Client not initialized"):
            await client._request("GET", "/projects/")


class TestClientRequest:
    """Tests for the internal _request method."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_request_sends_correct_headers(self, client: BenmoreClient):
        route = respx.get(f"{BASE_URL}/projects/").mock(
            return_value=httpx.Response(200, json=[])
        )
        async with client:
            await client._request("GET", "/projects/")
        assert route.called
        request = route.calls[0].request
        assert request.headers["X-API-KEY"] == API_KEY
        assert request.headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    @respx.mock
    async def test_request_constructs_correct_url(self, client: BenmoreClient):
        route = respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/team/").mock(
            return_value=httpx.Response(200, json={"team_members": []})
        )
        async with client:
            await client._request("GET", f"/projects/{PROJECT_ID}/team/")
        assert route.called

    @pytest.mark.asyncio
    @respx.mock
    async def test_request_passes_query_params(self, client: BenmoreClient):
        route = respx.get(f"{BASE_URL}/projects/search/").mock(
            return_value=httpx.Response(200, json=[])
        )
        async with client:
            await client._request("GET", "/projects/search/", params={"q": "test"})
        request = route.calls[0].request
        assert "q=test" in str(request.url)

    @pytest.mark.asyncio
    @respx.mock
    async def test_request_passes_json_body(self, client: BenmoreClient):
        route = respx.post(f"{BASE_URL}/projects/{PROJECT_ID}/team/").mock(
            return_value=httpx.Response(200, json={"status": "ok"})
        )
        async with client:
            await client._request(
                "POST",
                f"/projects/{PROJECT_ID}/team/",
                json={"usernames": ["alice"]},
            )
        request = route.calls[0].request
        import json

        body = json.loads(request.content)
        assert body["usernames"] == ["alice"]

    @pytest.mark.asyncio
    @respx.mock
    async def test_request_raises_on_http_error(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/").mock(
            return_value=httpx.Response(500, json={"error": "Server Error"})
        )
        async with client:
            with pytest.raises(httpx.HTTPStatusError):
                await client._request("GET", "/projects/")

    @pytest.mark.asyncio
    @respx.mock
    async def test_request_raises_on_404(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/comms/").mock(
            return_value=httpx.Response(
                404, json={"error": "No Slack channel connected to this project."}
            )
        )
        async with client:
            with pytest.raises(httpx.HTTPStatusError):
                await client._request("GET", f"/projects/{PROJECT_ID}/comms/")


# ─── Projects endpoint tests ──────────────────────────────────────────


class TestProjectsList:
    @pytest.mark.asyncio
    @respx.mock
    async def test_projects_list_handles_list_response(self, client: BenmoreClient):
        """Test that list response (not dict) is handled correctly."""
        respx.get(f"{BASE_URL}/projects/").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": "uuid1",
                        "title": "Project A [BEN-001]",
                        "status": None,
                        "phase": "implementation",
                    },
                    {
                        "id": "uuid2",
                        "title": "Project B [BEN-002]",
                        "status": "active",
                        "phase": "discovery",
                    },
                ],
            )
        )
        async with client:
            result = await client.projects_list()
        assert isinstance(result, ProjectListResponse)
        assert len(result.results) == 2
        assert result.results[0].id == "uuid1"
        assert result.results[0].title == "Project A [BEN-001]"
        assert result.results[1].phase == "discovery"

    @pytest.mark.asyncio
    @respx.mock
    async def test_projects_list_handles_dict_response(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [{"id": "p1", "title": "Proj"}],
                    "count": 1,
                    "next": None,
                    "previous": None,
                },
            )
        )
        async with client:
            result = await client.projects_list()
        assert isinstance(result, ProjectListResponse)
        assert result.count == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_projects_list_empty(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/").mock(
            return_value=httpx.Response(200, json=[])
        )
        async with client:
            result = await client.projects_list()
        assert result.results == []


class TestProjectsSearch:
    @pytest.mark.asyncio
    @respx.mock
    async def test_projects_search_list_response(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/search/").mock(
            return_value=httpx.Response(
                200,
                json=[{"id": "p1", "title": "Matching Project"}],
            )
        )
        async with client:
            result = await client.projects_search(q="Matching")
        assert isinstance(result, ProjectListResponse)
        assert len(result.results) == 1
        assert result.results[0].title == "Matching Project"

    @pytest.mark.asyncio
    @respx.mock
    async def test_projects_search_dict_response(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/search/").mock(
            return_value=httpx.Response(
                200,
                json={"results": [{"id": "p1", "title": "Found"}], "count": 1},
            )
        )
        async with client:
            result = await client.projects_search(q="Found")
        assert result.count == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_projects_search_passes_query_param(self, client: BenmoreClient):
        route = respx.get(f"{BASE_URL}/projects/search/").mock(
            return_value=httpx.Response(200, json=[])
        )
        async with client:
            await client.projects_search(q="my query")
        assert "q=my+query" in str(route.calls[0].request.url) or "q=my%20query" in str(
            route.calls[0].request.url
        )


class TestProjectsSummary:
    @pytest.mark.asyncio
    @respx.mock
    async def test_projects_summary(self, client: BenmoreClient):
        summary_data = {
            "active_count": 5,
            "total_count": 12,
            "health": {"green": 3, "yellow": 1, "red": 1},
        }
        respx.get(f"{BASE_URL}/projects/summary/").mock(
            return_value=httpx.Response(200, json=summary_data)
        )
        async with client:
            result = await client.projects_summary()
        assert result["active_count"] == 5
        assert result["health"]["green"] == 3


class TestProjectsContext:
    @pytest.mark.asyncio
    @respx.mock
    async def test_projects_context_minimal(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/context/").mock(
            return_value=httpx.Response(
                200,
                json={"id": PROJECT_ID, "title": "Alpha Project"},
            )
        )
        async with client:
            ctx = await client.projects_context(PROJECT_ID)
        assert isinstance(ctx, ProjectContext)
        assert ctx.id == PROJECT_ID
        assert ctx.title == "Alpha Project"

    @pytest.mark.asyncio
    @respx.mock
    async def test_projects_context_with_params(self, client: BenmoreClient):
        route = respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/context/").mock(
            return_value=httpx.Response(
                200,
                json={"id": PROJECT_ID, "title": "Alpha"},
            )
        )
        async with client:
            await client.projects_context(PROJECT_ID, full=True, days=30)
        url_str = str(route.calls[0].request.url)
        assert "full=true" in url_str
        assert "days=30" in url_str

    @pytest.mark.asyncio
    @respx.mock
    async def test_projects_context_with_nested_data(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/context/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": PROJECT_ID,
                    "title": "Alpha",
                    "team": [
                        {
                            "id": "u1",
                            "username": "alice",
                            "name": "Alice",
                            "email": "a@x.com",
                        }
                    ],
                    "channels": [{"id": "C1", "name": "alpha-dev"}],
                    "meetings": [
                        {"id": "m1", "title": "Standup", "date": "2024-03-01T09:00:00"}
                    ],
                    "documents": [{"id": "d1", "title": "Spec"}],
                    "blockers": ["Waiting for API keys"],
                    "github_repos": [
                        {"name": "repo", "url": "https://github.com/org/repo"}
                    ],
                },
            )
        )
        async with client:
            ctx = await client.projects_context(PROJECT_ID)
        assert len(ctx.team) == 1
        assert isinstance(ctx.team[0], TeamMember)
        assert len(ctx.channels) == 1
        assert isinstance(ctx.channels[0], Channel)
        assert len(ctx.meetings) == 1
        assert len(ctx.documents) == 1
        assert ctx.blockers == ["Waiting for API keys"]


class TestProjectsStatus:
    @pytest.mark.asyncio
    @respx.mock
    async def test_projects_status(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/status/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": PROJECT_ID,
                    "phase": "development",
                    "health": "green",
                    "completion_percentage": 65.0,
                    "blockers": [],
                },
            )
        )
        async with client:
            status = await client.projects_status(PROJECT_ID)
        assert isinstance(status, ProjectStatus)
        assert status.health == "green"
        assert status.completion_percentage == 65.0


class TestProjectsAssets:
    @pytest.mark.asyncio
    @respx.mock
    async def test_projects_assets(self, client: BenmoreClient):
        assets_data = {"documents": [], "diagrams": [], "signatures": []}
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/assets/").mock(
            return_value=httpx.Response(200, json=assets_data)
        )
        async with client:
            result = await client.projects_assets(PROJECT_ID)
        assert "documents" in result


class TestProjectsUpdate:
    @pytest.mark.asyncio
    @respx.mock
    async def test_projects_update(self, client: BenmoreClient):
        respx.patch(f"{BASE_URL}/projects/{PROJECT_ID}/update/").mock(
            return_value=httpx.Response(
                200,
                json={"id": PROJECT_ID, "title": "Updated", "phase": "testing"},
            )
        )
        async with client:
            result = await client.projects_update(PROJECT_ID, phase="testing")
        assert isinstance(result, Project)
        assert result.phase == "testing"

    @pytest.mark.asyncio
    @respx.mock
    async def test_projects_update_all_fields(self, client: BenmoreClient):
        route = respx.patch(f"{BASE_URL}/projects/{PROJECT_ID}/update/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": PROJECT_ID,
                    "title": "Updated",
                    "phase": "testing",
                    "description": "New desc",
                },
            )
        )
        async with client:
            await client.projects_update(
                PROJECT_ID,
                phase="testing",
                working_on="Bug fixes",
                description="New desc",
            )
        import json

        body = json.loads(route.calls[0].request.content)
        assert body["phase"] == "testing"
        assert body["working_on"] == "Bug fixes"
        assert body["description"] == "New desc"

    @pytest.mark.asyncio
    @respx.mock
    async def test_projects_update_no_fields_sends_empty_body(
        self, client: BenmoreClient
    ):
        route = respx.patch(f"{BASE_URL}/projects/{PROJECT_ID}/update/").mock(
            return_value=httpx.Response(
                200,
                json={"id": PROJECT_ID, "title": "Same"},
            )
        )
        async with client:
            await client.projects_update(PROJECT_ID)
        import json

        body = json.loads(route.calls[0].request.content)
        assert body == {}


# ─── Team endpoint tests ──────────────────────────────────────────────


class TestTeamList:
    @pytest.mark.asyncio
    @respx.mock
    async def test_team_list_api_format(self, client: BenmoreClient):
        """Test the actual API response format with team_members key."""
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/team/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "project_id": PROJECT_ID,
                    "project_title": "Project Title",
                    "team_members": [
                        {
                            "username": "alice",
                            "name": "Alice Smith",
                            "title": "Lead Developer",
                        },
                        {"username": "bob", "name": "Bob Jones", "title": "Designer"},
                    ],
                },
            )
        )
        async with client:
            members = await client.team_list(PROJECT_ID)
        assert len(members) == 2
        assert isinstance(members[0], TeamMember)
        assert members[0].username == "alice"
        assert members[0].name == "Alice Smith"
        assert members[0].role == "Lead Developer"  # title maps to role
        assert members[1].username == "bob"

    @pytest.mark.asyncio
    @respx.mock
    async def test_team_list_with_results_key(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/team/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"username": "charlie", "name": "Charlie", "email": "c@x.com"}
                    ]
                },
            )
        )
        async with client:
            members = await client.team_list(PROJECT_ID)
        assert len(members) == 1
        assert members[0].username == "charlie"

    @pytest.mark.asyncio
    @respx.mock
    async def test_team_list_with_string_members(self, client: BenmoreClient):
        """Test fallback for string-only member list."""
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/team/").mock(
            return_value=httpx.Response(
                200,
                json={"team_members": ["alice", "bob"]},
            )
        )
        async with client:
            members = await client.team_list(PROJECT_ID)
        assert len(members) == 2
        assert members[0].username == "alice"
        assert members[0].id == "alice"

    @pytest.mark.asyncio
    @respx.mock
    async def test_team_list_empty(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/team/").mock(
            return_value=httpx.Response(200, json={"team_members": []})
        )
        async with client:
            members = await client.team_list(PROJECT_ID)
        assert members == []


class TestTeamAdd:
    @pytest.mark.asyncio
    @respx.mock
    async def test_team_add_with_usernames(self, client: BenmoreClient):
        route = respx.post(f"{BASE_URL}/projects/{PROJECT_ID}/team/").mock(
            return_value=httpx.Response(200, json={"status": "ok", "added": ["alice"]})
        )
        async with client:
            result = await client.team_add(PROJECT_ID, usernames=["alice"])
        assert result["status"] == "ok"
        import json

        body = json.loads(route.calls[0].request.content)
        assert body["usernames"] == ["alice"]

    @pytest.mark.asyncio
    @respx.mock
    async def test_team_add_self(self, client: BenmoreClient):
        route = respx.post(f"{BASE_URL}/projects/{PROJECT_ID}/team/").mock(
            return_value=httpx.Response(200, json={"status": "ok"})
        )
        async with client:
            await client.team_add(PROJECT_ID)
        import json

        body = json.loads(route.calls[0].request.content)
        assert body == {}


class TestTeamRemove:
    @pytest.mark.asyncio
    @respx.mock
    async def test_team_remove(self, client: BenmoreClient):
        route = respx.delete(f"{BASE_URL}/projects/{PROJECT_ID}/team/").mock(
            return_value=httpx.Response(200, json={"status": "ok", "removed": ["bob"]})
        )
        async with client:
            result = await client.team_remove(PROJECT_ID, usernames=["bob"])
        assert result["status"] == "ok"
        import json

        body = json.loads(route.calls[0].request.content)
        assert body["usernames"] == ["bob"]


# ─── Comms endpoint tests ─────────────────────────────────────────────


class TestCommsChannelInfo:
    @pytest.mark.asyncio
    @respx.mock
    async def test_comms_channel_info_connected(self, client: BenmoreClient):
        """Test actual connected API response format."""
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/comms/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "channel_id": "C0AQRCF0BSS",
                    "total_messages": 11,
                    "last_message_at": "2026-04-06T14:59:05+00:00",
                    "recent_messages": [
                        {"text": "Hello", "user": "U123", "ts": "1234567890.123456"}
                    ],
                    "source": "database",
                },
            )
        )
        async with client:
            channel = await client.comms_channel_info(PROJECT_ID)
        assert isinstance(channel, Channel)
        assert channel.id == "C0AQRCF0BSS"
        assert (
            channel.total_messages == 11
        )  # Fixed: total_messages now has its own field
        assert (
            channel.member_count is None
        )  # member_count is separate from total_messages
        assert channel.last_message_ts == "2026-04-06T14:59:05+00:00"

    @pytest.mark.asyncio
    @respx.mock
    async def test_comms_channel_info_not_connected_raises(self, client: BenmoreClient):
        """Test 404 for unconnected project."""
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/comms/").mock(
            return_value=httpx.Response(
                404,
                json={"error": "No Slack channel connected to this project."},
            )
        )
        async with client:
            with pytest.raises(httpx.HTTPStatusError):
                await client.comms_channel_info(PROJECT_ID)


class TestCommsRaw:
    @pytest.mark.asyncio
    @respx.mock
    async def test_comms_raw(self, client: BenmoreClient):
        raw_data = {
            "channel_id": "C0AQRCF0BSS",
            "total_messages": 11,
            "last_message_at": "2026-04-06T14:59:05+00:00",
            "recent_messages": [{"text": "Hello", "user": "U123"}],
            "source": "database",
        }
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/comms/").mock(
            return_value=httpx.Response(200, json=raw_data)
        )
        async with client:
            result = await client.comms_raw(PROJECT_ID)
        assert result["channel_id"] == "C0AQRCF0BSS"
        assert result["total_messages"] == 11
        assert len(result["recent_messages"]) == 1


class TestCommsChannelConnect:
    @pytest.mark.asyncio
    @respx.mock
    async def test_comms_channel_connect(self, client: BenmoreClient):
        respx.patch(f"{BASE_URL}/projects/{PROJECT_ID}/comms/").mock(
            return_value=httpx.Response(
                200,
                json={"id": "C123NEW", "name": "new-channel"},
            )
        )
        async with client:
            channel = await client.comms_channel_connect(
                PROJECT_ID, channel_id="C123NEW"
            )
        assert isinstance(channel, Channel)
        assert channel.id == "C123NEW"


class TestCommsMessages:
    @pytest.mark.asyncio
    @respx.mock
    async def test_comms_messages_with_results_key(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/comms/messages/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"text": "Hello", "user": "U1", "ts": "111.222"},
                        {"text": "World", "user": "U2", "ts": "111.333"},
                    ]
                },
            )
        )
        async with client:
            messages = await client.comms_messages(PROJECT_ID)
        assert len(messages) == 2
        assert messages[0]["text"] == "Hello"

    @pytest.mark.asyncio
    @respx.mock
    async def test_comms_messages_list_response_handled(self, client: BenmoreClient):
        """comms_messages now handles raw list responses correctly."""
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/comms/messages/").mock(
            return_value=httpx.Response(
                200,
                json=[{"text": "Msg1"}],
            )
        )
        async with client:
            result = await client.comms_messages(PROJECT_ID)
        assert isinstance(result, list)
        assert result[0]["text"] == "Msg1"

    @pytest.mark.asyncio
    @respx.mock
    async def test_comms_messages_with_pagination(self, client: BenmoreClient):
        route = respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/comms/messages/").mock(
            return_value=httpx.Response(200, json={"results": []})
        )
        async with client:
            await client.comms_messages(PROJECT_ID, limit=10, before="111.222")
        url_str = str(route.calls[0].request.url)
        assert "limit=10" in url_str
        assert "before=111.222" in url_str


class TestCommsMessagePost:
    @pytest.mark.asyncio
    @respx.mock
    async def test_comms_message_post(self, client: BenmoreClient):
        route = respx.post(f"{BASE_URL}/projects/{PROJECT_ID}/comms/messages/").mock(
            return_value=httpx.Response(
                200,
                json={"ok": True, "ts": "111.444"},
            )
        )
        async with client:
            result = await client.comms_message_post(PROJECT_ID, text="Hello team!")
        assert result["ok"] is True
        import json

        body = json.loads(route.calls[0].request.content)
        assert body["text"] == "Hello team!"


class TestCommsThreadRead:
    @pytest.mark.asyncio
    @respx.mock
    async def test_comms_thread_read_with_results(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/comms/thread/111.222/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"text": "Reply 1", "user": "U1"},
                        {"text": "Reply 2", "user": "U2"},
                    ]
                },
            )
        )
        async with client:
            replies = await client.comms_thread_read(PROJECT_ID, ts="111.222")
        assert len(replies) == 2
        assert replies[0]["text"] == "Reply 1"

    @pytest.mark.asyncio
    @respx.mock
    async def test_comms_thread_read_list_response_handled(self, client: BenmoreClient):
        """comms_thread_read now handles raw list responses correctly."""
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/comms/thread/111.222/").mock(
            return_value=httpx.Response(
                200,
                json=[{"text": "Single reply"}],
            )
        )
        async with client:
            result = await client.comms_thread_read(PROJECT_ID, ts="111.222")
        assert isinstance(result, list)
        assert result[0]["text"] == "Single reply"


class TestCommsMeetings:
    @pytest.mark.asyncio
    @respx.mock
    async def test_comms_meetings(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/comms/meetings/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"id": "m1", "title": "Standup", "date": "2024-03-01T09:00:00"},
                        {"id": "m2", "title": "Retro", "date": "2024-03-02T10:00:00"},
                    ]
                },
            )
        )
        async with client:
            meetings = await client.comms_meetings(PROJECT_ID)
        assert len(meetings) == 2
        assert isinstance(meetings[0], Meeting)
        assert meetings[0].title == "Standup"

    @pytest.mark.asyncio
    @respx.mock
    async def test_comms_meetings_with_full_param(self, client: BenmoreClient):
        route = respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/comms/meetings/").mock(
            return_value=httpx.Response(200, json={"results": []})
        )
        async with client:
            await client.comms_meetings(PROJECT_ID, full=True)
        assert "full=true" in str(route.calls[0].request.url)

    @pytest.mark.asyncio
    @respx.mock
    async def test_comms_meetings_list_response_handled(self, client: BenmoreClient):
        """comms_meetings now handles raw list responses correctly."""
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/comms/meetings/").mock(
            return_value=httpx.Response(
                200,
                json=[{"id": "m1", "title": "Meeting", "date": "2024-03-01T09:00:00"}],
            )
        )
        async with client:
            result = await client.comms_meetings(PROJECT_ID)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].title == "Meeting"

    @pytest.mark.asyncio
    @respx.mock
    async def test_comms_meetings_empty(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/comms/meetings/").mock(
            return_value=httpx.Response(200, json={"results": []})
        )
        async with client:
            meetings = await client.comms_meetings(PROJECT_ID)
        assert meetings == []


class TestCommsMeetingCreate:
    @pytest.mark.asyncio
    @respx.mock
    async def test_comms_meeting_create_minimal(self, client: BenmoreClient):
        respx.post(f"{BASE_URL}/projects/{PROJECT_ID}/comms/meetings/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "m-new",
                    "title": "New Meeting",
                    "date": "2024-04-01T10:00:00",
                },
            )
        )
        async with client:
            meeting = await client.comms_meeting_create(
                PROJECT_ID, title="New Meeting", date="2024-04-01T10:00:00"
            )
        assert isinstance(meeting, Meeting)
        assert meeting.title == "New Meeting"

    @pytest.mark.asyncio
    @respx.mock
    async def test_comms_meeting_create_full(self, client: BenmoreClient):
        route = respx.post(f"{BASE_URL}/projects/{PROJECT_ID}/comms/meetings/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "m-new",
                    "title": "Full Meeting",
                    "date": "2024-04-01T10:00:00",
                    "duration_minutes": 60,
                    "attendees": ["Alice", "Bob"],
                },
            )
        )
        async with client:
            await client.comms_meeting_create(
                PROJECT_ID,
                title="Full Meeting",
                date="2024-04-01T10:00:00",
                duration_minutes=60,
                attendees=["Alice", "Bob"],
            )
        import json

        body = json.loads(route.calls[0].request.content)
        assert body["title"] == "Full Meeting"
        assert body["duration_minutes"] == 60
        assert body["attendees"] == ["Alice", "Bob"]


# ─── GitHub/Planning endpoint tests ───────────────────────────────────


class TestGitHubBoard:
    @pytest.mark.asyncio
    @respx.mock
    async def test_github_board(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/github/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "gh1",
                    "title": "Sprint Board",
                    "items": [{"id": "i1", "title": "Task", "status": "Todo"}],
                    "status_counts": {"Todo": 3, "Done": 5},
                    "iterations": [],
                },
            )
        )
        async with client:
            board = await client.github_board(PROJECT_ID)
        assert isinstance(board, GitHubBoard)
        assert board.title == "Sprint Board"
        assert len(board.items) == 1
        assert board.status_counts["Done"] == 5


class TestGitHubConnect:
    @pytest.mark.asyncio
    @respx.mock
    async def test_github_connect(self, client: BenmoreClient):
        route = respx.patch(f"{BASE_URL}/projects/{PROJECT_ID}/github/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "gh99",
                    "title": "Connected Board",
                    "items": [],
                    "iterations": [],
                },
            )
        )
        async with client:
            board = await client.github_connect(PROJECT_ID, github_project_id="99")
        assert isinstance(board, GitHubBoard)
        assert board.id == "gh99"
        import json

        body = json.loads(route.calls[0].request.content)
        assert body["github_project_id"] == "99"


class TestGitHubItemCreate:
    @pytest.mark.asyncio
    @respx.mock
    async def test_github_item_create_minimal(self, client: BenmoreClient):
        respx.post(f"{BASE_URL}/projects/{PROJECT_ID}/github/items/").mock(
            return_value=httpx.Response(
                200,
                json={"id": "item1", "title": "New Ticket"},
            )
        )
        async with client:
            result = await client.github_item_create(PROJECT_ID, title="New Ticket")
        assert result["title"] == "New Ticket"

    @pytest.mark.asyncio
    @respx.mock
    async def test_github_item_create_full(self, client: BenmoreClient):
        route = respx.post(f"{BASE_URL}/projects/{PROJECT_ID}/github/items/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "item1",
                    "title": "Task",
                    "status": "Todo",
                    "priority": "high",
                    "size": "medium",
                },
            )
        )
        async with client:
            await client.github_item_create(
                PROJECT_ID,
                title="Task",
                status="Todo",
                priority="high",
                size="medium",
            )
        import json

        body = json.loads(route.calls[0].request.content)
        assert body["title"] == "Task"
        assert body["status"] == "Todo"
        assert body["priority"] == "high"
        assert body["size"] == "medium"


class TestGitHubItemUpdate:
    @pytest.mark.asyncio
    @respx.mock
    async def test_github_item_update(self, client: BenmoreClient):
        route = respx.patch(f"{BASE_URL}/projects/{PROJECT_ID}/github/items/").mock(
            return_value=httpx.Response(
                200,
                json={"id": "item1", "status": "In Progress"},
            )
        )
        async with client:
            result = await client.github_item_update(
                PROJECT_ID, item_id="item1", field="status", value="In Progress"
            )
        assert result["status"] == "In Progress"
        import json

        body = json.loads(route.calls[0].request.content)
        assert body["item_id"] == "item1"
        assert body["field"] == "status"
        assert body["value"] == "In Progress"


class TestGitHubItemDelete:
    @pytest.mark.asyncio
    @respx.mock
    async def test_github_item_delete(self, client: BenmoreClient):
        route = respx.delete(f"{BASE_URL}/projects/{PROJECT_ID}/github/items/").mock(
            return_value=httpx.Response(200, json={"status": "deleted"})
        )
        async with client:
            result = await client.github_item_delete(PROJECT_ID, item_id="item1")
        assert result["status"] == "deleted"
        import json

        body = json.loads(route.calls[0].request.content)
        assert body["item_id"] == "item1"


class TestGitHubRepos:
    @pytest.mark.asyncio
    @respx.mock
    async def test_github_repos_with_results_key(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/github/repos/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "name": "backend",
                            "url": "https://github.com/org/backend",
                            "commits": 120,
                        },
                    ]
                },
            )
        )
        async with client:
            repos = await client.github_repos(PROJECT_ID)
        assert len(repos) == 1
        assert repos[0]["name"] == "backend"

    @pytest.mark.asyncio
    @respx.mock
    async def test_github_repos_list_response_handled(self, client: BenmoreClient):
        """github_repos now handles raw list responses correctly."""
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/github/repos/").mock(
            return_value=httpx.Response(
                200,
                json=[{"name": "frontend", "url": "https://github.com/org/frontend"}],
            )
        )
        async with client:
            result = await client.github_repos(PROJECT_ID)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == "frontend"


class TestGitHubRepoLink:
    @pytest.mark.asyncio
    @respx.mock
    async def test_github_repo_link(self, client: BenmoreClient):
        route = respx.post(f"{BASE_URL}/projects/{PROJECT_ID}/github/repos/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "r1",
                    "url": "https://github.com/org/repo",
                    "status": "linked",
                },
            )
        )
        async with client:
            result = await client.github_repo_link(
                PROJECT_ID, repo_url="https://github.com/org/repo"
            )
        assert result["status"] == "linked"
        import json

        body = json.loads(route.calls[0].request.content)
        assert body["url"] == "https://github.com/org/repo"


class TestGitHubRepoUnlink:
    @pytest.mark.asyncio
    @respx.mock
    async def test_github_repo_unlink(self, client: BenmoreClient):
        route = respx.delete(f"{BASE_URL}/projects/{PROJECT_ID}/github/repos/").mock(
            return_value=httpx.Response(200, json={"status": "unlinked"})
        )
        async with client:
            result = await client.github_repo_unlink(PROJECT_ID, repo_id="r1")
        assert result["status"] == "unlinked"
        import json

        body = json.loads(route.calls[0].request.content)
        assert body["repo_id"] == "r1"


# ─── Flash Documents endpoint tests ───────────────────────────────────


class TestFlashDocumentsList:
    @pytest.mark.asyncio
    @respx.mock
    async def test_flash_documents_list_with_results(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/flash-documents/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"id": "fd1", "title": "Doc A", "type": "specification"},
                        {"id": "fd2", "title": "Doc B", "type": "proposal"},
                    ]
                },
            )
        )
        async with client:
            docs = await client.flash_documents_list()
        assert len(docs) == 2
        assert isinstance(docs[0], Document)
        assert docs[0].title == "Doc A"

    @pytest.mark.asyncio
    @respx.mock
    async def test_flash_documents_list_list_response_handled(
        self, client: BenmoreClient
    ):
        """flash_documents_list now handles raw list responses correctly."""
        respx.get(f"{BASE_URL}/flash-documents/").mock(
            return_value=httpx.Response(
                200,
                json=[{"id": "fd1", "title": "Doc"}],
            )
        )
        async with client:
            result = await client.flash_documents_list()
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].title == "Doc"

    @pytest.mark.asyncio
    @respx.mock
    async def test_flash_documents_list_empty(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/flash-documents/").mock(
            return_value=httpx.Response(200, json={"results": []})
        )
        async with client:
            docs = await client.flash_documents_list()
        assert docs == []


class TestFlashDocumentsCreate:
    @pytest.mark.asyncio
    @respx.mock
    async def test_flash_documents_create_minimal(self, client: BenmoreClient):
        respx.post(f"{BASE_URL}/flash-documents/").mock(
            return_value=httpx.Response(
                200,
                json={"id": "fd-new", "title": "New Doc"},
            )
        )
        async with client:
            doc = await client.flash_documents_create(title="New Doc")
        assert isinstance(doc, Document)
        assert doc.title == "New Doc"

    @pytest.mark.asyncio
    @respx.mock
    async def test_flash_documents_create_full(self, client: BenmoreClient):
        route = respx.post(f"{BASE_URL}/flash-documents/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "fd-new",
                    "title": "Full Doc",
                    "type": "specification",
                    "content": "# Spec",
                },
            )
        )
        async with client:
            await client.flash_documents_create(
                title="Full Doc", content="# Spec", doc_type="specification"
            )
        import json

        body = json.loads(route.calls[0].request.content)
        assert body["title"] == "Full Doc"
        assert body["content"] == "# Spec"
        assert body["type"] == "specification"


class TestFlashDocumentsGet:
    @pytest.mark.asyncio
    @respx.mock
    async def test_flash_documents_get(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/flash-documents/my-doc-slug/").mock(
            return_value=httpx.Response(
                200,
                json={"id": "fd1", "title": "My Doc", "content": "Full content here"},
            )
        )
        async with client:
            doc = await client.flash_documents_get(slug="my-doc-slug")
        assert isinstance(doc, Document)
        assert doc.content == "Full content here"


class TestFlashDocumentsUpdate:
    @pytest.mark.asyncio
    @respx.mock
    async def test_flash_documents_update(self, client: BenmoreClient):
        route = respx.patch(f"{BASE_URL}/flash-documents/my-doc-slug/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "fd1",
                    "title": "Updated Title",
                    "content": "Updated content",
                },
            )
        )
        async with client:
            doc = await client.flash_documents_update(
                slug="my-doc-slug", title="Updated Title", content="Updated content"
            )
        assert isinstance(doc, Document)
        assert doc.title == "Updated Title"
        import json

        body = json.loads(route.calls[0].request.content)
        assert body["title"] == "Updated Title"
        assert body["content"] == "Updated content"

    @pytest.mark.asyncio
    @respx.mock
    async def test_flash_documents_update_partial(self, client: BenmoreClient):
        route = respx.patch(f"{BASE_URL}/flash-documents/my-doc/").mock(
            return_value=httpx.Response(
                200,
                json={"id": "fd1", "title": "Only Title"},
            )
        )
        async with client:
            await client.flash_documents_update(slug="my-doc", title="Only Title")
        import json

        body = json.loads(route.calls[0].request.content)
        assert "title" in body
        assert "content" not in body


class TestFlashDocumentsDelete:
    @pytest.mark.asyncio
    @respx.mock
    async def test_flash_documents_delete(self, client: BenmoreClient):
        respx.delete(f"{BASE_URL}/flash-documents/my-doc-slug/").mock(
            return_value=httpx.Response(200, json={"status": "deleted"})
        )
        async with client:
            result = await client.flash_documents_delete(slug="my-doc-slug")
        assert result["status"] == "deleted"


# ─── Convenience method tests ─────────────────────────────────────────


class TestGetTeamChannels:
    @pytest.mark.asyncio
    @respx.mock
    async def test_get_team_channels_with_project_ids(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/p1/comms/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "channel_id": "C1",
                    "total_messages": 5,
                    "last_message_at": "2024-01-01T00:00:00",
                },
            )
        )
        respx.get(f"{BASE_URL}/projects/p2/comms/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "channel_id": "C2",
                    "total_messages": 10,
                    "last_message_at": "2024-01-02T00:00:00",
                },
            )
        )
        async with client:
            channels = await client.get_team_channels(project_ids=["p1", "p2"])
        assert "p1" in channels
        assert "p2" in channels
        assert len(channels["p1"]) == 1
        assert isinstance(channels["p1"][0], Channel)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_team_channels_handles_error(self, client: BenmoreClient):
        """When a project has no channel (404), it should return empty list for that project."""
        respx.get(f"{BASE_URL}/projects/p1/comms/").mock(
            return_value=httpx.Response(
                404,
                json={"error": "No Slack channel connected."},
            )
        )
        async with client:
            channels = await client.get_team_channels(project_ids=["p1"])
        assert channels["p1"] == []

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_team_channels_fetches_projects_when_none(
        self, client: BenmoreClient
    ):
        """When project_ids is None, should fetch projects list first."""
        respx.get(f"{BASE_URL}/projects/").mock(
            return_value=httpx.Response(
                200,
                json=[{"id": "auto1", "title": "Auto Project"}],
            )
        )
        respx.get(f"{BASE_URL}/projects/auto1/comms/").mock(
            return_value=httpx.Response(
                200,
                json={"channel_id": "C-auto", "total_messages": 1},
            )
        )
        async with client:
            channels = await client.get_team_channels()
        assert "auto1" in channels


class TestGetProjectTeamByRole:
    @pytest.mark.asyncio
    @respx.mock
    async def test_get_project_team_by_role_all(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/team/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "team_members": [
                        {
                            "username": "alice",
                            "name": "Alice",
                            "title": "Lead Developer",
                        },
                        {"username": "bob", "name": "Bob", "title": "Designer"},
                    ]
                },
            )
        )
        async with client:
            members = await client.get_project_team_by_role(PROJECT_ID)
        assert len(members) == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_project_team_by_role_filtered(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/team/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "team_members": [
                        {
                            "username": "alice",
                            "name": "Alice",
                            "title": "Lead Developer",
                        },
                        {"username": "bob", "name": "Bob", "title": "Designer"},
                        {
                            "username": "carol",
                            "name": "Carol",
                            "title": "Lead Developer",
                        },
                    ]
                },
            )
        )
        async with client:
            leads = await client.get_project_team_by_role(
                PROJECT_ID, role="Lead Developer"
            )
        assert len(leads) == 2
        assert all(m.role == "Lead Developer" for m in leads)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_project_team_by_role_no_match(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/{PROJECT_ID}/team/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "team_members": [
                        {"username": "alice", "name": "Alice", "title": "Developer"},
                    ]
                },
            )
        )
        async with client:
            managers = await client.get_project_team_by_role(PROJECT_ID, role="Manager")
        assert managers == []


# ─── Edge cases and error handling ────────────────────────────────────


class TestClientEdgeCases:
    @pytest.mark.asyncio
    @respx.mock
    async def test_401_unauthorized_raises(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/").mock(
            return_value=httpx.Response(401, json={"detail": "Invalid API key"})
        )
        async with client:
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await client.projects_list()
            assert exc_info.value.response.status_code == 401

    @pytest.mark.asyncio
    @respx.mock
    async def test_403_forbidden_raises(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/").mock(
            return_value=httpx.Response(403, json={"detail": "Forbidden"})
        )
        async with client:
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await client.projects_list()
            assert exc_info.value.response.status_code == 403

    @pytest.mark.asyncio
    @respx.mock
    async def test_422_validation_error_raises(self, client: BenmoreClient):
        respx.post(f"{BASE_URL}/projects/{PROJECT_ID}/team/").mock(
            return_value=httpx.Response(422, json={"detail": "Validation error"})
        )
        async with client:
            with pytest.raises(httpx.HTTPStatusError):
                await client.team_add(PROJECT_ID, usernames=["invalid"])

    @pytest.mark.asyncio
    @respx.mock
    async def test_connection_error(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        async with client:
            with pytest.raises(httpx.ConnectError):
                await client.projects_list()

    @pytest.mark.asyncio
    @respx.mock
    async def test_timeout_error(self, client: BenmoreClient):
        respx.get(f"{BASE_URL}/projects/").mock(
            side_effect=httpx.ReadTimeout("Timeout")
        )
        async with client:
            with pytest.raises(httpx.ReadTimeout):
                await client.projects_list()

    def test_multiple_clients_independent(self):
        c1 = BenmoreClient(api_key="key1")
        c2 = BenmoreClient(api_key="key2", base_url="https://other.com/api")
        assert c1.api_key != c2.api_key
        assert c1.base_url != c2.base_url
