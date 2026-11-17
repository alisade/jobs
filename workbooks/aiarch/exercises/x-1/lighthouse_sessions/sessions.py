"""Lighthouse runtime session registry (table lighthouse-sessions, on-demand).

The drain runbook and the AgentOps dashboard need "all ACTIVE sessions"; that query goes
through the GSI ``by-status``. Sessions expire through TTL (``ttl``, epoch seconds).
"""
from __future__ import annotations

from boto3.dynamodb.conditions import Key

TABLE = "lighthouse-sessions"
INDEX = "by-status"
SESSION_TTL_SECONDS = 8 * 3600


def create_table(dynamodb):
    t = dynamodb.create_table(
        TableName=TABLE, BillingMode="PAY_PER_REQUEST",
        KeySchema=[{"AttributeName": "session_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": n, "AttributeType": "S"} for n in ("session_id", "status", "started")],
        GlobalSecondaryIndexes=[{"IndexName": INDEX, "KeySchema": [
            {"AttributeName": "status", "KeyType": "HASH"}, {"AttributeName": "started", "KeyType": "RANGE"}],
            "Projection": {"ProjectionType": "KEYS_ONLY"}}],
    )
    t.wait_until_exists()
    dynamodb.meta.client.update_time_to_live(TableName=TABLE, TimeToLiveSpecification={"Enabled": True, "AttributeName": "ttl"})
    return t


def open_session(table, session_id: str, user: str, started_iso: str, now: float) -> dict:
    item = {"session_id": session_id, "user": user, "started": started_iso, "status": "ACTIVE",
            "ttl": int(now) + SESSION_TTL_SECONDS}
    table.put_item(Item=item)
    return item


def close_session(table, session_id: str) -> None:
    table.update_item(Key={"session_id": session_id}, UpdateExpression="SET #s = :c",
                      ExpressionAttributeNames={"#s": "status"}, ExpressionAttributeValues={":c": "CLOSED"})


def list_active(table) -> list[str]:
    out, kw = [], {}
    while True:
        r = table.query(IndexName=INDEX, KeyConditionExpression=Key("status").eq("ACTIVE"), **kw)
        out += [i["session_id"] for i in r["Items"]]
        if "LastEvaluatedKey" not in r:
            return out
        kw["ExclusiveStartKey"] = r["LastEvaluatedKey"]
