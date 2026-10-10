"""Amazon Data Firehose transformation Lambda for Amazon Connect contact records (CTRs).

Connect streams contact records to Kinesis Data Streams; Firehose reads the stream, invokes this
Lambda with a batch, and writes the returned records to S3 using the partition keys we return
(dynamic partitioning). Contract per record: recordId (echo), result Ok | Dropped |
ProcessingFailed, data (base64), metadata.partitionKeys.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from typing import Any

DENY_ATTRIBUTES = {"ssn", "dob", "cardnumber", "cvv", "pin", "password"}
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CARD_CANDIDATE_RE = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")


def luhn_ok(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        total += d
        alt = not alt
    return total % 10 == 0


def redact_text(value: str) -> str:
    value = SSN_RE.sub("[REDACTED]", value)

    def card(m: re.Match) -> str:
        digits = re.sub(r"\D", "", m.group(0))
        return "[REDACTED]" if 13 <= len(digits) <= 19 and luhn_ok(digits) else m.group(0)

    return CARD_CANDIDATE_RE.sub(card, value)


def phone_hash(number: str | None) -> str | None:
    if not number:
        return None
    salt = os.environ.get("PHONE_HASH_SALT", "")
    return hashlib.sha256((salt + number).encode()).hexdigest()


def ts(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def retention_class(ctr: dict[str, Any], attrs: dict[str, str]) -> str:
    if attrs.get("legalHold") == "true":
        return "legal-hold"
    if ctr.get("Recording"):
        return "recorded-7y"
    return "standard-3y"


def transform(ctr: dict[str, Any]) -> dict[str, Any]:
    attrs = {k: v for k, v in (ctr.get("Attributes") or {}).items() if k.lower() not in DENY_ATTRIBUTES}
    attrs = {k: redact_text(str(v)) for k, v in attrs.items()}
    queue = ctr.get("Queue") or None
    agent = ctr.get("Agent") or None
    endpoint = ctr.get("CustomerEndpoint") or {}
    start = ts(ctr["InitiationTimestamp"])
    end = ts(ctr.get("DisconnectTimestamp"))
    answered = bool(agent and agent.get("ConnectedToAgentTimestamp"))
    talk = int((agent or {}).get("AgentInteractionDuration") or 0)
    hold = int((agent or {}).get("CustomerHoldDuration") or 0)
    acw = int((agent or {}).get("AfterContactWorkDuration") or 0)
    number = endpoint.get("Address") if endpoint else None
    return {
        "contact_id": ctr["ContactId"],
        "initial_contact_id": ctr.get("InitialContactId") or ctr["ContactId"],
        "channel": ctr["Channel"],
        "initiation_method": ctr.get("InitiationMethod"),
        "initiation_ts": ctr["InitiationTimestamp"],
        "disconnect_ts": ctr.get("DisconnectTimestamp"),
        "dt": start.strftime("%Y-%m-%d"),
        "duration_seconds": int((end - start).total_seconds()) if end else None,
        "queue_name": queue.get("Name") if queue else None,
        "queue_seconds": int(queue.get("Duration") or 0) if queue else None,
        "agent_username": agent.get("Username") if agent else None,
        "answered": answered,
        "abandoned": bool(queue) and not answered,
        "contained": not queue and not agent and attrs.get("selfServiceOutcome") == "resolved",
        "talk_seconds": talk if answered else None,
        "hold_seconds": hold if answered else None,
        "acw_seconds": acw if answered else None,
        "handle_seconds": talk + hold + acw if answered else None,
        "disconnect_reason": ctr.get("DisconnectReason"),
        "lex_intent": attrs.get("lexIntent"),
        "caller_verified": attrs.get("callerVerified") == "true",
        "phone_hash": phone_hash(number),
        "phone_last4": number[-4:] if number else None,
        "recorded": bool(ctr.get("Recording")),
        "retention_class": retention_class(ctr, attrs),
        "attributes": attrs,
    }


def lambda_handler(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    out = []
    for rec in event.get("records", []):
        rid = rec["recordId"]
        try:
            ctr = json.loads(base64.b64decode(rec["data"]))
            if not isinstance(ctr, dict) or "ContactId" not in ctr or "InitiationTimestamp" not in ctr:
                raise ValueError("not a contact record")
        except Exception:  # undecodable or not a CTR: keep it for the error prefix, do not crash the batch
            out.append({"recordId": rid, "result": "ProcessingFailed", "data": rec["data"]})
            continue
        if (ctr.get("Attributes") or {}).get("synthetic") == "true":
            out.append({"recordId": rid, "result": "Dropped", "data": rec["data"]})
            continue
        row = transform(ctr)
        data = base64.b64encode((json.dumps(row, sort_keys=True) + "\n").encode()).decode()
        out.append(
            {
                "recordId": rid,
                "result": "Ok",
                "data": data,
                "metadata": {"partitionKeys": {"channel": row["channel"].lower(), "dt": row["dt"], "retention": row["retention_class"]}},
            }
        )
    return {"records": out}
