"""SQS-triggered Lambda: S3 "Object Created" events (via EventBridge) -> one KB ingestion job each.

Pipeline: S3 -> EventBridge rule (source aws.s3, detail-type Object Created) -> SQS queue (with a
redrive policy to a DLQ) -> this Lambda (event source mapping with ReportBatchItemFailures).

Delivery is at least once (S3 event delivery, EventBridge and SQS all may duplicate), so the handler
is idempotent: the job record is written with a conditional put before StartIngestionJob, and the
call carries a clientToken derived from the object version, so a retry after a crash is safe too.
"""

from __future__ import annotations

import hashlib
import json
import logging
import pathlib
import re
import time
from dataclasses import dataclass
from typing import Any

from botocore.exceptions import ClientError

log = logging.getLogger("tidewater.ingest")
CONFIG = json.loads((pathlib.Path(__file__).resolve().parent / "config.json").read_text())
KEY_RE = re.compile(r"^tenants/([a-z0-9][a-z0-9-]{1,62})/docs/([^/].*)$")


class Poison(ValueError):
    """A message that can never succeed: record it and drop it (do not redeliver)."""


@dataclass(frozen=True)
class ObjectCreated:
    bucket: str
    key: str
    etag: str
    sequencer: str
    tenant_id: str


def parse(body: str, bucket: str) -> ObjectCreated:
    try:
        ev = json.loads(body)
    except (TypeError, ValueError) as e:
        raise Poison(f"body is not JSON: {e}") from None
    if not isinstance(ev, dict) or ev.get("source") != "aws.s3" or ev.get("detail-type") != "Object Created":
        raise Poison("not an S3 Object Created event")
    d = ev.get("detail") or {}
    b = (d.get("bucket") or {}).get("name")
    o = d.get("object") or {}
    key, etag, seq = o.get("key"), o.get("etag"), o.get("sequencer")
    if b != bucket:
        raise Poison(f"unexpected bucket {b!r}")
    if not (isinstance(key, str) and etag and seq):
        raise Poison("object key, etag or sequencer missing")
    m = KEY_RE.match(key)
    if not m or ".." in key.split("/") or key.endswith(".metadata.json"):
        raise Poison(f"key outside tenants/<tenant>/docs/: {key!r}")
    return ObjectCreated(b, key, str(etag), str(seq), m.group(1))


def job_key(obj: ObjectCreated) -> dict:
    h = hashlib.sha256(obj.key.encode()).hexdigest()[:16]
    return {"pk": f"TENANT#{obj.tenant_id}", "sk": f"INGEST#{h}#{obj.sequencer}"}


def client_token(obj: ObjectCreated) -> str:
    return hashlib.sha256(f"{obj.tenant_id}|{obj.key}|{obj.sequencer}".encode()).hexdigest()  # 64 chars


def _tenant(table: Any, tenant_id: str) -> dict:
    item = table.get_item(Key={"pk": f"TENANT#{tenant_id}", "sk": "PROFILE"}).get("Item")
    if not item or item.get("status") != "active":
        raise Poison(f"unknown or inactive tenant {tenant_id!r}")
    return item


def process(obj: ObjectCreated, table: Any, agent: Any) -> str:
    """Returns "started" or "duplicate". Raises ClientError for AWS failures."""
    tenant = _tenant(table, obj.tenant_id)
    key = job_key(obj)
    try:
        table.put_item(Item={**key, "status": "PENDING", "object_key": obj.key, "etag": obj.etag,
                             "sequencer": obj.sequencer, "created_at": int(time.time())},
                       ConditionExpression="attribute_not_exists(pk)")
    except ClientError as e:
        if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
            raise
        existing = table.get_item(Key=key, ConsistentRead=True).get("Item") or {}
        if existing.get("status") == "STARTED":
            return "duplicate"
        # PENDING: an earlier attempt wrote the record but did not start the job; finish it.
    resp = agent.start_ingestion_job(knowledgeBaseId=tenant["knowledge_base_id"], dataSourceId=tenant["data_source_id"],
                                     clientToken=client_token(obj), description=f"s3 {obj.key}"[:200])
    table.update_item(Key=key, UpdateExpression="SET #s = :s, ingestion_job_id = :j",
                      ExpressionAttributeNames={"#s": "status"},
                      ExpressionAttributeValues={":s": "STARTED", ":j": resp["ingestionJob"]["ingestionJobId"]})
    return "started"


def handler(event: dict, context: Any = None, table: Any = None, agent: Any = None) -> dict:
    if table is None or agent is None:  # pragma: no cover - real Lambda wiring
        import boto3
        table = table or boto3.resource("dynamodb").Table(CONFIG["table_name"])
        agent = agent or boto3.client("bedrock-agent")
    failures = []
    for rec in event.get("Records", []):
        mid = rec["messageId"]
        try:
            obj = parse(rec.get("body"), CONFIG["bucket"])
            outcome = process(obj, table, agent)
            log.info(json.dumps({"event": outcome, "message_id": mid, "tenant_id": obj.tenant_id, "key": obj.key}))
        except Poison as e:
            log.error(json.dumps({"event": "poison", "message_id": mid, "reason": str(e)}))
            table.put_item(Item={"pk": "POISON", "sk": f"MSG#{mid}", "reason": str(e)[:500],
                                 "body": str(rec.get("body"))[:2000], "created_at": int(time.time())})
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            retry = code in CONFIG["retryable_errors"]
            log.warning(json.dumps({"event": "retry" if retry else "failed", "message_id": mid, "code": code,
                                    "receive_count": rec.get("attributes", {}).get("ApproximateReceiveCount")}))
            failures.append({"itemIdentifier": mid})
    return {"batchItemFailures": failures}
