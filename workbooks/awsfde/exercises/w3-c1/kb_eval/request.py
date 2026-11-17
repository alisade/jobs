"""Build the Retrieve request. The tenant filter is not optional."""

from __future__ import annotations

TENANT_KEY = "tenant_id"


def build_retrieve_request(kb_id: str, tenant_id: str, query: str,
                           user_filters: list[dict] | None = None, k: int = 5) -> dict:
    """Keyword arguments for bedrock_agent_runtime.retrieve().

    TODO (README "Part A"):
    - retrievalQuery.text = query (reject empty), numberOfResults = k (1..100)
    - the filter always contains equals tenant_id == tenant_id (the verified tenant)
    - extra user filters are ANDed with it; andAll needs at least two members
    - a user filter that mentions tenant_id anywhere (even nested) raises ValueError
    """
    raise NotImplementedError
