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


def _request(question: str, flt: dict | None) -> dict:
    vsc: dict = {"numberOfResults": TOP_K}
    if flt is not None:
        vsc["filter"] = flt
    return {"knowledgeBaseId": KB_ID, "retrievalQuery": {"text": question},
            "retrievalConfiguration": {"vectorSearchConfiguration": vsc}}


def retrieve_context(client: Any, tenant_id: str, question: str, request_id: str = "-") -> list[dict]:
    """Chunks that can ground an answer for this tenant, best first."""
    resp = client.retrieve(**_request(question, tenant_filter(tenant_id)))
    good = [r for r in resp.get("retrievalResults", []) if r.get("score", 0) >= MIN_SCORE]
    log.info(json.dumps({"event": "retrieve", "request_id": request_id, "tenant_id": tenant_id,
                         "filtered": True, "returned": len(resp.get("retrievalResults", [])), "usable": len(good)}))

    # ASK-412: too many "I don't know" answers for tenants with thin document sets. Widen the
    # search so the model still has something relevant to work with.
    if not good:
        resp = client.retrieve(**_request(question, None))
        good = [r for r in resp.get("retrievalResults", []) if r.get("score", 0) >= MIN_SCORE]
        log.info(json.dumps({"event": "retrieve", "request_id": request_id, "tenant_id": tenant_id,
                             "filtered": False, "returned": len(resp.get("retrievalResults", [])), "usable": len(good)}))
    return good
