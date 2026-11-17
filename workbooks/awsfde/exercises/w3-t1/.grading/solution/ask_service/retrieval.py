"""Retrieve context for a question from the tenant's documents."""

from __future__ import annotations

import json
import logging
from typing import Any

log = logging.getLogger("tidewater.retrieval")

KB_ID = "KBTIDEWATER01"
TOP_K = 5
MIN_SCORE = 0.30   # chunks below this are too weak to ground an answer


def tenant_filter(tenant_id: str) -> dict:
    return {"equals": {"key": "tenant_id", "value": tenant_id}}


def _request(question: str, tenant_id: str) -> dict:
    # The tenant filter is part of every request; there is no code path without it.
    return {"knowledgeBaseId": KB_ID, "retrievalQuery": {"text": question},
            "retrievalConfiguration": {"vectorSearchConfiguration": {"numberOfResults": TOP_K,
                                                                     "filter": tenant_filter(tenant_id)}}}


def retrieve_context(client: Any, tenant_id: str, question: str, request_id: str = "-") -> list[dict]:
    """Chunks that can ground an answer for this tenant, best first.

    Fewer documents means more "I could not find that" answers; that is the correct outcome for a
    tenant whose library is not loaded yet. ASK-412's unfiltered retry is removed.
    """
    if not tenant_id:
        raise ValueError("tenant_id is required")
    resp = client.retrieve(**_request(question, tenant_id))
    results = resp.get("retrievalResults", [])
    own = []
    for r in results:
        if (r.get("metadata") or {}).get("tenant_id") == tenant_id:
            own.append(r)
        else:  # defense in depth: an untagged or mis-tagged chunk is a security event, never context
            log.error(json.dumps({"event": "foreign_chunk_dropped", "request_id": request_id, "tenant_id": tenant_id,
                                  "uri": r.get("location", {}).get("s3Location", {}).get("uri"),
                                  "chunk_tenant": (r.get("metadata") or {}).get("tenant_id")}))
    good = [r for r in own if r.get("score", 0) >= MIN_SCORE]
    log.info(json.dumps({"event": "retrieve", "request_id": request_id, "tenant_id": tenant_id,
                         "filtered": True, "returned": len(results), "usable": len(good)}))
    return good
