---
name: pcs-add-kafka-event
description: Use when adding a new Kafka event to a PCS service - covers topic naming, emitter function, handler registration, consumer setup, and cross-service event contracts
---

# PCS: Add Kafka Event

Add a new Kafka event (publish or consume) to a PCS microservice.

## Topic Naming: `pcs.<domain>.<entity>.<action>`

| Domain | Examples |
|--------|---------|
| auth | `pcs.auth.user.created`, `pcs.auth.login.success` |
| organization | `pcs.organization.employee.created` |
| background | `pcs.background.order.requested` |
| product | `pcs.product.created`, `pcs.product.price.changed` |
| order | `pcs.order.order.created`, `pcs.order.order.submitted` |
| audit | `pcs.audit.{service}.event` |

## Publishing

### Step 1: Topic constant in `app/events/emitters.py`
```python
class Topics:
    EMPLOYEE_CREATED = "pcs.organization.employee.created"
    EMPLOYEE_DELETED = "pcs.organization.employee.deleted"  # NEW
```

### Step 2: Emitter function
```python
async def emit_employee_deleted(org_id: str, employee_id: str, deleted_by: str | None = None, request_id: str | None = None) -> bool:
    return await publish(
        topic=Topics.EMPLOYEE_DELETED, key=org_id,
        value={"request_id": request_id, "org_id": org_id, "employee_id": employee_id,
               "deleted_by": deleted_by, "timestamp": datetime.now(UTC).isoformat(),
               "source_service": "organization-service"},
    )
```

### Step 3: Call from service/router
```python
await emit_employee_deleted(org_id=str(ctx.org_id), employee_id=str(emp.id),
                            deleted_by=str(ctx.user_id), request_id=request.headers.get("X-Request-ID"))
```

## Consuming

### Step 1: Handler in `app/events/handlers.py`
```python
async def handle_employee_created(data: dict[str, Any]) -> None:
    org_id, request_id = data.get("org_id"), data.get("request_id")
    logger.info("Handling employee.created", org_id=org_id, request_id=request_id)
    try:
        with TenantScope(org_id=UUID(org_id)):
            pass  # Business logic
    except Exception:
        logger.exception("Failed to handle employee.created", request_id=request_id)
```

### Step 2: Register in `app/events/__init__.py`
```python
def register_all_handlers() -> None:
    register_handler("pcs.organization.employee.created", handle_employee_created)
    # Register BEFORE consumer starts!
```

## Payload Contract (mandatory fields)
```json
{"request_id": "uuid", "org_id": "uuid", "timestamp": "ISO 8601", "source_service": "service-name"}
```

## Checklist

1. [ ] Topic follows `pcs.<domain>.<entity>.<action>`
2. [ ] Payload: request_id, org_id, timestamp, source_service
3. [ ] Partition key = org_id (tenant ordering)
4. [ ] Handler in TenantScope context manager
5. [ ] Handler registered BEFORE consumer starts
6. [ ] Handler is idempotent
7. [ ] Topic added to CLAUDE.md Kafka Topics Reference
