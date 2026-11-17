"""Build the Retrieve request. The tenant filter is not optional."""

from __future__ import annotations

TENANT_KEY = "tenant_id"


def _mentions_tenant(f: object) -> bool:
    if isinstance(f, dict):
        if f.get("key") == TENANT_KEY:
            return True
        return any(_mentions_tenant(v) for v in f.values())
    if isinstance(f, list):
        return any(_mentions_tenant(v) for v in f)
    return False


def build_retrieve_request(kb_id: str, tenant_id: str, query: str,
                           user_filters: list[dict] | None = None, k: int = 5) -> dict:
    """Keyword arguments for bedrock_agent_runtime.retrieve()."""
    if not tenant_id:
        raise ValueError("tenant_id is required")
    if not query or not query.strip():
        raise ValueError("query must not be empty")
    if not 1 <= int(k) <= 100:
        raise ValueError("k must be between 1 and 100")
    user_filters = list(user_filters or [])
    if _mentions_tenant(user_filters):
        raise ValueError("user filters may not reference tenant_id")
    tenant_filter = {"equals": {"key": TENANT_KEY, "value": tenant_id}}
    flt = {"andAll": [tenant_filter, *user_filters]} if user_filters else tenant_filter
    return {
        "knowledgeBaseId": kb_id,
        "retrievalQuery": {"text": query},
        "retrievalConfiguration": {"vectorSearchConfiguration": {"numberOfResults": int(k), "filter": flt}},
    }
