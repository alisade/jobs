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

import datetime as dt  # noqa: F401
from decimal import Decimal  # noqa: F401
from typing import Callable

from boto3.dynamodb.conditions import Key  # noqa: F401
from botocore.exceptions import ClientError  # noqa: F401

TABLE = "lighthouse-state"
SESSION_TTL_DAYS = 30


class InProgress(Exception):
    pass


class Conflict(Exception):
    pass


def create_table(dynamodb):
    """dynamodb: a boto3 DynamoDB resource. TODO: add what the access patterns need (at most two GSIs) and TTL."""
    t = dynamodb.create_table(
        TableName=TABLE, BillingMode="PAY_PER_REQUEST",
        KeySchema=[{"AttributeName": "PK", "KeyType": "HASH"}, {"AttributeName": "SK", "KeyType": "RANGE"}],
        AttributeDefinitions=[{"AttributeName": "PK", "AttributeType": "S"}, {"AttributeName": "SK", "AttributeType": "S"}],
    )
    t.wait_until_exists()
    return t


def start_session(table, user: str, agent: str, session_id: str, now: float) -> dict:
    raise NotImplementedError("TODO")


def recent_sessions(table, user: str, now: float, days: int = 7) -> list[dict]:
    raise NotImplementedError("TODO")


def get_session(table, session_id: str) -> dict | None:
    raise NotImplementedError("TODO")


def run_once(table, key: str, fn: Callable[[], dict], now: float, ttl_seconds: int = 86400) -> dict:
    raise NotImplementedError("TODO")


def record_usage(table, span: dict, prices: dict) -> int:
    raise NotImplementedError("TODO")


def daily_cost(table, agent: str, start: str, end: str) -> list[tuple[str, float]]:
    raise NotImplementedError("TODO")


def cost_for_day(table, day: str) -> dict[str, float]:
    raise NotImplementedError("TODO")


def create_approval(table, request_id: str) -> None:
    raise NotImplementedError("TODO")


def decide(table, request_id: str, decision: str, approver: str, expected_version: int) -> int:
    raise NotImplementedError("TODO")
