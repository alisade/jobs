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
    """TODO: the SQS body is the EventBridge event. Raise Poison for anything that can never succeed: bad JSON, not source aws.s3 / detail-type Object Created, another bucket, missing key/etag/sequencer, a key outside tenants/<tenant>/docs/ (including ".." segments and .metadata.json sidecars)."""
    raise NotImplementedError



def job_key(obj: ObjectCreated) -> dict:
    """TODO: the ingestion job record key: tenant partition, one item per object version (sequencer)."""
    raise NotImplementedError



def client_token(obj: ObjectCreated) -> str:
    """TODO: deterministic StartIngestionJob clientToken for this object version (33-256 characters)."""
    raise NotImplementedError



def _tenant(table: Any, tenant_id: str) -> dict:
    item = table.get_item(Key={"pk": f"TENANT#{tenant_id}", "sk": "PROFILE"}).get("Item")
    if not item or item.get("status") != "active":
        raise Poison(f"unknown or inactive tenant {tenant_id!r}")
    return item


def process(obj: ObjectCreated, table: Any, agent: Any) -> str:
    """TODO: tenant registry check (Poison if unknown or inactive), conditional put of a PENDING job record, StartIngestionJob with the clientToken, then mark STARTED. A duplicate of a STARTED record returns "duplicate" without calling Bedrock; a PENDING record left by a failed attempt is finished. Returns "started" or "duplicate"."""
    raise NotImplementedError



def handler(event: dict, context: Any = None, table: Any = None, agent: Any = None) -> dict:
    """TODO: per-record processing; return {"batchItemFailures": [...]} with only the records that should be redelivered. Poison messages are logged and recorded under pk POISON, sk MSG#<messageId>, and NOT redelivered."""
    raise NotImplementedError
