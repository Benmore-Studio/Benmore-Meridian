---
name: pcs-pr-review
description: Use when reviewing pull requests for PCS microservices - covers architecture compliance, multi-tenant safety, Kafka event contracts, Kong route validation, security checks, and test coverage requirements
---

# PCS: PR Review

Architecture-aware review checklist for PCS microservice pull requests.

## Review Order

1. **Architecture** - Does it fit the microservice boundaries?
2. **Multi-tenancy** - Is org_id enforced everywhere?
3. **Security** - Auth, encryption, input validation?
4. **Events** - Kafka contracts followed?
5. **Infrastructure** - Kong, Docker, migrations correct?
6. **Tests** - Coverage adequate?
7. **Code quality** - Patterns, types, logging?

## 1. Architecture Compliance

- [ ] Changes stay within one service boundary (no cross-service model imports)
- [ ] Service-to-service calls use HTTP (`httpx`) or Kafka (never direct DB access)
- [ ] New endpoints follow REST conventions (`/api/v1/{resource}`)
- [ ] Response schemas use `DataResponse` or `PaginatedResponse` wrappers
- [ ] No business logic in routers (belongs in services layer)

## 2. Multi-Tenant Safety (Critical)

- [ ] Every `SELECT` query filters by `org_id`
- [ ] Every `UPDATE`/`DELETE` filters by BOTH `id` AND `org_id`
- [ ] JOINs don't cross tenant boundaries
- [ ] Aggregations (COUNT, SUM) scoped to `org_id`
- [ ] Wrong-tenant access returns 404 (not 403 - leaks resource existence)
- [ ] Kafka handlers wrap logic in `TenantScope(org_id=...)`
- [ ] New endpoints use `Depends(get_tenant_context)`

## 3. Security

- [ ] Sensitive data encrypted (SSN uses Fernet, not stored plaintext)
- [ ] No secrets in code (API keys, passwords in env vars only)
- [ ] Input validated via Pydantic schemas (no raw dict access)
- [ ] SQL injection impossible (SQLAlchemy ORM, no raw SQL)
- [ ] Rate limiting on public-facing endpoints
- [ ] Audit events emitted for security-sensitive operations

## 4. Kafka Event Contracts

- [ ] Topic follows `pcs.<domain>.<entity>.<action>` naming
- [ ] Payload includes mandatory fields: `request_id`, `org_id`, `timestamp`, `source_service`
- [ ] Partition key = `org_id` (tenant ordering guarantee)
- [ ] Handler registered in `register_all_handlers()` BEFORE consumer starts
- [ ] Handler is idempotent (safe to replay)
- [ ] New topics documented in CLAUDE.md

## 5. Infrastructure

### Kong (`kong/kong.yml`)
- [ ] New routes don't conflict with existing paths
- [ ] `strip_path` matches upstream URL structure
- [ ] Health check path exists on new service
- [ ] JWT bypass added for unauthenticated routes (webhooks, health)

### Docker (`docker-compose.yml`)
- [ ] Service block added with correct port
- [ ] `depends_on` includes postgres and kafka (if needed)
- [ ] Health check configured
- [ ] Environment variables set (DB, Kafka, Redis, Auth URL)

### Migrations
- [ ] New tables have `org_id` column with index
- [ ] `downgrade()` properly reverses `upgrade()`
- [ ] `DateTime` columns use `timezone=True`
- [ ] Models imported in `app/models/__init__.py`

## 6. Test Coverage

- [ ] CRUD tests for new endpoints
- [ ] Missing X-Org-Id returns 400
- [ ] Cross-tenant isolation test (Org B can't access Org A data)
- [ ] Kafka events mocked and assertions on topic/payload
- [ ] Edge cases: empty input, duplicate records, not-found
- [ ] Tests pass: `cd <service> && uv run pytest tests/ -q`

## 7. Code Quality

- [ ] Type hints on all function signatures
- [ ] Structured logging (`structlog`) instead of `print()`
- [ ] `model_config = {"from_attributes": True}` on response schemas
- [ ] Ruff passes: `uv run ruff check .`
- [ ] No commented-out code
- [ ] No hardcoded UUIDs or magic strings

## Quick Rejection Criteria

Immediately request changes if any of these are true:

| Issue | Severity |
|-------|----------|
| Missing `org_id` filter on query | **Critical** - tenant data leak |
| Plaintext sensitive data storage | **Critical** - compliance violation |
| Cross-service direct DB import | **Critical** - architecture violation |
| No tests for new endpoint | **High** - untested code |
| Wrong-tenant returns 403 instead of 404 | **High** - info leak |
| Missing Kafka event on state change | **Medium** - broken async contract |
| No migration for schema change | **Medium** - deploy will fail |

## Review Comment Template

```markdown
### PR Review: #{number}

**Architecture:** {pass/issues}
**Multi-tenancy:** {pass/issues}
**Security:** {pass/issues}
**Events:** {pass/N/A}
**Infrastructure:** {pass/issues}
**Tests:** {pass/needs work}
**Code quality:** {pass/minor issues}

**Verdict:** {Approve / Request Changes}

#### Issues
1. {file}:{line} - {description}
2. ...
```
