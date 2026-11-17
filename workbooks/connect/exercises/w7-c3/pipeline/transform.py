"""Amazon Data Firehose transformation Lambda for Amazon Connect contact records (CTRs).

Connect streams contact records to Kinesis Data Streams; Firehose reads the stream, invokes this
Lambda with a batch, and writes the returned records to S3. See README.md for the contract and
LFG's data-handling rules. This is the version that went to the data lake pilot.
"""
from __future__ import annotations

import base64
import json
from typing import Any


def transform(ctr: dict[str, Any]) -> dict[str, Any]:
    queue = ctr.get("Queue") or None
    agent = ctr.get("Agent") or None
    endpoint = ctr.get("CustomerEndpoint") or {}
    return {
        "contact_id": ctr["ContactId"],
        "channel": ctr["Channel"],
        "initiation_ts": ctr["InitiationTimestamp"],
        "dt": ctr["InitiationTimestamp"][:10],
        "queue_name": queue.get("Name") if queue else None,
        "queue_seconds": queue.get("Duration") if queue else None,
        "agent_username": agent.get("Username") if agent else None,
        "answered": bool(agent),
        "abandoned": bool(queue) and not agent,
        "handle_seconds": (agent or {}).get("AgentInteractionDuration"),
        "customer_phone": endpoint.get("Address") if endpoint else None,
        "lex_intent": (ctr.get("Attributes") or {}).get("lexIntent"),
        "attributes": ctr.get("Attributes") or {},
        # TODO: the remaining output columns, redaction, retention class (README)
    }


def lambda_handler(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    out = []
    for rec in event.get("records", []):
        ctr = json.loads(base64.b64decode(rec["data"]))
        row = transform(ctr)
        out.append({"recordId": rec["recordId"], "result": "Ok", "data": base64.b64encode(json.dumps(row).encode()).decode()})
    return {"records": out}
