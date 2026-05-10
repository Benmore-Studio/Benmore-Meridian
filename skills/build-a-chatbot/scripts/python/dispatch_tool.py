# pyright: reportMissingImports=false
# Note: This is a SCAFFOLD. The relative imports below won't resolve until
# you copy this file into your project's `chat_tools/__init__.py` (or
# equivalent) and create the sibling domain modules.
"""
dispatch_tool.py — Centralized tool dispatch with feature gating.

This is the SINGLE entry point through which every tool call passes. It does
three things:

1. Resolves the tool name to a handler.
2. Enforces feature gating (Pro-only, role-based) BEFORE the handler runs.
3. Calls the handler with (user, args).

Why centralized: the LLM sees the full tool catalog every request. Feature
gating must happen server-side at dispatch — never by hiding tools from the
model (the model's behavior is more predictable when the catalog is
stable).

Place this in `chat_tools/__init__.py` of your project.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict, Union

# Replace these imports with your domain modules.
from .customer_tools import HANDLERS as _CUSTOMER
from .quote_tools    import HANDLERS as _QUOTE
from .invoice_tools  import HANDLERS as _INVOICE
# from .order_tools    import HANDLERS as _ORDER
# ...

# Combined handler registry. Keys are tool names (must match schema names).
ALL_HANDLERS: dict[str, Any] = {
    **_CUSTOMER,
    **_QUOTE,
    **_INVOICE,
    # **_ORDER,
}


# ─── Feature gating ─────────────────────────────────────────────────────────

# Tools that require a paid tier. Read-only counterparts (e.g.
# `search_invoices`, `get_invoice_details`) typically stay free.
PRO_ONLY_TOOLS: frozenset[str] = frozenset({
    "create_invoice",
    "send_invoice",
    "create_payment_link",
    "mark_invoice_paid",
    # add your own write tools here
})


# Tools that require a specific role beyond `user`. Example: admin-only tools.
ADMIN_ONLY_TOOLS: frozenset[str] = frozenset({
    # "delete_user",
    # "export_all_data",
})


# ─── Type definitions ──────────────────────────────────────────────────────

class ProDenied(TypedDict):
    error: Literal["requires_pro"]
    feature: str
    message: str


class AdminDenied(TypedDict):
    error: Literal["requires_admin"]
    feature: str
    message: str


class UnknownTool(TypedDict):
    error: str   # always "Unknown tool: ..."


ToolResult = Union[ProDenied, AdminDenied, UnknownTool, dict, list]


# ─── Helpers ───────────────────────────────────────────────────────────────

def _friendly_feature(tool_name: str) -> str:
    """Convert tool_name into a human-readable feature label.

    `create_invoice` → `create invoice`
    """
    return tool_name.replace("_", " ")


# ─── The dispatcher ────────────────────────────────────────────────────────

def dispatch_tool(user, name: str, args: dict | None = None) -> ToolResult:
    """Run a tool handler with permission gates.

    Returns the handler's result on success. On gate denial, returns a
    structured error envelope that the chat layer can translate into a
    friendly upsell or denial message.

    The handler signature is `(user, args: dict) -> dict | list`.
    """
    handler = ALL_HANDLERS.get(name)
    if handler is None:
        return {"error": f"Unknown tool: {name}"}

    role = (getattr(user, "role", "") or "free").lower()

    # Pro gate (free users blocked from Pro tools)
    if name in PRO_ONLY_TOOLS and role == "free":
        feature = _friendly_feature(name)
        return ProDenied(
            error="requires_pro",
            feature=feature,
            message=f"{feature.capitalize()} is a Pro feature. Upgrade to unlock it.",
        )

    # Admin gate
    if name in ADMIN_ONLY_TOOLS and role != "admin":
        feature = _friendly_feature(name)
        return AdminDenied(
            error="requires_admin",
            feature=feature,
            message=f"{feature.capitalize()} requires admin access.",
        )

    # Auditor / read-only gate (uncomment if you have this role)
    # if role == "auditor" and name not in READ_ONLY_TOOLS:
    #     return {"error": "auditor_read_only", "message": "Auditors have read-only access."}

    return handler(user, args or {})


__all__ = [
    "ALL_HANDLERS",
    "PRO_ONLY_TOOLS",
    "ADMIN_ONLY_TOOLS",
    "ToolResult",
    "ProDenied",
    "AdminDenied",
    "dispatch_tool",
]
