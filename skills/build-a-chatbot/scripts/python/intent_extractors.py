"""
intent_extractors.py — Regex-based fast-path argument extraction.

Each extractor parses the user's message and returns:
  - dict        — args extracted successfully
  - {}          — no args needed (e.g. get_dashboard_summary)
  - None        — couldn't extract; fall back to LLM

Combined with intent_matcher, lets common requests skip the LLM entirely:

    args = INTENT_EXTRACTORS[intent.name](message)
    args = apply_context(intent.name, args, message, context)
    if args is not None and intent.name in ALL_HANDLERS:
        result = dispatch_tool(user, intent.name, args)   # FAST PATH ✓
    else:
        result = chat_service.process_message(message)    # SLOW PATH (LLM)
"""

from __future__ import annotations

import re
from typing import Callable

# ─── Common patterns ──────────────────────────────────────────────────────

_QUOTE_NUMBER  = re.compile(r"\b(Q-\d{6}-\d{4,})\b", re.IGNORECASE)
_INVOICE_NUMBER = re.compile(r"\b(INV-\d{6}-\d{4,})\b", re.IGNORECASE)
_REFERENTIAL    = re.compile(r"\b(this|that|these|those|it|current)\b", re.IGNORECASE)


def _no_args(_message: str) -> dict:  # noqa: ARG001 — _message kept for uniform signature
    return {}


# ─── Per-intent extractors ────────────────────────────────────────────────

def _extract_quote_number(message: str) -> dict | None:
    m = _QUOTE_NUMBER.search(message)
    return {"quote_number": m.group(1).upper()} if m else None


def _extract_invoice_number(message: str) -> dict | None:
    m = _INVOICE_NUMBER.search(message)
    return {"invoice_number": m.group(1).upper()} if m else None


def _extract_followups(message: str) -> dict:
    m = re.search(r"(?:next|in|in the next)\s+(\d+)\s+days?", message, re.I)
    return {"days_ahead": int(m.group(1))} if m else {}  # default to 7


def _extract_search_customers(message: str) -> dict | None:
    # "find customer named X" / "search for X" / "look up X"
    patterns = [
        r"(?:find|search\s+for|look\s*up)\s+(?:customer|client)?\s*(?:named|called)?\s*[\"']?([A-Za-z][\w\s&.-]{1,40})[\"']?",
        r"do\s+we\s+have\s+(?:a\s+)?(?:customer|client)\s+(?:named|called)\s+([A-Za-z][\w\s&.-]{1,40})",
    ]
    for p in patterns:
        m = re.search(p, message, re.I)
        if m:
            return {"query": m.group(1).strip().rstrip(".!?,")}
    return None


def _extract_create_invoice(message: str) -> dict | None:
    # "create invoice from quote Q-..." / "convert Q-... to invoice"
    m = _QUOTE_NUMBER.search(message)
    return {"quote_number": m.group(1).upper()} if m else None


def _extract_delete_customer(message: str) -> dict | None:
    # "delete customer Ada Lovelace"
    m = re.search(
        r"delete\s+(?:customer|client)\s+(?:named\s+)?[\"']?([A-Za-z][\w\s&.-]{1,40})[\"']?",
        message, re.I,
    )
    return {"customer_name": m.group(1).strip().rstrip(".!?,")} if m else None


def _extract_pricing_lookup(message: str) -> dict | None:
    patterns = [
        r"\b(?:price|cost|rate)s?\s+(?:for|of|on)\s+([^\n?.!,]{2,40})",
        r"\blook\s*up\s+([^\n?.!,]{2,40})\s+(?:pric|cost)",
        r"\bhow\s+much\s+(?:is|does|for|are)\s+([^\n?.!,]{2,40})",
    ]
    for p in patterns:
        m = re.search(p, message, re.I)
        if m:
            return {"query": m.group(1).strip().rstrip(".!?,")}
    return None


# ─── Registry ─────────────────────────────────────────────────────────────

INTENT_EXTRACTORS: dict[str, Callable[[str], dict | None]] = {
    # No args needed
    "get_dashboard_summary":  _no_args,
    "get_overdue_invoices":   _no_args,
    "get_profile":            _no_args,
    "list_templates":         _no_args,

    # Optional args
    "get_followups":          _extract_followups,
    "search_customers":       _extract_search_customers,
    "get_pricing_lookup":     _extract_pricing_lookup,

    # Entity-id args
    "get_quote_details":      _extract_quote_number,
    "send_quote":             _extract_quote_number,
    "duplicate_quote":        _extract_quote_number,
    "accept_quote":           _extract_quote_number,
    "reject_quote":           _extract_quote_number,
    "create_invoice":         _extract_create_invoice,
    "get_invoice_details":    _extract_invoice_number,
    "send_invoice":           _extract_invoice_number,
    "mark_invoice_paid":      _extract_invoice_number,
    "delete_customer":        _extract_delete_customer,
    # ... add yours
}


# ─── Context fill-in ───────────────────────────────────────────────────────

# Maps intent → (arg_name to fill, frontend context key to read from).
# Used when the user says "send this", "delete it", etc.
_CONTEXT_FILL: dict[str, tuple[str, str]] = {
    "get_quote_details":     ("quote_number", "current_quote_number"),
    "send_quote":            ("quote_number", "current_quote_number"),
    "duplicate_quote":       ("quote_number", "current_quote_number"),
    "accept_quote":          ("quote_number", "current_quote_number"),
    "reject_quote":          ("quote_number", "current_quote_number"),
    "delete_customer":       ("customer_name", "current_customer_name"),
    "get_invoice_details":   ("invoice_number", "current_invoice_number"),
    "send_invoice":          ("invoice_number", "current_invoice_number"),
}


def extract_args(intent_name: str, message: str) -> dict | None:
    """Run the extractor for `intent_name`, or return None if no extractor."""
    extractor = INTENT_EXTRACTORS.get(intent_name)
    if extractor is None:
        return None
    return extractor(message)


def apply_context(
    intent_name: str,
    args: dict | None,
    message: str,
    context: dict | None,
) -> dict | None:
    """Fill missing required arg from FE context when message is referential.

    Triggered only when:
      1. The intent has a (arg_name → ctx_key) mapping in _CONTEXT_FILL.
      2. The arg isn't already in `args`.
      3. The message contains a referential pronoun (this/that/it/...).
      4. The FE context has the key.
    """
    if not context:
        return args

    mapping = _CONTEXT_FILL.get(intent_name)
    if not mapping:
        return args

    arg_name, ctx_key = mapping

    if args is not None and arg_name in args:
        return args   # already extracted

    if not _REFERENTIAL.search(message):
        return args   # no this/that/it

    ctx_value = context.get(ctx_key)
    if not ctx_value:
        return args

    merged = dict(args) if args else {}
    merged[arg_name] = ctx_value
    return merged
