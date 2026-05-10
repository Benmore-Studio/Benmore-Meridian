# Recipe: Adding a Tool to Your Chatbot

Five steps. The whole loop takes 10–20 minutes per tool.

## 1. Pick the right granularity

Each tool should be one **user-meaningful action**, not one ORM operation.
"Send a quote" is one tool, even if it touches 3 tables and enqueues 2
Celery jobs. "Update customer.email" alone is too granular — make it
`update_customer(args: {customer_name, email?, phone?, ...})`.

Heuristics:

- If you can write the tool description in one sentence, it's the right
  size.
- If users would say "Can you X for me?" naturally, X is a tool.
- 5–15 tools per domain module is typical. > 20 is a smell — split the
  module.

## 2. Define the schema (`definitions.py`)

```python
# in chat_tools/definitions.py

from .builder import _tool   # (helper that builds OpenAI function shape)

CUSTOMER_TOOLS = [
    _tool(
        name="create_customer",
        description="Create a new customer in the user's organization.",
        properties={
            "name":         {"type": "string", "description": "Customer full name."},
            "email":        {"type": "string", "description": "Email address. Optional."},
            "phone":        {"type": "string", "description": "Phone (E.164). Optional."},
            "company_name": {"type": "string", "description": "Company. Optional."},
        },
        required=["name"],
    ),
    _tool(
        name="search_customers",
        description="Search customers by name, email, or company. Returns up to 5.",
        properties={
            "query": {"type": "string", "description": "Search string."},
        },
        required=["query"],
    ),
    # ...
]
```

Tips for descriptions:

- **Tool description** — describe *when to call it*, not what it does. The
  model already infers what from the name. "Use when the user asks to
  create a new customer record" is better than "Creates a customer".
- **Parameter descriptions** — include format hints, units, ranges.
  ("E.164", "ISO date", "1-100"). The model trusts these.
- Keep descriptions tight. They're sent on every request and cost tokens.

## 3. Implement the handler

```python
# in chat_tools/customer_tools.py

def create_customer(user, args: dict) -> dict:
    """Create a customer scoped to user.organization."""
    from myapp.customers.models import Customer

    name = (args.get("name") or "").strip()
    if not name:
        return {"error": "name is required."}

    phone = args.get("phone", "")
    if phone:
        try:
            phone = normalize_phone(phone)   # E.164 normalization
        except ValueError:
            return {"error": f"Invalid phone: {phone}"}

    customer = Customer.objects.create(
        organization=user.organization,
        created_by=user,
        name=name,
        email=args.get("email", ""),
        phone=phone,
        company_name=args.get("company_name", ""),
    )

    return {
        "id":      str(customer.id),
        "name":    customer.name,
        "created": True,
    }


HANDLERS = {
    "create_customer":  create_customer,
    "search_customers": search_customers,
    # ...
}
```

Conventions every handler must follow:

- **Signature**: `(user, args: dict) -> dict | list`.
- **Tenant scoping**: `Customer.objects.filter(organization=user.organization)`.
  Never trust args to be tenant-scoped.
- **Return envelope**: `{...result..., "success": True}` on writes; bare
  `{...}` or `[...]` on reads; `{"error": "..."}` on user-level failures.
- **Don't catch programming errors**. `AttributeError`, `KeyError`,
  `TypeError` should propagate to your error tracker. Catch domain
  exceptions: `IntegrityError`, `PermissionDenied`, `ValidationError`,
  `<Vendor>Error`.
- **Stringify Decimals/UUIDs/datetimes** — `str(decimal_value)`,
  `str(uuid)`, `dt.strftime(...)`. Otherwise the model sees ugly JSON
  serialization errors.

## 4. Register

Two places:

```python
# in chat_tools/definitions.py
ALL_TOOLS = [
    *CUSTOMER_TOOLS,
    *QUOTE_TOOLS,
    *ORDER_TOOLS,
]

# in chat_tools/__init__.py
from .customer_tools import HANDLERS as _CUSTOMER
from .quote_tools    import HANDLERS as _QUOTE
from .order_tools    import HANDLERS as _ORDER

ALL_HANDLERS = {**_CUSTOMER, **_QUOTE, **_ORDER}
```

If the tool is gated (Pro-only, admin-only):

```python
# in chat_tools/__init__.py
PRO_ONLY_TOOLS = frozenset({
    "create_invoice", "send_invoice", "create_payment_link",
    # add new ones here
})
```

## 5. Verify

Run the parity check (every schema has a handler):

```python
from chat_tools import ALL_TOOLS, ALL_HANDLERS
defs = {t["function"]["name"] for t in ALL_TOOLS}
handlers = set(ALL_HANDLERS)
assert defs == handlers, defs ^ handlers
```

If your build pipeline lets you, add this as a unit test that runs in CI.

Then smoke test:

```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"create a customer named Ada Lovelace","history":[],"context":{}}'
```

Expect 200, `actions[0].tool == "create_customer"`, and a customer row in
your DB.

## Anti-patterns

Things that look reasonable but bite later:

❌ **Hiding tools to enforce gating.** "If user is free, don't include the
Pro tools in `ALL_TOOLS`." Don't. The model's behavior is more predictable
when it sees the same catalog every time. Gate at dispatch.

❌ **Returning the full DB row.** The model only needs identifiers and
human-readable fields. Returning everything wastes tokens and leaks
internal fields. `{"id": str(c.id), "name": c.name}` is plenty for most
cases; `get_customer_details` can return more.

❌ **Mixing read and write semantics in one tool.** `update_or_create_customer`
is hard for the model to reason about. Split into `create_customer` and
`update_customer` with `customer_name` (fuzzy lookup) as the resolution arg.

❌ **Using free-form strings for enums.** If status can only be one of
{`draft`, `sent`, `accepted`, `rejected`}, mark it `enum` in the schema.
The model respects this and you avoid validation code in the handler.

❌ **One mega-tool that takes a `command` arg.** `do_anything(command:
"create-customer-and-quote-and-invoice")` defeats the purpose of function
calling. Multi-turn loop + small focused tools is better.

❌ **Echoing back PII in the response.** If args include an email or phone,
strip before logging. Same applies to the result envelope — the result
becomes part of the conversation history and may be cached.

## When to add a fast-path extractor

If a new intent is in the top 5 most common, also add it to
`INTENT_EXTRACTORS` in `intent_extractors.py`. The extractor is a function
`(message: str) -> dict | None` that pulls args via regex.

```python
def extract_create_customer(message: str) -> dict | None:
    # "create a customer named Ada Lovelace"
    m = re.search(r"customer\s+(?:named|called)\s+([A-Z][\w\s]+)", message)
    if m:
        return {"name": m.group(1).strip()}
    return None

INTENT_EXTRACTORS["create_customer"] = extract_create_customer
```

If the regex doesn't match, return `None` and the dispatch falls back to
the LLM. Your test cases should cover both — a phrase the regex catches
and one it misses.
