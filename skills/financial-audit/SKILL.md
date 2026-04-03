---
name: financial-audit
description: Reads documented financial formulas from module docs (CLAUDE.md), compares against actual code implementation, flags mismatches, and runs related tests. Use when auditing financial calculations, after changing pricing/billing logic, or before releases.
context: fork
---

# Financial Formula Audit

Systematically verify that documented financial formulas match their code implementations. Catches formula drift — when code evolves but docs (or vice versa) don't keep up.

## When to Use
- After modifying any financial calculation (pricing, billing, cost allocation, P&L, breakeven)
- Before a release that touches financial modules
- When a stakeholder reports "the numbers don't match"
- After updating formula documentation in CLAUDE.md
- During periodic audits of financial accuracy

## Prerequisites
- Module documentation (CLAUDE.md or equivalent) containing financial formulas
- Formulas documented with variable names that map to code variables
- Test suite covering financial calculations

## Workflow

### Step 1: Discover Documented Formulas

Scan module documentation for formula patterns:

```
Search patterns:
  - Code blocks containing: =, ×, ÷, +, -, Σ, /, *
  - Headers containing: "calculation", "formula", "pricing", "cost", "P&L", "breakeven"
  - ASCII flow diagrams with arithmetic operations
  - Named equations (e.g., "COG/lb = ...")
```

For each formula found, extract:
```
┌──────────────────────────────────────────────────────┐
│ Formula Record                                        │
├──────────────────────────────────────────────────────┤
│ Name:        Cost of Gain per lb                      │
│ Location:    lots/CLAUDE.md line 142                   │
│ Formula:     COG/lb = (Feed + Treatment + Processing  │
│              + Interest + Death Loss + Yardage + Misc) │
│              / Total Lbs Gained                        │
│ Variables:   Feed, Treatment, Processing, Interest,    │
│              Death_Loss, Yardage, Misc, Total_Lbs_Gain│
│ Code file:   lots/cost_of_gain_service.py (expected)   │
└──────────────────────────────────────────────────────┘
```

### Step 2: Locate Code Implementation

For each documented formula:

1. **Find the code file** — use the documented file path, or grep for function/variable names
2. **Read the implementation** — find the actual arithmetic
3. **Map variables** — match doc variable names to code variable names

```
VARIABLE MAPPING
================
Doc Variable        →  Code Variable              →  Source
───────────────────────────────────────────────────────────
Feed                →  feed_cost                   →  _get_feed_cost()
Treatment           →  treatment_cost              →  _get_treatment_cost()
Death Loss          →  death_loss                  →  mortality_count × purchase_price_per_head
Total Lbs Gained    →  total_gain                  →  sold_gain + remaining_gain
Interest            →  interest_expense            →  total_cost × rate / 365 × DOF
```

### Step 3: Compare Formula vs Code

For each formula, check:

```
CHECK 1: COMPONENTS MATCH
  Doc says:  COG = (A + B + C + D + E + F + G) / H
  Code does: COG = (A + B + C + D + E + F + G) / H
  Result: ✅ MATCH

CHECK 2: OPERATOR CORRECTNESS
  Doc says:  Interest = principal × rate / 365 × DOF
  Code does: Interest = principal * rate / 365 * DOF
  Result: ✅ MATCH

CHECK 3: EDGE CASES HANDLED
  Doc says:  "Default $0.85/lb when total_gain ≤ 0"
  Code does: if total_gain <= 0: return Decimal("0.85")
  Result: ✅ MATCH

CHECK 4: VARIABLE SOURCES
  Doc says:  "purchase_price_per_head from PurchaseGroup"
  Code does: lot.computed_purchase_price_per_cwt (3-tier fallback)
  Result: ⚠️ DRIFT — doc doesn't mention fallback chain
```

### Step 4: Run Financial Tests

```bash
# Find tests related to each formula
grep -rl "cost_of_gain\|breakeven\|interest\|profit_loss" tests/ --include="*.py"

# Run them
python manage.py test <discovered_test_modules> -v 2
```

### Step 5: Generate Audit Report

```
FINANCIAL FORMULA AUDIT REPORT
===============================
Date: 2026-04-02
Modules audited: 5
Formulas checked: 12

  #  Formula                    Doc Location         Code Location                 Status
  ── ────────────────────────── ──────────────────── ───────────────────────────── ──────
  1  COG per lb                 lots/CLAUDE.md:142   cost_of_gain_service.py:245   ✅ MATCH
  2  Interest (flat formula)    lots/CLAUDE.md:180   interest_service.py:89        ✅ MATCH
  3  Breakeven per cwt          reports/CLAUDE.md:95 closeout_views.py:312         ✅ MATCH
  4  Proportional P&L           reports/CLAUDE.md:120 closeout_views.py:350        ✅ MATCH
  5  ACT CONV death-DM          reports/CLAUDE.md:145 closeout_views.py:280        ⚠️ DRIFT
  6  Head days calculation      invoices/CLAUDE.md:88 head_days_service.py:45      ✅ MATCH
  7  FIFO feed cost             inventory/CLAUDE.md:67 services.py:120             ✅ MATCH
  8  Retail markup              inventory/CLAUDE.md:92 models.py:158               ✅ MATCH
  9  Three-iteration breakeven  lots/CLAUDE.md:210   interest_service.py:145       ✅ MATCH
  10 Yardage allocation         allocations/CLAUDE.md:55 services.py:78            ❌ MISMATCH
  11 Per-head-day billing       subscriptions/CLAUDE.md:100 tasks.py:67            ✅ MATCH
  12 Feed DM calculation        feeds/CLAUDE.md:75   models.py:250                 ✅ MATCH

ISSUES:
  #5 ACT CONV: Doc says 4 locations must stay in sync. Location 3 (summary helper)
     uses `total_dm_consumed / total_animal_days` but location 4 (serializer)
     uses `total_dm_consumed / (head_in × DOF)` — old formula.

  #10 Yardage: Doc says "arrival-inclusive, departure-exclusive" but code uses
      `date__gte=start, date__lt=end` which is start-inclusive, end-exclusive
      relative to the DATE RANGE, not the lot lifecycle.

TESTS: 45 passed, 0 failed, 3 skipped (Redis)
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| Doc file name | `CLAUDE.md` | Module documentation file to scan |
| Formula markers | `=`, `×`, `÷`, `Σ` | Characters that indicate a formula |
| Section headers | `Calculation`, `Formula`, `Pricing` | Headers to search under |
| Test command | `python manage.py test` | Test runner command |
| Severity levels | MATCH, DRIFT, MISMATCH | Categorization thresholds |

## Severity Definitions

| Level | Meaning | Action |
|-------|---------|--------|
| **MATCH** | Doc and code agree on formula, operators, and edge cases | None |
| **DRIFT** | Doc and code produce same result but differ in description (e.g., missing fallback chain) | Update docs |
| **MISMATCH** | Doc and code produce different results for the same inputs | Fix code or docs — determine which is authoritative |

## Key Principles

1. **Docs and code are both suspects** — a mismatch means one is wrong, not necessarily the code
2. **Test with concrete numbers** — abstract formula comparison misses order-of-operations bugs
3. **Check edge cases explicitly** — zero, negative, null, division-by-zero guards
4. **Track multi-location formulas** — if the same formula exists in N places, verify all N match
5. **Decimal precision matters** — `float` vs `Decimal`, rounding rules, `toFixed(2)` patterns
