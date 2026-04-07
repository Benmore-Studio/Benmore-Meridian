"""Benmore API Enumerations - Type-safe constants for domain values.

These enums provide compile-time safety for common API values used in
project management, communications, and planning workflows.
"""

from enum import Enum


class Phase(str, Enum):
    """Project lifecycle phases."""

    DISCOVERY = "discovery"
    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    LAUNCH = "launch"
    MAINTENANCE = "maintenance"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"


class Status(str, Enum):
    """General status indicators."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class Priority(str, Enum):
    """Task and item priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Size(str, Enum):
    """Estimation size for work items (story points / T-shirt sizing)."""

    XS = "xs"
    S = "small"
    M = "medium"
    L = "large"
    XL = "xl"
    XXL = "xxl"


class Severity(str, Enum):
    """Issue and bug severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DocumentType(str, Enum):
    """Types of documents in projects."""

    SPECIFICATION = "specification"
    PROPOSAL = "proposal"
    CONTRACT = "contract"
    MEETING_NOTES = "meeting_notes"
    DECISION_LOG = "decision_log"
    ARCHITECTURE = "architecture"
    ROADMAP = "roadmap"
    OTHER = "other"


class IterationStatus(str, Enum):
    """GitHub Project iteration/sprint status."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
