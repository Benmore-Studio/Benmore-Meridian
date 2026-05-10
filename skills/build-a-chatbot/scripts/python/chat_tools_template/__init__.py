# pyright: reportMissingImports=false
# Note: This is a SCAFFOLD. Sibling-module imports won't resolve until the
# folder is renamed `chat_tools/` and dropped into your project alongside
# the matching domain modules.
"""
chat_tools/__init__.py — Tool registry + dispatch.

This is the file that aggregates all domain tool modules and exposes:
  - ALL_TOOLS:     the schema list sent to the LLM
  - ALL_HANDLERS:  name → handler-function map
  - dispatch_tool: the single entry point with feature gating
  - PRO_ONLY_TOOLS: gating set

Adapt the imports for your project. Add new domain modules here.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict, Union

from .definitions   import ALL_TOOLS
from .example_tools import HANDLERS as _EXAMPLE
# from .quote_tools    import HANDLERS as _QUOTE
# from .invoice_tools  import HANDLERS as _INVOICE
# ... add your domain modules


# Combined handler registry. Keys are tool names; must match schemas.
ALL_HANDLERS: dict[str, Any] = {
    **_EXAMPLE,
    # **_QUOTE,
    # **_INVOICE,
}


# ─── Feature gating ─────────────────────────────────────────────────────────

PRO_ONLY_TOOLS: frozenset[str] = frozenset({
    # Add tool names that require a paid subscription.
    # "create_invoice",
    # "send_invoice",
})


# ─── Types ─────────────────────────────────────────────────────────────────

class ProDenied(TypedDict):
    error: Literal["requires_pro"]
    feature: str
    message: str


ToolResult = Union[ProDenied, dict, list]


def _friendly_feature(tool_name: str) -> str:
    return tool_name.replace("_", " ")


# ─── Dispatch ───────────────────────────────────────────────────────────────

def dispatch_tool(user, name: str, args: dict | None = None) -> ToolResult:
    """Run a tool handler with permission gates.

    See dispatch_tool.py for the canonical, fully-typed implementation
    (including admin and auditor gates). This is the minimum-viable version
    for a starter chatbot.
    """
    handler = ALL_HANDLERS.get(name)
    if handler is None:
        return {"error": f"Unknown tool: {name}"}

    role = (getattr(user, "role", "") or "free").lower()
    if name in PRO_ONLY_TOOLS and role == "free":
        feature = _friendly_feature(name)
        return ProDenied(
            error="requires_pro",
            feature=feature,
            message=f"{feature.capitalize()} is a Pro feature. Upgrade to unlock it.",
        )

    return handler(user, args or {})


__all__ = [
    "ALL_TOOLS",
    "ALL_HANDLERS",
    "PRO_ONLY_TOOLS",
    "ToolResult",
    "ProDenied",
    "dispatch_tool",
]
