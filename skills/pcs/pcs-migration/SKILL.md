---
name: pcs-migration
description: Use when creating or modifying Alembic database migrations for PCS services - covers async engine setup, autogenerate, multi-tenant column requirements, migration ordering, and rollback procedures
---

# PCS: Alembic Migration

Create and manage database migrations for PCS microservices using Alembic with async SQLAlchemy.

## Quick Reference

```bash
cd <service-name>

# Create migration (autogenerate from model changes)
alembic revision --autogenerate -m "Add employee_status column"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current migration
alembic current

# Show migration history
alembic history --verbose
```

## Migration Naming Convention

Format: `YYYY_MM_DD_HHMM_{description}.py`

Alembic generates the timestamp prefix. Use descriptive `-m` messages:

```bash
# Good
alembic revision --autogenerate -m "Add consent_records table"
alembic revision --autogenerate -m "Add index on employees org_id"
alembic revision --autogenerate -m "Add kyc_status to employees"

# Bad
alembic revision --autogenerate -m "update"
alembic revision --autogenerate -m "fix"
```

## env.py Pattern (Async)

All PCS services use the same async pattern:

```python
import asyncio
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.models import Base

config = context.config
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)
target_metadata = Base.metadata

async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(
            lambda conn: context.configure(connection=conn, target_metadata=target_metadata)
        )
        await connection.run_sync(lambda conn: context.run_migrations())
    await connectable.dispose()
```

## Multi-Tenant Column Requirements

Every new table MUST include:

```python
def upgrade() -> None:
    op.create_table(
        "my_table",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("org_id", sa.UUID(), nullable=False, index=True),  # REQUIRED
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        # ... other columns
    )
    # Always index org_id for tenant queries
    op.create_index("ix_my_table_org_id", "my_table", ["org_id"])
```

## Common Migration Operations

### Add column
```python
def upgrade() -> None:
    op.add_column("employees", sa.Column("status", sa.String(20), nullable=True))

def downgrade() -> None:
    op.drop_column("employees", "status")
```

### Add index
```python
def upgrade() -> None:
    op.create_index("ix_employees_email_org", "employees", ["email", "org_id"], unique=True)

def downgrade() -> None:
    op.drop_index("ix_employees_email_org")
```

### Add table with foreign key
```python
def upgrade() -> None:
    op.create_table(
        "consent_records",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("org_id", sa.UUID(), nullable=False),
        sa.Column("consent_type", sa.String(100), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_consent_user", "consent_records", ["user_id", "consent_type"])

def downgrade() -> None:
    op.drop_table("consent_records")
```

### Rename column (data-safe)
```python
def upgrade() -> None:
    op.alter_column("employees", "ssn", new_column_name="social_security_number")

def downgrade() -> None:
    op.alter_column("employees", "social_security_number", new_column_name="ssn")
```

## Model Import Requirement

All models MUST be imported in `app/models/__init__.py` for autogenerate to detect them:

```python
# app/models/__init__.py
from app.models.base import Base
from app.models.employee import Employee
from app.models.consent_record import ConsentRecord  # NEW - add here
```

## Checklist

1. [ ] Model imported in `app/models/__init__.py`
2. [ ] `org_id` column present and indexed on new tables
3. [ ] `downgrade()` reverses all `upgrade()` operations
4. [ ] Foreign keys have `ondelete` behavior specified
5. [ ] `DateTime` columns use `timezone=True`
6. [ ] Migration tested: `alembic upgrade head && alembic downgrade -1 && alembic upgrade head`
7. [ ] No data loss in downgrade (column drops are intentional)

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Missing model import | Add to `app/models/__init__.py` |
| No `org_id` on new table | Always add `org_id UUID NOT NULL` + index |
| Empty autogenerate | Model not imported or no changes detected |
| `nullable=False` on existing column | Add as `nullable=True` first, backfill, then alter |
| Missing `downgrade()` body | Always implement reverse operations |
| `DateTime` without timezone | Use `DateTime(timezone=True)` |
