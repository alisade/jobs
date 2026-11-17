"""Retrieve context for a question from the tenant's documents. (release 2026.11.03)"""

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


def retrieve_context(client: Any, tenant_id: str, question: str, request_id: str = "-") -> list[dict]:
    """Chunks that can ground an answer for this tenant, best first."""
    resp = client.retrieve(
        knowledgeBaseId=KB_ID,
        retrievalQuery={"text": question},
        retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": TOP_K,
                                                              "filter": tenant_filter(tenant_id)}},
    )
    good = [r for r in resp.get("retrievalResults", []) if r.get("score", 0) >= MIN_SCORE]
    log.info(json.dumps({"event": "retrieve", "request_id": request_id, "tenant_id": tenant_id,
                         "filtered": True, "returned": len(resp.get("retrievalResults", [])), "usable": len(good)}))
    return good
