"""Shared helpers for w1-t1 tests: a Stubber-backed bedrock-runtime client and the replay."""

from __future__ import annotations

import pathlib

import boto3
from botocore.config import Config
from botocore.stub import Stubber

ROOT = pathlib.Path(__file__).resolve().parent.parent


class StubBedrock:
    """Real bedrock-runtime client with SDK retries off; the Stubber replays responses in order."""

    def __init__(self) -> None:
        self.client = boto3.client("bedrock-runtime", region_name="us-east-1",
                                   config=Config(retries={"total_max_attempts": 1, "mode": "standard"}))
        self.stub = Stubber(self.client)
        self.calls = 0
        self.client.meta.events.register("provide-client-params.bedrock-runtime.Converse", self._count)

    def _count(self, params, **_):
        self.calls += 1

    def ok(self, text: str = "SH-10001 is in transit.") -> None:
        self.stub.add_response("converse", {
            "output": {"message": {"role": "assistant", "content": [{"text": text}]}},
            "stopReason": "end_turn",
            "usage": {"inputTokens": 50, "outputTokens": 10, "totalTokens": 60},
            "metrics": {"latencyMs": 2100},
        })

    def error(self, code: str, status: int = 400) -> None:
        self.stub.add_client_error("converse", service_error_code=code, service_message=code,
                                   http_status_code=status)
