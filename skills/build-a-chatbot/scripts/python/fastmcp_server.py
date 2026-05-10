"""
fastmcp_server.py — Minimal FastMCP server template.

Run with `python fastmcp_server.py`. By default uses stdio (suitable for
Claude Desktop / Claude Code). For remote use, switch the `transport`
argument at the bottom.

Pip install: `pip install mcp`

This template shows:
  - A tool (`lookup_price`) — POST-shaped, side-effecting.
  - A resource (`pricing://catalog`) — GET-shaped, addressable data.
  - A prompt (`weekly_report`) — server-supplied template.

`@mcp.tool()` auto-generates the JSON schema from your type hints and
docstring. Keep parameter docstrings tight and informative — the LLM reads
them.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-pricing-server")


# ─── Tools (LLM can call these) ────────────────────────────────────────────

@mcp.tool()
def lookup_price(item_name: str, province: str = "ON") -> dict:
    """Look up a Home Depot Canada price for a construction material.

    Args:
        item_name: Material name, e.g. "2x4 SPF 8ft".
        province: Two-letter province code (default: ON).

    Returns:
        {"item": str, "province": str, "price_cad": float}
    """
    # Replace with your real lookup (DB query, API call, etc.).
    return {
        "item": item_name,
        "province": province,
        "price_cad": 4.97,
    }


@mcp.tool()
def list_categories() -> list[str]:
    """List all material categories in the pricing library."""
    return ["lumber", "concrete", "insulation", "roofing", "drywall"]


# ─── Resources (LLM/host can read these) ───────────────────────────────────

@mcp.resource("pricing://catalog")
def catalog() -> str:
    """The full pricing catalog as CSV.

    Hosts can render this in a UI or inline it into the next LLM message.
    """
    return "name,unit,price_cad\n2x4 SPF 8ft,each,4.97\nDrywall 4x8 1/2in,sheet,12.50\n"


# ─── Prompts (host can render these as slash-commands) ─────────────────────

@mcp.prompt()
def weekly_report(focus_area: str = "all") -> str:
    """Generate a weekly pricing report prompt the user can run."""
    return (
        f"Summarize price changes in the {focus_area} category over the "
        f"last 7 days. Include: items with > 5% movement, mean change, "
        f"top 3 surprises."
    )


# ─── Run ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Local subprocess (default — used by Claude Desktop / Claude Code).
    mcp.run()

    # Remote HTTP server (uncomment when deploying behind a load balancer):
    # mcp.run(transport="streamable-http", host="0.0.0.0", port=8765)
