"""Lighthouse platform state in one DynamoDB table.

Access patterns -> keys:
  1 sessions for a user in the last N days     PK=USER#<user>        SK=SESSION#<iso start>#<id>
  2 one session by id                          GSI1PK=SESSION#<id>   GSI1SK=META
  3 has this tool side effect already run      PK=IDEMP#<key>        SK=IDEMP
  4 cost for one agent by day                  PK=COST#<agent>       SK=DAY#<yyyy-mm-dd>
  5 cost for all agents on one day             GSI1PK=DAY#<day>      GSI1SK=AGENT#<agent>
  6 approval state with optimistic locking     PK=APPROVAL#<id>      SK=STATE
Sessions expire through TTL (attribute ``ttl``, epoch seconds). Money is stored as integer
micro-dollars so ADD stays exact.
"""
from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Callable

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

TABLE = "lighthouse-state"
SESSION_TTL_DAYS = 30


class InProgress(Exception):
    pass


class Conflict(Exception):
    pass


def create_table(dynamodb):
    """dynamodb: a boto3 DynamoDB resource. On-demand, TTL on ``ttl``, one GSI (GSI1)."""
    t = dynamodb.create_table(
        TableName=TABLE, BillingMode="PAY_PER_REQUEST",
        KeySchema=[{"AttributeName": "PK", "KeyType": "HASH"}, {"AttributeName": "SK", "KeyType": "RANGE"}],
        AttributeDefinitions=[{"AttributeName": n, "AttributeType": "S"} for n in ("PK", "SK", "GSI1PK", "GSI1SK")],
        GlobalSecondaryIndexes=[{"IndexName": "GSI1", "KeySchema": [
            {"AttributeName": "GSI1PK", "KeyType": "HASH"}, {"AttributeName": "GSI1SK", "KeyType": "RANGE"}],
            "Projection": {"ProjectionType": "ALL"}}],
    )
    t.wait_until_exists()
    dynamodb.meta.client.update_time_to_live(TableName=TABLE, TimeToLiveSpecification={"Enabled": True, "AttributeName": "ttl"})
    return t


def _iso(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def start_session(table, user: str, agent: str, session_id: str, now: float) -> dict:
    item = {"PK": f"USER#{user}", "SK": f"SESSION#{_iso(now)}#{session_id}", "GSI1PK": f"SESSION#{session_id}",
            "GSI1SK": "META", "user": user, "agent": agent, "session_id": session_id, "started": _iso(now),
            "ttl": int(now) + SESSION_TTL_DAYS * 86400}
    table.put_item(Item=item, ConditionExpression="attribute_not_exists(PK)")
    return item


def recent_sessions(table, user: str, now: float, days: int = 7) -> list[dict]:
    lo = f"SESSION#{_iso(now - days * 86400)}"
    hi = f"SESSION#{_iso(now)}#~"
    r = table.query(KeyConditionExpression=Key("PK").eq(f"USER#{user}") & Key("SK").between(lo, hi), ScanIndexForward=False)
    return r["Items"]


def get_session(table, session_id: str) -> dict | None:
    r = table.query(IndexName="GSI1", KeyConditionExpression=Key("GSI1PK").eq(f"SESSION#{session_id}") & Key("GSI1SK").eq("META"))
    return r["Items"][0] if r["Items"] else None


def run_once(table, key: str, fn: Callable[[], dict], now: float, ttl_seconds: int = 86400) -> dict:
    pk = {"PK": f"IDEMP#{key}", "SK": "IDEMP"}
    try:
        table.put_item(Item={**pk, "status": "PENDING", "ttl": int(now) + ttl_seconds},
                       ConditionExpression="attribute_not_exists(PK)")
    except ClientError as e:
        if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
            raise
        prev = table.get_item(Key=pk, ConsistentRead=True).get("Item", {})
        if prev.get("status") == "DONE":
            return prev["result"]
        raise InProgress(f"side effect {key} is already running") from e
    try:
        result = fn()
    except Exception:
        table.delete_item(Key=pk)
        raise
    table.update_item(Key=pk, UpdateExpression="SET #s = :d, #r = :r",
                      ExpressionAttributeNames={"#s": "status", "#r": "result"},
                      ExpressionAttributeValues={":d": "DONE", ":r": result})
    return result


def _micros(tokens: int, per_million_usd: str) -> int:
    return int((Decimal(tokens) * Decimal(per_million_usd)).to_integral_value())


def record_usage(table, span: dict, prices: dict) -> int:
    a = span["attributes"]
    model = a["gen_ai.request.model"]
    if model not in prices:
        raise KeyError(f"no price for model {model}")
    p = prices[model]
    inp, out = int(a.get("gen_ai.usage.input_tokens", 0)), int(a.get("gen_ai.usage.output_tokens", 0))
    cache_read = int(a.get("gen_ai.usage.cache_read_input_tokens", 0))
    cost = _micros(inp, p["input"]) + _micros(out, p["output"]) + _micros(cache_read, p.get("cache_read", p["input"]))
    day = span["start_time"][:10]
    agent = a["gen_ai.agent.name"]
    names = {"#gpk": "GSI1PK", "#gsk": "GSI1SK", "#agent": "agent", "#day": "day", "#in": "input_tokens",
             "#out": "output_tokens", "#cr": "cache_read_tokens", "#cost": "cost_micro_usd", "#calls": "calls"}
    table.update_item(
        Key={"PK": f"COST#{agent}", "SK": f"DAY#{day}"},
        UpdateExpression="SET #gpk = :g, #gsk = :a, #agent = :n, #day = :day "
                         "ADD #in :i, #out :o, #cr :c, #cost :m, #calls :one",
        ExpressionAttributeNames=names,
        ExpressionAttributeValues={":g": f"DAY#{day}", ":a": f"AGENT#{agent}", ":n": agent, ":day": day,
                                   ":i": inp, ":o": out, ":c": cache_read, ":m": cost, ":one": 1},
    )
    return cost


def daily_cost(table, agent: str, start: str, end: str) -> list[tuple[str, float]]:
    r = table.query(KeyConditionExpression=Key("PK").eq(f"COST#{agent}") & Key("SK").between(f"DAY#{start}", f"DAY#{end}"))
    return [(i["day"], int(i["cost_micro_usd"]) / 1e6) for i in r["Items"]]


def cost_for_day(table, day: str) -> dict[str, float]:
    r = table.query(IndexName="GSI1", KeyConditionExpression=Key("GSI1PK").eq(f"DAY#{day}"))
    return {i["agent"]: int(i["cost_micro_usd"]) / 1e6 for i in r["Items"]}


def create_approval(table, request_id: str) -> None:
    table.put_item(Item={"PK": f"APPROVAL#{request_id}", "SK": "STATE", "state": "PENDING", "version": 1},
                   ConditionExpression="attribute_not_exists(PK)")


def decide(table, request_id: str, decision: str, approver: str, expected_version: int) -> int:
    try:
        r = table.update_item(
            Key={"PK": f"APPROVAL#{request_id}", "SK": "STATE"},
            UpdateExpression="SET #s = :s, #ap = :a, #v = #v + :one",
            ConditionExpression="#v = :v AND #s = :pending",
            ExpressionAttributeNames={"#s": "state", "#ap": "approver", "#v": "version"},
            ExpressionAttributeValues={":s": decision, ":a": approver, ":one": 1, ":v": expected_version, ":pending": "PENDING"},
            ReturnValues="UPDATED_NEW")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise Conflict(f"{request_id} changed since version {expected_version}") from e
        raise
    return int(r["Attributes"]["version"])
