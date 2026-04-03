---
name: service-invariant-guard
description: Scans for direct mutations of aggregate or computed fields that should only be modified through a centralized service. Catches bypasses of HeadCountService, BalanceService, InventoryService, or any domain service that owns a critical invariant. Configurable for any domain.
context: fork
---

# Service Invariant Guard

Detect code that directly mutates fields which should only be modified through a designated service. Prevents invariant violations where aggregate counts, computed balances, or state machines drift out of sync.

## When to Use
- After adding code that could modify a guarded field
- Before PRs that touch models with service-managed fields
- During code review of new contributors
- Periodically as a codebase hygiene check
- After refactoring service boundaries

## The Problem

Many systems have fields that LOOK like simple model attributes but are actually **service-managed invariants**:

```python
# DANGEROUS — bypasses the service that keeps counts in sync
lot.current_head_count -= 1
lot.save()

# SAFE — uses the service that updates counts, assignments, and audit trail
HeadCountService.record_mortality(lot, pen, head_count=1, user=request.user)
```

When code bypasses the service:
- Related records don't update (e.g., LotPenAssignment, HospitalPenOccupant)
- Audit trail is incomplete
- Computed properties diverge from stored values
- Business rules are skipped (e.g., lot closure check, notification dispatch)

## Workflow

### Step 1: Define Invariants

Read project documentation or configure the invariant registry:

```
INVARIANT REGISTRY
==================
┌─────────────────────────────────┬─────────────────────────┬──────────────────────────────┐
│ Guarded Field                    │ Owning Service           │ Allowed Mutation Points       │
├─────────────────────────────────┼─────────────────────────┼──────────────────────────────┤
│ Lot.current_head_count           │ HeadCountService         │ process_cattle_inbound,       │
│                                  │                          │ process_cattle_outbound,      │
│                                  │                          │ record_mortality,             │
│                                  │                          │ transfer_between_lots         │
│                                  │                          │                              │
│ Pen.current_head_count           │ (computed property)      │ NEVER — it's a @property      │
│                                  │                          │                              │
│ FeedLoad.remaining_tons          │ FeedInventoryDeduction   │ deduct_for_event,             │
│                                  │  Service                 │ reverse_deduction             │
│                                  │                          │                              │
│ PharmaBatch.remaining_quantity   │ PharmaceuticalInventory  │ deduct_for_treatment,         │
│                                  │  DeductionService        │ reverse_deduction             │
│                                  │                          │                              │
│ Lot.status                       │ HeadCountService         │ _try_close_lot (via signal)   │
│                                  │                          │                              │
│ BillingUsage.peak_head_count     │ BillingUsage signal      │ post_save on Lot              │
└─────────────────────────────────┴─────────────────────────┴──────────────────────────────┘
```

### Step 2: Build Search Patterns

For each guarded field, construct grep patterns that detect direct mutation:

```python
# Pattern: Direct attribute assignment
f"{model_name_lower}.{field_name}\s*[+\-\*]?="
# Matches: lot.current_head_count = 50
#          lot.current_head_count -= 1
#          lot.current_head_count += head_count

# Pattern: update() calls
f"\.update\(.*{field_name}\s*="
# Matches: Lot.objects.filter(...).update(current_head_count=F('current_head_count') - 1)

# Pattern: save() with update_fields containing the field
f"save\(.*update_fields.*{field_name}"
# Matches: lot.save(update_fields=['current_head_count'])

# Pattern: bulk_update with the field
f"bulk_update\(.*\[.*'{field_name}'"
# Matches: Lot.objects.bulk_update(lots, ['current_head_count'])

# Pattern: F() expressions on the field
f"F\('{field_name}'\)"
# Matches: Lot.objects.update(current_head_count=F('current_head_count') - 1)
```

### Step 3: Scan and Classify

For each match found:

```
CLASSIFICATION
==============

✅ AUTHORIZED — Match is inside the owning service:
    lots/services.py:HeadCountService.process_cattle_inbound()
        lot.current_head_count += head_count  ← This IS the service

✅ MIGRATION — Match is in a data migration:
    lots/migrations/0058_restore_hospital_head_counts.py
        lot.current_head_count += occupant_count  ← One-time data fix, acceptable

⚠️ LEGACY — Match predates the service (may need refactoring):
    health/models.py:MortalityEvent.save()
        lot.current_head_count -= 1  ← Direct update, legacy pattern
    DOCUMENTED: "legacy pattern" in lots/CLAUDE.md

❌ VIOLATION — Match is outside the service with no justification:
    sorts/views.py:145
        source_lot.current_head_count -= transfer.head_count
    SHOULD BE: HeadCountService.transfer_between_lots(...)

❌ COMPUTED PROPERTY WRITE — Attempting to write to a computed field:
    health/views.py:89
        pen.current_head_count = new_count
    INVALID: Pen.current_head_count is a @property (read-only)
```

### Step 4: Check for Missing Service Calls

Beyond direct mutations, check that the service is actually being called where it should be:

```
MISSING SERVICE CALLS
=====================
Scan for operations that SHOULD use the service but don't call it:

1. Cattle arrival without HeadCountService:
   grep -rn "CattleInbound.*create\|CattleInbound.*save" --include="*.py"
   → Verify each is followed by HeadCountService.process_cattle_inbound()

2. Mortality without HeadCountService:
   grep -rn "MortalityEvent.*create\|MortalityEvent.*save" --include="*.py"
   → Verify each calls HeadCountService.record_mortality()

3. Inventory deduction without service:
   grep -rn "remaining_tons.*-=\|remaining_quantity.*-=" --include="*.py"
   → Should use FeedInventoryDeductionService or PharmaceuticalInventoryDeductionService
```

### Step 5: Generate Guard Report

```
SERVICE INVARIANT GUARD REPORT
===============================
Invariants checked: 6
Files scanned: 85
Mutations found: 34

  Guarded Field                  Authorized  Legacy  Violation  Computed Write
  ──────────────────────────────────────────────────────────────────────────────
  Lot.current_head_count         12          1       2          0
  FeedLoad.remaining_tons        8           0       0          0
  PharmaBatch.remaining_quantity 6           0       1          0
  Lot.status                     3           0       0          0
  Pen.current_head_count         0           0       0          1
  BillingUsage.peak_head_count   1           0       0          0

VIOLATIONS (ACTION REQUIRED):
  #1  sorts/views.py:145
      source_lot.current_head_count -= transfer.head_count
      FIX: Replace with HeadCountService.transfer_between_lots()

  #2  sorts/views.py:148
      dest_lot.current_head_count += transfer.head_count
      FIX: Same — HeadCountService handles both sides

  #3  processing/services.py:89
      batch.remaining_quantity -= quantity
      FIX: Use PharmaceuticalInventoryDeductionService.deduct()

COMPUTED PROPERTY WRITES:
  #1  health/views.py:89
      pen.current_head_count = new_count
      FIX: This is a @property — mutation is silently ignored. Remove the line.

LEGACY (TRACK FOR FUTURE REFACTOR):
  #1  health/models.py:MortalityEvent.save()
      lot.current_head_count -= 1
      NOTE: Documented as legacy in lots/CLAUDE.md. Refactor to HeadCountService.record_mortality()
```

## Configuration

```yaml
# .service-invariant-guard.yml (or configure inline)
invariants:
  - model: Lot
    field: current_head_count
    service: HeadCountService
    service_file: lots/services.py
    allowed_files:
      - lots/services.py
      - lots/migrations/*

  - model: FeedLoad
    field: remaining_tons
    service: FeedInventoryDeductionService
    service_file: inventory/services.py
    allowed_files:
      - inventory/services.py
      - inventory/migrations/*

  - model: PharmaBatch
    field: remaining_quantity
    service: PharmaceuticalInventoryDeductionService
    service_file: inventory/services.py
    allowed_files:
      - inventory/services.py
      - inventory/migrations/*

  - model: Pen
    field: current_head_count
    type: computed_property  # NEVER writable
    
exclude_dirs:
  - tests/
  - migrations/  # Optional: include to catch migration issues
```

## Framework Adaptations

### Django
```python
# Guarded fields are often on Model classes
# Services are typically in <app>/services.py
# Computed properties use @property decorator
# Signals can bypass services — check signals.py files
```

### FastAPI + SQLAlchemy
```python
# Guarded fields are on SQLAlchemy models
# Services are in <module>/service.py
# Computed properties use @hybrid_property
# Event listeners can bypass services
```

### Rails
```ruby
# Guarded fields are ActiveRecord attributes
# Services are in app/services/
# Computed properties use def field_name; end
# Callbacks (before_save, after_create) can bypass services
```

## Key Principles

1. **The service IS the invariant** — if code bypasses the service, the invariant is broken
2. **Migrations are special** — data migrations may need direct access for one-time fixes
3. **Tests are exempt** — test setup code can set fields directly for test isolation
4. **Legacy code is tracked** — don't ignore it, document it for future refactoring
5. **Computed properties are NEVER writable** — writing to a @property is a silent no-op bug
6. **Signals are sneaky** — a post_save signal might directly mutate a guarded field in another model
