---
name: multi-tenant-guard
description: Use when implementing or auditing multi-tenant isolation in shared-database architectures - covers row-level org_id filtering, context propagation, tenant-aware queries, cross-tenant data leak prevention, and isolation testing
---

# Multi-Tenant Guard

Enforce and audit tenant isolation in shared-schema multi-tenant applications.

## When to Use
- Adding new database queries (must filter by org_id)
- Creating new endpoints accessing tenant-scoped data
- Auditing existing code for missing tenant filters
- Writing cross-tenant isolation tests
- Setting up tenant context from API gateway headers

## Core Pattern

### 1. Tenant Context
```python
from dataclasses import dataclass, field
from uuid import UUID

@dataclass
class TenantContext:
    org_id: UUID
    user_id: UUID | None = None
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
```

### 2. Header Extraction
```python
async def get_tenant_context(
    x_org_id: Annotated[str | None, Header()] = None,
    x_user_id: Annotated[str | None, Header()] = None,
    x_roles: Annotated[str | None, Header()] = None,
    x_permissions: Annotated[str | None, Header()] = None,
) -> TenantContext:
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id header required")
    return TenantContext(
        org_id=UUID(x_org_id),
        user_id=UUID(x_user_id) if x_user_id else None,
        roles=x_roles.split(",") if x_roles else [],
        permissions=x_permissions.split(",") if x_permissions else [],
    )
```

### 3. ContextVar for Background Tasks
```python
from contextvars import ContextVar

_current_org_id: ContextVar[UUID | None] = ContextVar("current_org_id", default=None)

class TenantScope:
    def __init__(self, org_id: UUID):
        self.org_id = org_id
        self._token = None
    def __enter__(self):
        self._token = _current_org_id.set(self.org_id)
        return self
    def __exit__(self, *args):
        _current_org_id.reset(self._token)
```

### 4. Tenant-Aware Queries
```python
# EVERY query MUST include org_id
result = await db.execute(
    select(Employee).where(Employee.org_id == org_id)  # Always filter
)

# UPDATE/DELETE must include BOTH org_id AND id
await db.execute(
    update(Employee).where(Employee.id == id, Employee.org_id == org_id).values(**data)
)
```

### 5. Middleware to Clear Context
```python
@app.middleware("http")
async def clear_tenant_context(request, call_next):
    try:
        return await call_next(request)
    finally:
        _current_org_id.set(None)  # Prevent leaking between requests
```

## Audit Checklist

1. [ ] SELECT has `WHERE org_id = :org_id`
2. [ ] UPDATE has `WHERE org_id = :org_id AND id = :id`
3. [ ] DELETE has `WHERE org_id = :org_id AND id = :id`
4. [ ] JOINs don't cross tenant boundaries
5. [ ] Aggregations scoped to org_id
6. [ ] Pagination doesn't leak cross-tenant totals
7. [ ] Search filters by org_id BEFORE text search
8. [ ] Kafka handlers set TenantScope
9. [ ] Background jobs iterate per-tenant
10. [ ] Wrong-tenant access returns 404 (not 403)

## Isolation Test Template

```python
ORG_A, ORG_B = str(uuid4()), str(uuid4())

def headers_for(org_id):
    return {"X-Org-Id": org_id, "X-User-Id": str(uuid4()), "X-Roles": "admin"}

@pytest.mark.asyncio
async def test_tenant_isolation(client):
    # Org A creates resource
    resp = await client.post("/api/v1/resources", json={"name": "Secret"}, headers=headers_for(ORG_A))
    rid = resp.json()["data"]["id"]

    # Org B cannot see it
    resp = await client.get("/api/v1/resources", headers=headers_for(ORG_B))
    assert rid not in [r["id"] for r in resp.json()["data"]]

    # Org B gets 404 on direct access, update, delete
    assert (await client.get(f"/api/v1/resources/{rid}", headers=headers_for(ORG_B))).status_code == 404
    assert (await client.put(f"/api/v1/resources/{rid}", json={"name": "X"}, headers=headers_for(ORG_B))).status_code == 404
    assert (await client.delete(f"/api/v1/resources/{rid}", headers=headers_for(ORG_B))).status_code == 404
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Missing org_id on UPDATE/DELETE | Always `AND org_id = :org_id` |
| 403 for wrong tenant | Use 404 - 403 leaks resource exists |
| Global COUNT | `WHERE org_id = :org_id` on aggregations |
| Kafka handler no TenantScope | Wrap in `with TenantScope(org_id):` |
| Not clearing ContextVar | Middleware resets to None after each request |
| JOINs crossing boundary | Both sides filtered by org_id |
