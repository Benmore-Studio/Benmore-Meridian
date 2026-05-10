"""
chat_tools/definitions.py — OpenAI function-calling schemas.

Each tool gets a `_tool(...)` entry. Group by domain, then aggregate into
`ALL_TOOLS`. The shape:

    {
        "type": "function",
        "function": {
            "name":        "tool_name",
            "description": "When to call this tool.",
            "parameters": {
                "type": "object",
                "properties": {...},
                "required":   ["..."]
            }
        }
    }

Tips for descriptions:
  - Tool description: explain WHEN to call it, not WHAT it does. The
    model already infers what from the name.
  - Parameter description: include format hints (E.164, ISO date, range).
"""

from __future__ import annotations


def _tool(
    name: str,
    description: str,
    properties: dict,
    required: list[str] | None = None,
) -> dict:
    """Build an OpenAI function-calling tool schema."""
    params: dict = {"type": "object", "properties": properties}
    if required:
        params["required"] = required
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": params,
        },
    }


# ─── Example domain: customers ─────────────────────────────────────────────

EXAMPLE_TOOLS = [
    _tool(
        name="create_customer",
        description="Use when the user wants to add a new customer record. Gathers basic contact info; only `name` is required.",
        properties={
            "name":         {"type": "string", "description": "Full name."},
            "email":        {"type": "string", "description": "Email address. Optional."},
            "phone":        {"type": "string", "description": "Phone (E.164 format). Optional."},
            "company_name": {"type": "string", "description": "Company. Optional."},
        },
        required=["name"],
    ),
    _tool(
        name="search_customers",
        description="Use when the user wants to find customers by name, email, or company. Returns up to 5 matches.",
        properties={
            "query": {"type": "string", "description": "Search string. Matches name, email, or company."},
        },
        required=["query"],
    ),
    _tool(
        name="get_customer_stats",
        description="Use when the user asks how many quotes/invoices/revenue a customer has.",
        properties={
            "customer_name": {"type": "string", "description": "Customer name (fuzzy-matched)."},
        },
        required=["customer_name"],
    ),
]


# ─── Aggregation ───────────────────────────────────────────────────────────

ALL_TOOLS: list[dict] = [
    *EXAMPLE_TOOLS,
    # *QUOTE_TOOLS,
    # *INVOICE_TOOLS,
    # ...
]
