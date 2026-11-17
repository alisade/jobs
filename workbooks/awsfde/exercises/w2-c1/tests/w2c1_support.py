"""Helpers for w2-c1: tokens as the runtime forwards them, and a Stubber-backed Memory client.

botocore validates every RetrieveMemoryRecords / CreateEvent request against the real
bedrock-agentcore model (actorId and sessionId patterns, required fields), so a malformed request
fails here as a ParamValidationError instead of a ValidationException in AWS.
"""

from __future__ import annotations

import base64
import datetime as dt
import json
import pathlib

import boto3
import pytest
from botocore.stub import ANY, Stubber

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "config.json").read_text())
MEMORY_ID = CONFIG["memory_id"]
SESSION = "sess-acme-2026-11-13-0001-7f3a9c2e0b1d4c55"

ALICE = {"sub": "7f3a9c2e-0b1d-4c55-9e0a-2a1b3c4d5e6f", "tenant_id": "acme-foods", "token_use": "access"}
BOB = {"sub": "91d0b6aa-33c2-4f7e-8b11-0c9d8e7f6a5b", "tenant_id": "brightline-health", "token_use": "access"}


def token(claims: dict) -> str:
    def b64(d: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")
    return f"{b64({'alg': 'RS256', 'kid': 'k1'})}.{b64(claims)}.c2lnbmF0dXJl"


def headers(claims: dict | None, session: str | None = SESSION) -> dict:
    h = {"Content-Type": "application/json"}
    if claims is not None:
        h["Authorization"] = "Bearer " + token(claims)
    if session is not None:
        h["X-Amzn-Bedrock-AgentCore-Runtime-Session-Id"] = session
    return h


def body(**kw) -> bytes:
    return json.dumps(kw).encode()


def ns(claims: dict) -> str:
    return f"/tenant/{claims['tenant_id']}/actor/{claims['tenant_id']}:{claims['sub']}/preferences/"


def record(text: str, claims: dict) -> dict:
    return {"memoryRecordId": "mem-" + "a" * 40, "content": {"text": text},
            "memoryStrategyId": "TenantUserPreferences-x1y2z3w4v5", "namespaces": [ns(claims)],
            "createdAt": dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc), "score": 0.91}


class Memory:
    def __init__(self) -> None:
        self.client = boto3.client("bedrock-agentcore", region_name="us-east-1")
        self.stub = Stubber(self.client)
        self.calls: list[tuple[str, dict]] = []
        for op in ("RetrieveMemoryRecords", "CreateEvent"):
            self.client.meta.events.register(
                f"provide-client-params.bedrock-agentcore.{op}",
                lambda params, _op=op, **_: self.calls.append((_op, json.loads(json.dumps(params, default=str)))))

    def expect_retrieve(self, claims: dict, texts: list[str], query: str | None = None) -> None:
        self.stub.add_response(
            "retrieve_memory_records", {"memoryRecordSummaries": [record(t, claims) for t in texts]},
            {"memoryId": MEMORY_ID, "namespace": ns(claims),
             "searchCriteria": {"searchQuery": query if query is not None else ANY, "topK": ANY}})

    def expect_create(self, claims: dict) -> None:
        self.stub.add_response(
            "create_event",
            {"event": {"memoryId": MEMORY_ID, "actorId": f"{claims['tenant_id']}:{claims['sub']}",
                       "sessionId": SESSION, "eventId": "0000001731500000000#a1b2c3d4",
                       "eventTimestamp": dt.datetime(2026, 11, 13, tzinfo=dt.timezone.utc), "payload": []}},
            {"memoryId": MEMORY_ID, "actorId": f"{claims['tenant_id']}:{claims['sub']}", "sessionId": SESSION,
             "eventTimestamp": ANY, "payload": ANY,
             "extractionConfig": {"namespaceVariables": {"tenantid": claims["tenant_id"]}}})

    def error(self, op: str, code: str, status: int = 429) -> None:
        self.stub.add_client_error(op, service_error_code=code, service_message=code, http_status_code=status)


@pytest.fixture
def mem():
    m = Memory()
    with m.stub:
        yield m
