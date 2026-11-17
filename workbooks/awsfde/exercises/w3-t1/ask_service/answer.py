"""Answer assembly. In production a Converse call writes the answer from the chunks; here a
deterministic stand-in quotes the best chunk so the replay is reproducible."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .retrieval import retrieve_context

NO_ANSWER = "I could not find that in your company's documents. Try rephrasing, or ask your admin to add the document."


@dataclass
class Answer:
    tenant_id: str
    question: str
    text: str
    citations: list[dict] = field(default_factory=list)   # [{"uri", "tenant_id", "score"}]
    grounded: bool = False


def answer(client: Any, tenant_id: str, question: str, request_id: str = "-") -> Answer:
    chunks = retrieve_context(client, tenant_id, question, request_id)
    if not chunks:
        return Answer(tenant_id, question, NO_ANSWER)
    best = chunks[0]
    cites = []
    for c in chunks[:3]:
        uri = c["location"]["s3Location"]["uri"]
        if uri not in [x["uri"] for x in cites]:
            cites.append({"uri": uri, "tenant_id": (c.get("metadata") or {}).get("tenant_id"), "score": c["score"]})
    return Answer(tenant_id, question, best["content"]["text"], cites, True)
