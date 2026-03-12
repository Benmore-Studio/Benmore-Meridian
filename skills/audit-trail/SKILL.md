---
name: audit-trail
description: Use when adding audit logging to API endpoints, database operations, or security events - covers model creation, structured logging, Kafka/event emission, IP/user-agent capture, and correlation ID tracking
---

# Audit Trail

Add comprehensive, compliance-ready audit logging to any FastAPI + SQLAlchemy service.

## When to Use
- Adding a new endpoint that modifies data
- Implementing security event tracking (login, password change, MFA)
- Need forensic-grade audit trail for compliance (SOC 2, HIPAA, GDPR)
- Adding request correlation across microservices

## Core Pattern

### 1. Audit Log Model
```python
from datetime import UTC, datetime
from uuid import uuid4
from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[bytes] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    # WHO
    user_id: Mapped[bytes | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    org_id: Mapped[bytes | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    # WHAT
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # CONTEXT
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    # OUTCOME
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # FLEXIBLE PAYLOAD
    extra_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC),
        server_default=func.now(), nullable=False,
    )
```

### 2. Event Type Enum
```python
from enum import StrEnum

class AuditEventType(StrEnum):
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGED = "password_changed"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    RESOURCE_CREATED = "resource_created"
    RESOURCE_UPDATED = "resource_updated"
    RESOURCE_DELETED = "resource_deleted"
    PERMISSION_DENIED = "permission_denied"
    CONSENT_GRANTED = "consent_granted"
    CONSENT_REVOKED = "consent_revoked"
    DATA_EXPORTED = "data_exported"
    DATA_DELETED = "data_deleted"
```

### 3. Audit Emitter
```python
async def emit_audit_event(
    event_type: str,
    user_id: str | None = None,
    org_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    request_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    success: bool = True,
    error_message: str | None = None,
    extra_data: dict | None = None,
    source_service: str = "unknown",
) -> bool:
    payload = {
        "event_type": event_type,
        "user_id": user_id,
        "org_id": org_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "request_id": request_id,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "success": success,
        "error_message": error_message,
        "extra_data": extra_data or {},
        "source_service": source_service,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    return await publish(topic=f"audit.{source_service}.event", key=user_id, value=payload)
```

### 4. Request Context Extraction
```python
from fastapi import Request

def extract_request_context(request: Request) -> dict[str, str | None]:
    return {
        "ip_address": request.headers.get("X-Forwarded-For", request.client.host if request.client else None),
        "user_agent": request.headers.get("User-Agent"),
        "request_id": request.headers.get("X-Request-ID"),
    }
```

### 5. Router Integration
```python
@router.post("/resources", status_code=201)
async def create_resource(data: CreateRequest, request: Request, context=Depends(get_tenant_context)):
    result = await service.create(data, context.org_id)
    await emit_audit_event(
        event_type=AuditEventType.RESOURCE_CREATED,
        user_id=str(context.user_id), org_id=str(context.org_id),
        resource_type="resource", resource_id=str(result.id),
        success=True, source_service="my-service",
        **extract_request_context(request),
    )
    return result
```

## Checklist

1. [ ] Event type defined in `AuditEventType` enum
2. [ ] Request context extracted (IP, user-agent, request-id)
3. [ ] Audit emitted AFTER successful DB commit (not before)
4. [ ] `org_id` included for multi-tenant filtering
5. [ ] `resource_type` + `resource_id` for traceability
6. [ ] Failures: `success=False` + `error_message`
7. [ ] Security events: always capture IP + user-agent
8. [ ] `request_id` index on audit_logs table

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Emit before DB commit | Emit AFTER `await session.commit()` |
| Missing IP on security events | Extract from `X-Forwarded-For` header |
| Hardcoded event type strings | Use StrEnum |
| No request_id correlation | Extract from `X-Request-ID` header |
| Audit in same transaction | Use separate session or Kafka |
| Logging PII in extra_data | Never store raw passwords, full SSN, or tokens |
