"""Shared fixtures for w1-c1: a moto DynamoDB table and a Stubber-backed bedrock-runtime client.

The Stubber returns recorded Converse responses in order. botocore still validates every request
against the real Converse API model, so a malformed request fails here the way it would fail
with a ValidationException in AWS.
"""

from __future__ import annotations

import copy
import json
import pathlib

import boto3
import pytest
from botocore.stub import Stubber
from moto import mock_aws

from ask_agent.context import CallerContext

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load_config() -> dict:
    return json.loads((ROOT / "config.json").read_text())


SHIPMENTS = [
    ("acme-foods", "SH-10001", "IN_TRANSIT", "Fresno, CA", "Denver, CO", "2026-11-16"),
    ("acme-foods", "SH-10002", "DELIVERED", "Fresno, CA", "Boise, ID", "2026-11-10"),
    ("brightline-health", "SH-20001", "HELD_AT_CUSTOMS", "Toronto, ON", "Buffalo, NY", "2026-11-20"),
]


class Bedrock:
    """A real boto3 client with a Stubber; records every converse() call's kwargs."""

    def __init__(self) -> None:
        self.client = boto3.client("bedrock-runtime", region_name="us-east-1")
        self.stub = Stubber(self.client)
        self.requests: list[dict] = []
        self.client.meta.events.register(
            "provide-client-params.bedrock-runtime.Converse",
            lambda params, **_: self.requests.append(copy.deepcopy(params)),
        )

    def add(self, response: dict) -> None:
        self.stub.add_response("converse", response)

    def add_error(self, code: str, message: str = "x", status: int = 400) -> None:
        self.stub.add_client_error("converse", service_error_code=code, service_message=message,
                                   http_status_code=status)


def reply(content: list[dict], stop: str, in_tok: int = 120, out_tok: int = 30,
          latency: int = 400, trace: dict | None = None, cache_read: int = 0) -> dict:
    usage = {"inputTokens": in_tok, "outputTokens": out_tok, "totalTokens": in_tok + out_tok}
    if cache_read:
        usage["cacheReadInputTokens"] = cache_read
    r = {
        "output": {"message": {"role": "assistant", "content": content}},
        "stopReason": stop,
        "usage": usage,
        "metrics": {"latencyMs": latency},
    }
    if trace is not None:
        r["trace"] = trace
    return r


def text(t: str) -> dict:
    return {"text": t}


def tool_use(tool_use_id: str, name: str, inp: dict) -> dict:
    return {"toolUse": {"toolUseId": tool_use_id, "name": name, "input": inp}}


@pytest.fixture
def config() -> dict:
    return load_config()


@pytest.fixture
def ctx() -> CallerContext:
    return CallerContext(tenant_id="acme-foods", user_id="u-7f3a", request_id="req-0001")


@pytest.fixture
def table(config):
    with mock_aws():
        ddb = boto3.resource("dynamodb", region_name="us-east-1")
        t = ddb.create_table(
            TableName=config["table_name"],
            KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}, {"AttributeName": "sk", "KeyType": "RANGE"}],
            AttributeDefinitions=[{"AttributeName": "pk", "AttributeType": "S"},
                                  {"AttributeName": "sk", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        for tenant, sid, status, origin, dest, eta in SHIPMENTS:
            t.put_item(Item={"pk": f"TENANT#{tenant}", "sk": f"SHIPMENT#{sid}", "status": status,
                             "origin": origin, "destination": dest, "eta": eta})
        yield t


@pytest.fixture
def bedrock():
    b = Bedrock()
    with b.stub:
        yield b
