---
name: pcs-new-service
description: Use when creating a new microservice for the PCS backend - scaffolds the complete service directory with FastAPI app, config, models, routers, services, Kafka events, Dockerfile, pyproject.toml, tests, and wires it into Kong and Docker Compose
---

# PCS: New Microservice

Scaffold a complete PCS microservice following established patterns.

## Pre-flight
```bash
ls docker-compose.yml kong/kong.yml CLAUDE.md  # Verify pcs_backend root
# Port map: 8001-auth, 8002-org, 8003-tazworks, 8004-mcp, 8005-bg, 8007-product, 8008-order, 8009-bff
```

## Directory Structure
```
{service-name}/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI + lifespan (DB -> Redis -> Kafka producer -> handlers -> consumer)
│   ├── config.py             # pydantic-settings
│   ├── cli.py                # typer CLI
│   ├── core/
│   │   ├── __init__.py
│   │   ├── database.py       # SQLAlchemy async engine + session
│   │   ├── kafka.py          # Producer/consumer + register_handler()
│   │   ├── logging.py        # structlog (JSON + console)
│   │   ├── exceptions.py     # NotFoundException, ConflictException, ValidationException
│   │   └── tenant.py         # TenantContext + ContextVar
│   ├── models/
│   │   ├── __init__.py
│   │   └── base.py           # Base, UUIDMixin, TenantMixin, TimestampMixin
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── base.py           # DataResponse, PaginatedResponse
│   │   └── common.py         # TenantContext dataclass
│   ├── services/
│   │   ├── __init__.py
│   │   └── base.py           # BaseRepository (CRUD + org_id scoping)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── dependencies.py   # get_tenant_context, get_db_session
│   │   └── health.py         # GET /health
│   └── events/
│       ├── __init__.py        # register_all_handlers()
│       ├── handlers.py
│       └── emitters.py        # Topics + publish helpers
├── alembic/ (env.py, script.py.mako, versions/)
├── alembic.ini
├── tests/
│   ├── __init__.py
│   └── conftest.py           # SQLite in-memory, AsyncClient, tenant_headers
├── pyproject.toml
├── Dockerfile                # python:3.11-slim + uv
├── .env
└── README.md
```

## main.py Template

```python
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    setup_logging(log_level=settings.log_level, json_format=settings.log_json_format)
    await init_database()
    await start_producer(bootstrap_servers=settings.kafka_bootstrap_servers, client_id=settings.kafka_client_id)
    register_all_handlers()
    await start_consumer(bootstrap_servers=settings.kafka_bootstrap_servers, group_id=settings.kafka_group_id)
    yield
    await stop_consumer()
    await stop_producer()
    await close_database()
```

## After Scaffolding - Wire Into Infrastructure

### 1. kong/kong.yml
```yaml
  - name: {service-name}
    url: http://{service-name}:{port}
    connect_timeout: 30000
    write_timeout: 30000
    read_timeout: 30000
    healthchecks:
      active:
        healthy: { interval: 30, successes: 2 }
        unhealthy: { interval: 10, http_failures: 3 }
        http_path: /health
        timeout: 5
    routes:
      - name: {service}-routes
        paths: ["/api/v1/{resource}"]
        strip_path: false
        protocols: ["http", "https"]
```

### 2. docker-compose.yml
```yaml
  {service-name}:
    build: { context: ./{service-name}, dockerfile: Dockerfile }
    container_name: pcs-{service-name}
    restart: unless-stopped
    env_file: [./{service-name}/.env]
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: {service}_db
      DB_USER: {service}_user
      DB_PASSWORD: ${SERVICE_DB_PASSWORD:-service_password}
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
      AUTH_SERVICE_URL: http://auth-service:8001
    depends_on:
      postgres: { condition: service_healthy }
      kafka: { condition: service_healthy }
    networks: [pcs-internal]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{port}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

### 3. scripts/init-databases.sh - add DB creation
### 4. CLAUDE.md - add to repo structure, architecture diagram, Kafka topics
