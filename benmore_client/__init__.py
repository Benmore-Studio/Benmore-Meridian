"""Benmore Client API v2 - Production Python Client

Unified interface to Benmore project management, communications, and planning APIs.
Type-safe, async-first design with comprehensive Pydantic models.

Example:
    from benmore_client import BenmoreClient

    async with BenmoreClient(api_key="bpk_...") as client:
        projects = await client.projects_list()
        channels = await client.get_team_channels()
"""

from .client import BenmoreAPIError, BenmoreClient
from .enums import (
    DocumentType,
    Phase,
    Priority,
    Severity,
    Size,
    Status,
)
from .models import (
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

__version__ = "1.0.1"
__all__ = [
    "BenmoreClient",
    "BenmoreAPIError",
    # Enums
    "Phase",
    "Status",
    "Priority",
    "Size",
    "Severity",
    "DocumentType",
    # Models
    "Project",
    "ProjectListResponse",
    "ProjectContext",
    "ProjectStatus",
    "TeamMember",
    "Channel",
    "Meeting",
    "Document",
    "GitHubBoard",
]
