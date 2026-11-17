"""Fixtures for x-1: a moto DynamoDB table with tenant profiles, a Stubber-backed bedrock-agent client,
and S3 Object Created events wrapped the way EventBridge delivers them to SQS."""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import sys

import boto3
import pytest
from botocore.stub import Stubber
from moto import mock_aws

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

BUCKET = "tidewater-kb-docs-111122223333"


def s3_event(key: str, seq: str = "617f08299329d189", etag: str = "b1946ac92492d2347c6235b4d2611184",
             bucket: str = BUCKET) -> dict:
    return {"version": "0", "id": f"ev-{seq}", "detail-type": "Object Created", "source": "aws.s3",
            "account": "111122223333", "time": "2026-11-13T10:00:00Z", "region": "us-east-1",
            "resources": [f"arn:aws:s3:::{bucket}"],
            "detail": {"version": "0", "bucket": {"name": bucket},
                       "object": {"key": key, "size": 18234, "etag": etag, "sequencer": seq},
                       "request-id": "N4N7GDK58NMKJ12R", "requester": "111122223333", "reason": "PutObject"}}


def sqs_record(mid: str, body, receive_count: int = 1) -> dict:
    return {"messageId": mid, "receiptHandle": f"rh-{mid}",
            "body": body if isinstance(body, str) else json.dumps(body),
            "attributes": {"ApproximateReceiveCount": str(receive_count), "SentTimestamp": "1763028000000"},
            "messageAttributes": {}, "eventSource": "aws:sqs",
            "eventSourceARN": "arn:aws:sqs:us-east-1:111122223333:tw-ingest", "awsRegion": "us-east-1"}


def batch(*records) -> dict:
    return {"Records": list(records)}


def job_response(job_id: str = "IJOB000001", kb: str = "KBACME0001", ds: str = "DSACME0001") -> dict:
    now = dt.datetime(2026, 11, 13, 10, 0, tzinfo=dt.timezone.utc)
    return {"ingestionJob": {"knowledgeBaseId": kb, "dataSourceId": ds, "ingestionJobId": job_id,
                             "status": "STARTING", "startedAt": now, "updatedAt": now}}


@pytest.fixture
def table():
    with mock_aws():
        t = boto3.resource("dynamodb", region_name="us-east-1").create_table(
            TableName="tidewater-ops",
            KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}, {"AttributeName": "sk", "KeyType": "RANGE"}],
            AttributeDefinitions=[{"AttributeName": "pk", "AttributeType": "S"}, {"AttributeName": "sk", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST")
        t.put_item(Item={"pk": "TENANT#acme-foods", "sk": "PROFILE", "status": "active",
                         "knowledge_base_id": "KBACME0001", "data_source_id": "DSACME0001"})
        t.put_item(Item={"pk": "TENANT#corvid-logistics", "sk": "PROFILE", "status": "active",
                         "knowledge_base_id": "KBCORVID01", "data_source_id": "DSCORVID01"})
        t.put_item(Item={"pk": "TENANT#old-tenant", "sk": "PROFILE", "status": "offboarded",
                         "knowledge_base_id": "KBOLD00001", "data_source_id": "DSOLD00001"})
        yield t


class Agent:
    def __init__(self) -> None:
        self.client = boto3.client("bedrock-agent", region_name="us-east-1")
        self.stub = Stubber(self.client)


@pytest.fixture
def agent():
    a = Agent()
    with a.stub:
        yield a


def jobs(table) -> list[dict]:
    return [i for i in table.scan()["Items"] if i["sk"].startswith("INGEST#")]
