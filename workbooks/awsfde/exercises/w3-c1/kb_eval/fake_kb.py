"""A recorded stand-in for bedrock-agent-runtime Retrieve (done; do not edit).

Every request is validated against the real Retrieve input shape from botocore's service model, so a
filter that AWS would reject (for example an andAll with one member) raises ParamValidationError
here too. Responses come from fixtures/recorded-<config>.json, keyed by question text.
"""

from __future__ import annotations

import copy
import json
import pathlib

import boto3
from botocore.validate import ParamValidator

_MODEL = boto3.client("bedrock-agent-runtime", region_name="us-east-1").meta.service_model
_RETRIEVE = _MODEL.operation_model("Retrieve").input_shape


class RecordedKnowledgeBase:
    def __init__(self, recordings: dict[str, list[dict]], golden: list[dict]) -> None:
        self._by_text = {q["question"]: recordings.get(q["id"], []) for q in golden}
        self.requests: list[dict] = []

    @classmethod
    def from_fixtures(cls, config: str, root: pathlib.Path | None = None) -> "RecordedKnowledgeBase":
        root = root or pathlib.Path(__file__).resolve().parent.parent / "fixtures"
        golden = json.loads((root / "golden.json").read_text())
        rec = json.loads((root / f"recorded-{config}.json").read_text())
        return cls(rec, golden)

    def retrieve(self, **params) -> dict:
        report = ParamValidator().validate(params, _RETRIEVE)
        if report.has_errors():
            from botocore.exceptions import ParamValidationError
            raise ParamValidationError(report=report.generate_report())
        self.requests.append(copy.deepcopy(params))
        text = params["retrievalQuery"]["text"]
        k = params.get("retrievalConfiguration", {}).get("vectorSearchConfiguration", {}).get("numberOfResults", 5)
        return {"retrievalResults": copy.deepcopy(self._by_text.get(text, []))[:k]}
