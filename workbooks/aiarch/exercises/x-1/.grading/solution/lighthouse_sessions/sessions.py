"""Lighthouse runtime session registry (table lighthouse-sessions, on-demand).

Fix (INC-20470): the GSI used to be keyed on status="ACTIVE", one partition key value for every
open session, so all index writes landed on one GSI partition (about 1,000 WCU per partition).
At the 09:00 login wave the GSI throttled and, because GSI throttling back-pressures the base
table, session writes failed even though the table is on-demand. The index key is now
write-sharded (ACTIVE#0..ACTIVE#9 from a stable hash of the session id) and sparse: closing a
session removes the index attributes, so the index holds only active sessions.
"""
from __future__ import annotations

import hashlib

from boto3.dynamodb.conditions import Key

TABLE = "lighthouse-sessions"
INDEX = "by-status"
SHARDS = 10
SESSION_TTL_SECONDS = 8 * 3600


def shard_key(session_id: str) -> str:
    n = int(hashlib.sha256(session_id.encode()).hexdigest(), 16) % SHARDS
    return f"ACTIVE#{n}"


def create_table(dynamodb):
    t = dynamodb.create_table(
        TableName=TABLE, BillingMode="PAY_PER_REQUEST",
        KeySchema=[{"AttributeName": "session_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": n, "AttributeType": "S"} for n in ("session_id", "active_shard", "started")],
        GlobalSecondaryIndexes=[{"IndexName": INDEX, "KeySchema": [
            {"AttributeName": "active_shard", "KeyType": "HASH"}, {"AttributeName": "started", "KeyType": "RANGE"}],
            "Projection": {"ProjectionType": "KEYS_ONLY"}}],
    )
    t.wait_until_exists()
    dynamodb.meta.client.update_time_to_live(TableName=TABLE, TimeToLiveSpecification={"Enabled": True, "AttributeName": "ttl"})
    return t


def open_session(table, session_id: str, user: str, started_iso: str, now: float) -> dict:
    item = {"session_id": session_id, "user": user, "started": started_iso, "status": "ACTIVE",
            "active_shard": shard_key(session_id), "ttl": int(now) + SESSION_TTL_SECONDS}
    table.put_item(Item=item)
    return item


def close_session(table, session_id: str) -> None:
    table.update_item(Key={"session_id": session_id}, UpdateExpression="SET #s = :c REMOVE active_shard",
                      ExpressionAttributeNames={"#s": "status"}, ExpressionAttributeValues={":c": "CLOSED"})


def list_active(table) -> list[str]:
    out: list[str] = []
    for n in range(SHARDS):
        kw: dict = {}
        while True:
            r = table.query(IndexName=INDEX, KeyConditionExpression=Key("active_shard").eq(f"ACTIVE#{n}"), **kw)
            out += [i["session_id"] for i in r["Items"]]
            if "LastEvaluatedKey" not in r:
                break
            kw["ExclusiveStartKey"] = r["LastEvaluatedKey"]
    return out
