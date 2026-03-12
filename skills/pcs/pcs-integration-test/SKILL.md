---
name: pcs-integration-test
description: Use when writing integration or unit tests for PCS microservices - covers async test fixtures, SQLite in-memory setup, tenant header helpers, dependency override patterns, Kafka mock strategies, and cross-tenant isolation tests
---

# PCS: Integration Tests

Write tests for PCS FastAPI microservices using pytest-asyncio with SQLite in-memory.

## Run Tests

```bash
cd <service-name>
uv run pytest tests/ -q              # Quick run
uv run pytest tests/ -v              # Verbose
uv run pytest tests/ --cov=app       # With coverage
uv run pytest tests/test_orders.py -k "test_create"  # Specific test
```

## conftest.py Template

Every service follows this pattern:

```python
import asyncio
from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_db
from app.main import create_app
from app.models.base import Base


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture
async def test_app(test_session: AsyncSession):
    app = create_app()
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_session
    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def client(test_app) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def test_org_id() -> str:
    return str(uuid4())


@pytest.fixture
def test_user_id() -> str:
    return str(uuid4())


@pytest.fixture
def tenant_headers(test_org_id: str, test_user_id: str) -> dict[str, str]:
    return {
        "X-Org-Id": test_org_id,
        "X-User-Id": test_user_id,
        "X-Roles": "admin",
        "X-Permissions": "resource:read,resource:write",
    }
```

## Test Patterns

### CRUD Endpoint Test

```python
@pytest.mark.asyncio
async def test_create_resource(client: AsyncClient, tenant_headers: dict):
    resp = await client.post(
        "/api/v1/resources",
        json={"name": "Test Resource"},
        headers=tenant_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Test Resource"


@pytest.mark.asyncio
async def test_list_resources(client: AsyncClient, tenant_headers: dict):
    # Create first
    await client.post("/api/v1/resources", json={"name": "R1"}, headers=tenant_headers)
    await client.post("/api/v1/resources", json={"name": "R2"}, headers=tenant_headers)

    resp = await client.get("/api/v1/resources", headers=tenant_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 2
```

### Missing Tenant Header Test

```python
@pytest.mark.asyncio
async def test_missing_org_id_returns_400(client: AsyncClient):
    resp = await client.get("/api/v1/resources")
    assert resp.status_code == 400
    assert "X-Org-Id" in resp.json()["detail"]
```

### Cross-Tenant Isolation Test

```python
ORG_A, ORG_B = str(uuid4()), str(uuid4())

def headers_for(org_id: str) -> dict:
    return {"X-Org-Id": org_id, "X-User-Id": str(uuid4()), "X-Roles": "admin"}

@pytest.mark.asyncio
async def test_tenant_isolation(client: AsyncClient):
    # Org A creates resource
    resp = await client.post("/api/v1/resources", json={"name": "Secret"}, headers=headers_for(ORG_A))
    rid = resp.json()["data"]["id"]

    # Org B cannot see it
    resp = await client.get("/api/v1/resources", headers=headers_for(ORG_B))
    assert rid not in [r["id"] for r in resp.json()["data"]]

    # Org B gets 404 on direct access (not 403)
    assert (await client.get(f"/api/v1/resources/{rid}", headers=headers_for(ORG_B))).status_code == 404
    assert (await client.put(f"/api/v1/resources/{rid}", json={"name": "X"}, headers=headers_for(ORG_B))).status_code == 404
    assert (await client.delete(f"/api/v1/resources/{rid}", headers=headers_for(ORG_B))).status_code == 404
```

### Mocking Kafka Events

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_create_emits_kafka_event(client: AsyncClient, tenant_headers: dict):
    with patch("app.events.emitters.publish", new_callable=AsyncMock) as mock_publish:
        resp = await client.post("/api/v1/resources", json={"name": "Test"}, headers=tenant_headers)
        assert resp.status_code == 201
        mock_publish.assert_called_once()
        call_args = mock_publish.call_args
        assert call_args.kwargs["topic"] == "pcs.domain.resource.created"
```

### Mocking External HTTP Calls

```python
@pytest.mark.asyncio
async def test_service_with_external_call(client: AsyncClient, tenant_headers: dict):
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "value"}

    with patch("app.services.my_service.http_client.get", return_value=mock_response):
        resp = await client.get("/api/v1/resources/external", headers=tenant_headers)
        assert resp.status_code == 200
```

## Key Gotchas

| Issue | Fix |
|-------|-----|
| `AsyncMock` returns coroutine, not dict | Set `mock.method.return_value = {...}` explicitly |
| SQLite doesn't support UUID natively | Models use `String(36)` or test with `str(uuid4())` |
| Patch path wrong | Patch where imported: `app.services.my_service.publish`, not `app.events.emitters.publish` |
| `event_loop` deprecation warning | Use `scope="session"` fixture as shown above |
| Tests pollute each other | Each test gets fresh `test_engine` fixture (table recreated) |
| Bulk test state leakage | Clean up created records between iterations |

## Checklist

1. [ ] Test file: `tests/test_{resource}.py`
2. [ ] Uses `tenant_headers` fixture for all authenticated endpoints
3. [ ] Tests: create, read, list, update, delete (CRUD)
4. [ ] Tests: missing X-Org-Id returns 400
5. [ ] Tests: cross-tenant isolation (Org B can't see Org A data)
6. [ ] Tests: wrong-tenant access returns 404 (not 403)
7. [ ] Kafka events mocked with `patch` + `AsyncMock`
8. [ ] External HTTP calls mocked
9. [ ] All tests pass: `uv run pytest tests/ -q`
