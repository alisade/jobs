"""POST /v1/answer: one question in, one answer out (API Gateway HTTP API -> Lambda)."""

from __future__ import annotations

import json
import logging
import pathlib
from typing import Any

from botocore.exceptions import ClientError

log = logging.getLogger("tidewater.answer")
CONFIG = json.loads((pathlib.Path(__file__).resolve().parent.parent / "config" / "release.json").read_text())


def outcome_for_error(code: str) -> int:
    return 500


def answer(question: str, client: Any) -> dict:
    try:
        resp = client.converse(
            modelId=CONFIG["model_id"],
            messages=[{"role": "user", "content": [{"text": question}]}],
            inferenceConfig={"maxTokens": CONFIG["max_tokens"]},
        )
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "Unknown")
        log.error(json.dumps({"event": "model_call_failed", "code": code}))
        return {"statusCode": outcome_for_error(code), "body": json.dumps({"error": "internal_error"})}
    text = "".join(b.get("text", "") for b in resp["output"]["message"]["content"])
    return {"statusCode": 200, "body": json.dumps({"answer": text})}
