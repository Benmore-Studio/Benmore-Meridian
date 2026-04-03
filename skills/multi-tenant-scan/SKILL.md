---
name: multi-tenant-scan
description: Scans all ViewSets, querysets, and API endpoints for missing tenant isolation filters. Catches data leaks where one tenant can see another's data. Framework-aware for Django, FastAPI, and Rails.
context: fork
---

# Multi-Tenant Isolation Scanner

Systematically scan an entire codebase for missing tenant isolation filters — the #1 security vulnerability in multi-tenant SaaS applications.

## When to Use
- After adding a new ViewSet, endpoint, or queryset
- Before any release or security audit
- When onboarding a new module to an existing multi-tenant system
- After refactoring queryset logic
- Periodically (monthly) as a hygiene check

## The Problem

In shared-database multi-tenancy, every query that returns data MUST filter by the tenant identifier. A single missing filter means Tenant A can see Tenant B's data.

```
DANGEROUS:
    Model.objects.all()                        ← returns ALL tenants' data
    Model.objects.filter(status='active')      ← still returns all tenants

SAFE:
    Model.objects.filter(operation=request.user.current_operation)
    Model.objects.filter(org_id=tenant_context.org_id)
```

## Workflow

### Step 1: Detect Tenant Architecture

Read the project's main documentation or settings to identify:

```
┌──────────────────────────────────────────────┐
│ Tenant Configuration                          │
├──────────────────────────────────────────────┤
│ Framework:     Django / FastAPI / Rails        │
│ Tenant field:  operation / org_id / tenant_id  │
│ Context source: middleware / dependency / scope │
│ Exempt models: User, SiteContent, etc.         │
│ Exempt paths:  /admin/, /health/, /public/     │
└──────────────────────────────────────────────┘
```

**Auto-detection patterns:**

| Framework | Look for | Tenant field |
|-----------|----------|-------------|
| Django | `OperationContextMiddleware`, `current_operation` | `operation` |
| FastAPI | `get_tenant_context`, `Depends(get_org)` | `org_id` |
| Rails | `ActsAsTenant`, `current_tenant` | `tenant_id` |

### Step 2: Discover All Data Access Points

Scan for every location that queries the database:

**Django patterns to find:**
```python
# ViewSet querysets (HIGHEST PRIORITY — these are API-exposed)
grep -rn "def get_queryset" --include="*.py"
grep -rn "\.objects\." --include="*.py"

# Direct model access in services
grep -rn "Model\.objects\.(all|filter|get|exclude|annotate)" --include="*.py"

# Raw SQL (rare but dangerous)
grep -rn "raw\(|cursor\(\)" --include="*.py"

# Serializer querysets (nested serializers can leak)
grep -rn "queryset\s*=" --include="*.py" | grep -i serializer
```

**FastAPI patterns:**
```python
grep -rn "session\.(query|execute|scalars)" --include="*.py"
grep -rn "select\(Model\)" --include="*.py"
```

**Rails patterns:**
```ruby
grep -rn "\.all\|\.where\|\.find" --include="*.rb"
```

### Step 3: Classify Each Access Point

For each discovered query, classify it:

```
CLASSIFICATION RULES
====================

✅ SAFE — Query filters by tenant field:
    Model.objects.filter(operation=request.user.current_operation)
    session.query(Model).filter(Model.org_id == ctx.org_id)

✅ EXEMPT — Model is tenant-agnostic:
    User.objects.get(id=user_id)           ← Users span tenants
    SiteContent.objects.first()            ← Singleton, public data
    CMEPrice.objects.filter(...)           ← Shared market data

⚠️ INDIRECT — Filters via FK chain (verify chain is tenant-safe):
    FeedEvent.objects.filter(lot__operation=op)   ← Safe IF lot.operation is guaranteed
    TreatmentEventDrug.objects.filter(
        treatment_event__operation=op              ← Safe IF FK enforces tenant
    )

❌ MISSING — No tenant filter found:
    Model.objects.all()
    Model.objects.filter(status='active')  ← Filters exist but not tenant

❌ BYPASS — Intentionally skips tenant filter (needs justification):
    Model.all_objects.filter(...)          ← Soft-delete bypass — is tenant filter present?
    Model.objects.using('admin_db')        ← Cross-tenant admin query
```

### Step 4: Audit Indirect Filters

For `⚠️ INDIRECT` classifications, trace the FK chain:

```
FeedEvent.objects.filter(lot__operation=op)
    │
    ├── FeedEvent.lot → FK to Lot (CASCADE)
    ├── Lot.operation → FK to Operation (CASCADE)
    └── ✅ Chain is tenant-safe: every intermediate FK enforces tenant
```

```
InvoiceLineItem.objects.filter(invoice__customers__operation=op)
    │
    ├── InvoiceLineItem.invoice → FK to Invoice
    ├── Invoice.customers → M2M to Customer
    ├── Customer.operation → FK to Operation
    └── ⚠️ M2M traversal: verify no cross-tenant customers in M2M
```

### Step 5: Generate Scan Report

```
MULTI-TENANT ISOLATION SCAN
============================
Project: cattle-management
Tenant field: operation (via OperationContextMiddleware)
Files scanned: 47
Queries found: 189

RESULTS BY STATUS:
  ✅ Safe:      142 (75.1%)
  ✅ Exempt:     23 (12.2%)
  ⚠️ Indirect:   18 (9.5%)
  ❌ Missing:     4 (2.1%)
  ❌ Bypass:      2 (1.1%)

MISSING TENANT FILTERS (CRITICAL):
  File                          Line  Query
  ─────────────────────────────────────────────────────────
  reports/analytics_views.py    45    Lot.objects.filter(status='active')
  feeds/services.py             312   FeedLoad.objects.filter(is_depleted=False)
  health/tasks.py               78    ScheduledTreatment.objects.filter(due_date__lte=today)
  inventory/signals.py          23    Ration.objects.filter(ingredients__feed_commodity=commodity)

BYPASS (NEEDS JUSTIFICATION):
  File                          Line  Query                              Justification
  ──────────────────────────────────────────────────────────────────────────────────
  lots/views.py                 89    Lot.all_objects.filter(...)         Soft-delete admin view — HAS tenant filter ✅
  risk/tasks.py                 45    CMEPrice.objects.all()              Shared market data — no tenant needed ✅

INDIRECT FILTERS (VERIFY FK CHAIN):
  18 queries use FK traversal — all chains verified tenant-safe ✅
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| Tenant field | `operation` | The field name used for tenant isolation |
| Context accessor | `request.user.current_operation` | How tenant context is accessed |
| Exempt models | `User, SiteContent, CMEPrice` | Models that don't need tenant filters |
| Exempt paths | `/admin/, /health/` | URL paths that skip tenant checks |
| File patterns | `*.py` | Files to scan |
| Exclude dirs | `migrations/, tests/, management/` | Directories to skip |

## Framework-Specific Patterns

### Django — ViewSet Pattern
```python
# REQUIRED in every ModelViewSet
def get_queryset(self):
    return Model.objects.filter(
        operation=self.request.user.current_operation
    )
```

### Django — Service Pattern
```python
# Services should receive operation as parameter
def calculate_cost(lot, operation):
    expenses = MiscExpense.objects.filter(lot=lot, lot__operation=operation)
```

### FastAPI — Dependency Pattern
```python
async def get_items(
    tenant: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
):
    return await session.scalars(
        select(Item).where(Item.org_id == tenant.org_id)
    )
```

### Rails — ActsAsTenant Pattern
```ruby
class ApplicationController < ActionController::Base
  set_current_tenant_through_filter
  before_action :set_tenant

  def set_tenant
    set_current_tenant(current_user.organization)
  end
end
```

## Key Principles

1. **Default deny** — assume every query is unsafe until proven safe
2. **Scan services too** — ViewSets get attention, but services and tasks often skip tenant filters
3. **Celery/background tasks are high-risk** — they don't have request context, so tenant must be passed explicitly
4. **Signals cross boundaries** — a signal handler in module B triggered by module A may not have tenant context
5. **Admin views need tenant filters too** — unless explicitly designed for cross-tenant admin access
6. **Test with 2 tenants** — create test data for 2 tenants, query as tenant 1, assert tenant 2's data is absent
