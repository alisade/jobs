"""Fixtures for w4-c1: a moto DynamoDB table with two GSIs, seeded for two tenants."""

from __future__ import annotations

import json
import pathlib
import sys

import boto3
import pytest
from moto import mock_aws

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

TICKETS = [
    ("acme-foods", "TK-0000A001", "open", "2026-11-10T09:00:00Z", "Pallet damaged at Denver dock", "SH-10001"),
    ("acme-foods", "TK-0000A002", "open", "2026-11-12T14:30:00Z", "Reefer temperature alarm", "SH-10003"),
    ("acme-foods", "TK-0000A003", "closed", "2026-11-01T08:00:00Z", "Invoice dispute", None),
    ("brightline-health", "TK-0000B001", "open", "2026-11-11T10:00:00Z", "Customs hold Buffalo", "SH-20001"),
]


def make_table():
    from tickets.keys import ticket_item
    ddb = boto3.resource("dynamodb", region_name="us-east-1")
    t = ddb.create_table(
        TableName="tidewater-ops",
        KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}, {"AttributeName": "sk", "KeyType": "RANGE"}],
        AttributeDefinitions=[{"AttributeName": n, "AttributeType": "S"} for n in
                              ("pk", "sk", "gsi1pk", "gsi1sk", "gsi2pk", "gsi2sk")],
        GlobalSecondaryIndexes=[
            {"IndexName": "gsi1", "KeySchema": [{"AttributeName": "gsi1pk", "KeyType": "HASH"},
                                                {"AttributeName": "gsi1sk", "KeyType": "RANGE"}],
             "Projection": {"ProjectionType": "ALL"}},
            {"IndexName": "gsi2", "KeySchema": [{"AttributeName": "gsi2pk", "KeyType": "HASH"},
                                                {"AttributeName": "gsi2sk", "KeyType": "RANGE"}],
             "Projection": {"ProjectionType": "ALL"}},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    for tenant, tid, status, created, summary, ship in TICKETS:
        t.put_item(Item=ticket_item(tenant, tid, status, created, summary, ship))
    t.put_item(Item={"pk": "USER#u-acme-1", "sk": "TENANT", "tenant_id": "acme-foods"})
    t.put_item(Item={"pk": "USER#u-bl-1", "sk": "TENANT", "tenant_id": "brightline-health"})
    return t


def http_event(route: str, tenant: str | None = "acme-foods", path: dict | None = None,
               qs: dict | None = None, body: dict | str | None = None) -> dict:
    claims = {"sub": "u-acme-1", "token_use": "access", "client_id": "5abc"}
    if tenant is not None:
        claims["tenant_id"] = tenant
    ev = {"version": "2.0", "routeKey": route, "rawPath": route.split(" ", 1)[1],
          "requestContext": {"authorizer": {"jwt": {"claims": claims, "scopes": ["tickets/read"]}},
                             "http": {"method": route.split(" ")[0]}}}
    if path is not None:
        ev["pathParameters"] = path
    if qs is not None:
        ev["queryStringParameters"] = qs
    if body is not None:
        ev["body"] = body if isinstance(body, str) else json.dumps(body)
    return ev


def pretoken_event(sub: str, version: str = "2") -> dict:
    return {"version": version, "triggerSource": "TokenGeneration_Authentication", "region": "us-east-1",
            "userPoolId": "us-east-1_TideW8ter", "userName": sub,
            "callerContext": {"awsSdkVersion": "aws-sdk-unknown-unknown", "clientId": "5abc"},
            "request": {"userAttributes": {"sub": sub, "email": f"{sub}@example.com"},
                        "groupConfiguration": {"groupsToOverride": [], "iamRolesToOverride": [], "preferredRole": None},
                        "scopes": ["openid", "tickets/read"]},
            "response": {"claimsAndScopeOverrideDetails": None}}


def body(resp: dict) -> dict:
    return json.loads(resp["body"])


@pytest.fixture
def table():
    with mock_aws():
        yield make_table()
