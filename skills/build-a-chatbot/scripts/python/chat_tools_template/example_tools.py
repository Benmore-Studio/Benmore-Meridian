"""
chat_tools/example_tools.py — Example domain handler module.

This is a starter showing the canonical handler shape. Copy + rename for
your real domains (customer_tools.py, order_tools.py, etc.).

Convention every handler must follow:
  - Signature:  (user, args: dict) -> dict | list
  - Tenant-scope every query by user.organization (or your tenant key).
  - Return envelope:
      success (write):  {"id": "...", "name": "...", "created": True}
      success (read):   {...domain fields...} or [...]
      not found:        {"error": "Customer 'X' not found."}
      bad arg:          {"error": "Invalid status '...'. Valid: ..."}
  - Stringify Decimals/UUIDs/datetimes before returning.
  - Don't catch programming errors (AttributeError, KeyError) — they
    should propagate to your error tracker.
"""

from __future__ import annotations

from typing import Any


# ─── Handlers ──────────────────────────────────────────────────────────────

def create_customer(user, args: dict) -> dict:  # noqa: ARG001 — `user` used after stub is replaced
    """Create a customer scoped to user.organization."""
    # Replace with your model:
    # from myapp.customers.models import Customer

    name = (args.get("name") or "").strip()
    if not name:
        return {"error": "name is required."}

    phone = args.get("phone", "")
    if phone:
        try:
            phone = _normalize_phone(phone)
        except ValueError as exc:
            return {"error": f"Invalid phone: {exc}"}

    # customer = Customer.objects.create(
    #     organization=user.organization,
    #     created_by=user,
    #     name=name,
    #     email=args.get("email", ""),
    #     phone=phone,
    #     company_name=args.get("company_name", ""),
    # )
    customer_id = "stub-id-replace-me"

    return {
        "id":      customer_id,
        "name":    name,
        "created": True,
    }


def search_customers(user, args: dict) -> list[dict]:  # noqa: ARG001
    """Search by name/email/company across user's organization. Top 5."""
    query = args.get("query", "")
    if not query:
        return []

    # qs = Customer.objects.filter(
    #     organization=user.organization
    # ).filter(
    #     Q(name__icontains=query)
    #     | Q(company_name__icontains=query)
    #     | Q(email__icontains=query),
    # )[:5]
    # return [
    #     {"id": str(c.id), "name": c.name, "email": c.email, "company": c.company_name}
    #     for c in qs
    # ]
    return [
        {"id": "stub", "name": f"(stub match for '{query}')", "email": "", "company": ""}
    ]


def get_customer_stats(user, args: dict) -> dict:  # noqa: ARG001
    """Aggregate stats for a single customer (quotes, revenue, etc.)."""
    name = (args.get("customer_name") or "").strip()
    if not name:
        return {"error": "customer_name is required."}

    # customer = match_customer(user.organization, name)
    # if not customer:
    #     return {"error": f"No customer found matching '{name}'."}
    # quotes = customer.quotes.all()
    # ...

    return {
        "name":          name,
        "total_quotes":  0,
        "total_revenue": "0.00",
        "draft":         0,
        "sent":          0,
        "accepted":      0,
        "rejected":      0,
    }


# ─── Helpers ───────────────────────────────────────────────────────────────

def _normalize_phone(raw: str) -> str:
    """Replace with your real E.164 normalizer."""
    digits = "".join(c for c in raw if c.isdigit() or c == "+")
    if not digits:
        raise ValueError("phone is empty after normalization")
    return digits


# ─── Registry ──────────────────────────────────────────────────────────────

HANDLERS: dict[str, Any] = {
    "create_customer":    create_customer,
    "search_customers":   search_customers,
    "get_customer_stats": get_customer_stats,
}
