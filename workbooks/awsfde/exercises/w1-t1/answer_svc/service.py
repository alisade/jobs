"""POST /v1/answer: one question in, one answer out (API Gateway HTTP API -> Lambda)."""

from __future__ import annotations

import json
import logging
import pathlib
import random
import time
from typing import Any, Callable

from botocore.exceptions import ClientError

from .resilience import APP_POLICY, RetryPolicy, call_with_retries

log = logging.getLogger("tidewater.answer")
CONFIG = json.loads((pathlib.Path(__file__).resolve().parent.parent / "config" / "release.json").read_text())


def outcome_for_error(code: str) -> int:
    """HTTP status returned to the caller when the model call finally fails with `code`."""
    return 500


def error_response(code: str) -> dict:
    status = outcome_for_error(code)
    return {"statusCode": status, "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "internal_error", "detail": code})}


def answer(question: str, client: Any, *, policy: RetryPolicy = APP_POLICY,
           sleep: Callable[[float], None] = time.sleep, rng: Callable[[], float] = random.random) -> dict:
    def call() -> dict:
        return client.converse(
            modelId=CONFIG["model_id"],
            messages=[{"role": "user", "content": [{"text": question}]}],
            inferenceConfig={"maxTokens": CONFIG["max_tokens"]},
        )

    try:
        resp = call_with_retries(call, policy, sleep=sleep, rng=rng)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "Unknown")
        log.error(json.dumps({"event": "model_call_failed", "code": code}))
        return error_response(code)
    text = "".join(b.get("text", "") for b in resp["output"]["message"]["content"])
    return {"statusCode": 200, "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"answer": text})}
