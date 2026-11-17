"""POST /v1/answer: one question in, one answer out (API Gateway HTTP API -> Lambda)."""

from __future__ import annotations

import json
import logging
import pathlib
import random
import time
from typing import Any, Callable

from botocore.exceptions import ClientError

from .resilience import APP_POLICY, TRANSIENT_CODES, RetryPolicy, call_with_retries

log = logging.getLogger("tidewater.answer")
CONFIG = json.loads((pathlib.Path(__file__).resolve().parent.parent / "config" / "release.json").read_text())

RETRY_AFTER_S = 30
BUSY_MESSAGE = ("Tidewater Ask is busy right now. Your question was not lost: "
                "try again in about 30 seconds.")


def outcome_for_error(code: str) -> int:
    """HTTP status returned to the caller when the model call finally fails with `code`."""
    if code == "ValidationException":
        return 400            # the request itself is bad: retrying cannot help
    if code in TRANSIENT_CODES:
        return 503            # degraded: the portal shows "busy" and honors Retry-After
    return 500                # AccessDeniedException and anything else: our bug, page us


def error_response(code: str) -> dict:
    status = outcome_for_error(code)
    headers = {"Content-Type": "application/json"}
    if status == 503:
        headers["Retry-After"] = str(RETRY_AFTER_S)
        body = {"error": "busy", "message": BUSY_MESSAGE}
    elif status == 400:
        body = {"error": "invalid_request", "detail": code}
    else:
        body = {"error": "internal_error"}
    return {"statusCode": status, "headers": headers, "body": json.dumps(body)}


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
