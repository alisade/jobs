"""A Knowledge Base simulator with the Retrieve API's request and response shapes.

- Documents and their `<file>.metadata.json` sidecars (`{"metadataAttributes": {...}}`) are read
  from kb_sim/corpus/ the way a KB data source sync reads an S3 prefix.
- Chunks are sentences (a stand-in for the hierarchical chunking re-ingest).
- Scores are a deterministic word-overlap similarity in [0, 1], not real embeddings.
- Filters support equals, notEquals, in, andAll and orAll with Retrieve semantics.
- Every request is validated against the real Retrieve input shape from botocore.
- Every call is appended to `self.calls` and, if a log path is given, to a JSON-lines log in the
  shape of the service's own retrieval log.
"""

from __future__ import annotations

import copy
import json
import math
import pathlib
import re

import boto3
from botocore.exceptions import ParamValidationError
from botocore.validate import ParamValidator

_SHAPE = boto3.client("bedrock-agent-runtime", region_name="us-east-1").meta.service_model.operation_model("Retrieve").input_shape
CORPUS = pathlib.Path(__file__).resolve().parent / "corpus"
BUCKET = "s3://tidewater-kb-docs-111122223333/tenants"
STOP = set("a an the and or of to for in on at by is are be can do does what how how many much we our my i you "
           "your with after before per that this it if from".split())


def words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP}


def _match(flt: dict | None, md: dict) -> bool:
    if not flt:
        return True
    (op, arg), = flt.items()
    if op == "andAll":
        return all(_match(f, md) for f in arg)
    if op == "orAll":
        return any(_match(f, md) for f in arg)
    val = md.get(arg["key"])
    if op == "equals":
        return val == arg["value"]
    if op == "notEquals":
        return val != arg["value"]
    if op == "in":
        return val in arg["value"]
    raise ValueError(f"filter operator {op} not supported by the simulator")


class KnowledgeBase:
    def __init__(self, corpus: pathlib.Path = CORPUS, log_path: pathlib.Path | None = None) -> None:
        self.chunks: list[dict] = []
        for f in sorted(corpus.glob("*/*.txt")):
            side = f.with_name(f.name + ".metadata.json")
            md = json.loads(side.read_text())["metadataAttributes"] if side.exists() else {}
            uri = f"{BUCKET}/{f.parent.name}/docs/{f.stem}.pdf"
            for i, sent in enumerate(s.strip() for s in re.split(r"(?<=\.)\s+", f.read_text()) if s.strip()):
                self.chunks.append({"text": sent, "uri": uri, "md": dict(md, **{"x-amz-bedrock-kb-source-uri": uri,
                                                                                    "x-amz-bedrock-kb-chunk-id": f"{f.stem}-{i}"})})
        self.calls: list[dict] = []
        self.log_path = log_path

    def retrieve(self, **params) -> dict:
        report = ParamValidator().validate(params, _SHAPE)
        if report.has_errors():
            raise ParamValidationError(report=report.generate_report())
        self.calls.append(copy.deepcopy(params))
        vsc = params.get("retrievalConfiguration", {}).get("vectorSearchConfiguration", {})
        k, flt = vsc.get("numberOfResults", 5), vsc.get("filter")
        q = words(params["retrievalQuery"]["text"])
        scored = []
        for c in self.chunks:
            if not _match(flt, c["md"]):
                continue
            d = words(c["text"])
            s = len(q & d) / math.sqrt(len(q) * len(d)) if q and d else 0.0
            scored.append((round(s, 4), c))
        scored.sort(key=lambda x: (-x[0], x[1]["uri"]))
        results = [{"content": {"type": "TEXT", "text": c["text"]},
                    "location": {"type": "S3", "s3Location": {"uri": c["uri"]}},
                    "metadata": copy.deepcopy(c["md"]), "score": s} for s, c in scored[:k]]
        if self.log_path:
            with self.log_path.open("a") as fh:
                fh.write(json.dumps({"component": "kb", "knowledgeBaseId": params["knowledgeBaseId"],
                                     "filter": flt, "numberOfResults": k, "returned": len(results),
                                     "top_score": results[0]["score"] if results else None,
                                     "uris": [r["location"]["s3Location"]["uri"] for r in results]}) + "\n")
        return {"retrievalResults": results}
