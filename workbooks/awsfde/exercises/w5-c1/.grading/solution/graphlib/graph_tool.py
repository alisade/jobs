"""The agent's graph tool: named openCypher templates on Neptune Analytics, scoped to the caller's tenant.

The model picks a template name and supplies arguments; it never supplies query text. The tenant
comes from the verified CallerContext and is bound as $tenant_id. Every node pattern in every
template must be constrained to $tenant_id, checked before the query is sent.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from .cypher import read_query

MAX_ROWS = 50
QUERY_TIMEOUT_MS = 5000
MAX_ARG_LEN = 100


@dataclass(frozen=True)
class CallerContext:
    tenant_id: str
    user_id: str
    request_id: str


class ToolError(Exception):
    """A failure the model should see (bad template name or arguments)."""


TEMPLATES: dict[str, dict] = {
    "suppliers_of_product": {"query": "q1_suppliers_of_product", "args": {"product": r"^[\w .,'&/()-]{1,100}$"}},
    "customers_exposed_to_supplier": {"query": "q2_customers_exposed_to_supplier", "args": {"supplier": r"^[\w .,'&/()-]{1,100}$"}},
    "products_reachable_from_supplier": {"query": "q3_products_within_two_hops", "args": {"supplier": r"^[\w .,'&/()-]{1,100}$"}},
    "parts_per_supplier": {"query": "q4_parts_per_supplier", "args": {}},
    "suppliers_in_country": {"query": "q5_suppliers_in_country", "args": {"country": r"^[A-Z]{2}$"}},
}

_NODE = re.compile(r"\(\s*([A-Za-z_]\w*)?\s*((?::\s*\w+\s*)*)(\{[^}]*\})?\s*\)")


def check_tenant_scoped(query: str) -> None:
    """Raise ValueError unless every node variable is constrained to $tenant_id."""
    where = query.split("WHERE", 1)[1] if "WHERE" in query else ""
    seen: set[str] = set()
    scoped: set[str] = set()
    for m in _NODE.finditer(query):
        var, _labels, props = m.group(1), m.group(2), m.group(3) or ""
        if not var:
            raise ValueError("anonymous node pattern () cannot be tenant-scoped; name it and constrain it")
        seen.add(var)
        if re.search(r"\btenant_id\s*:\s*\$tenant_id\b", props):
            scoped.add(var)
    for var in seen:
        if re.search(rf"\b{var}\.tenant_id\s*=\s*\$tenant_id\b", where):
            scoped.add(var)
    missing = sorted(seen - scoped)
    if not seen:
        raise ValueError("no node patterns found")
    if missing:
        raise ValueError(f"node variable(s) not scoped to $tenant_id: {', '.join(missing)}")


def build_request(graph_id: str, ctx: CallerContext, tool: str, args: dict) -> dict:
    spec = TEMPLATES.get(tool)
    if spec is None:
        raise ToolError(f"unknown graph tool {tool!r}; available: {', '.join(sorted(TEMPLATES))}")
    if not isinstance(args, dict):
        raise ToolError("arguments must be an object")
    extra = set(args) - set(spec["args"])
    if extra:
        raise ToolError(f"unexpected argument(s): {', '.join(sorted(extra))}")
    params: dict[str, Any] = {}
    for name, pattern in spec["args"].items():
        v = args.get(name)
        if not isinstance(v, str) or len(v) > MAX_ARG_LEN or not re.match(pattern, v):
            raise ToolError(f"invalid value for {name}")
        params[name] = v
    params["tenant_id"] = ctx.tenant_id
    query = read_query(spec["query"])
    check_tenant_scoped(query)
    return {"graphIdentifier": graph_id, "queryString": query, "language": "OPEN_CYPHER",
            "parameters": params, "queryTimeoutMilliseconds": QUERY_TIMEOUT_MS}


def run_tool(client: Any, graph_id: str, ctx: CallerContext, tool: str, args: dict) -> dict:
    resp = client.execute_query(**build_request(graph_id, ctx, tool, args))
    body = resp["payload"].read()
    data = json.loads(body.decode("utf-8") if isinstance(body, bytes) else body)
    rows = data.get("results", [])
    return {"rows": rows[:MAX_ROWS], "truncated": len(rows) > MAX_ROWS}
