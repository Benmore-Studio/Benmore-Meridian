"""Benmore Client API v2 - Production Python Client

Unified interface to Benmore project management, communications, and planning APIs.
Type-safe, async-first design with comprehensive Pydantic models.

Example:
    from benmore_client import BenmoreClient

    client = BenmoreClient(api_key="bpk_...")
    projects = await client.projects.list()
    channels = await client.get_team_channels()
"""

from .client import BenmoreClient
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
    Meeting,
    Project,
    ProjectContext,
    ProjectStatus,
    TeamMember,
)

__version__ = "1.0.0"
__all__ = [
    "BenmoreClient",
    # Enums
    "Phase",
    "Status",
    "Priority",
    "Size",
    "Severity",
    "DocumentType",
    # Models
    "Project",
    "ProjectContext",
    "ProjectStatus",
    "TeamMember",
    "Channel",
    "Meeting",
    "Document",
]
