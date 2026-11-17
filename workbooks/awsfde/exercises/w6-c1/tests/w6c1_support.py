"""Fixtures for w6-c1: a real quicksight client with a Stubber, and HTTP API events."""

from __future__ import annotations

import json
import pathlib
import sys

import boto3
import pytest
from botocore.stub import Stubber

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

URL = "https://us-east-1.quicksight.aws.amazon.com/embed/abc123/dashboards/dash?code=SECRETCODE&identityprovider=quicksight"


def event(tenant: str | None = "acme-foods", user: str | None = "maria.lopez", dashboard: str | None = None) -> dict:
    claims = {"sub": "u-1", "token_use": "access"}
    if tenant:
        claims["tenant_id"] = tenant
    if user:
        claims["username"] = user
    ev = {"version": "2.0", "routeKey": "GET /analytics/embed-url",
          "requestContext": {"authorizer": {"jwt": {"claims": claims, "scopes": []}}}}
    if dashboard:
        ev["queryStringParameters"] = {"dashboard": dashboard}
    return ev


def ok_registered() -> dict:
    return {"EmbedUrl": URL, "Status": 200, "RequestId": "rq-1"}


def ok_anonymous() -> dict:
    return {"EmbedUrl": URL, "Status": 200, "RequestId": "rq-2",
            "AnonymousUserArn": "arn:aws:quicksight:us-east-1:111122223333:user/default/anon"}


def body(r: dict) -> dict:
    return json.loads(r["body"])


class QS:
    def __init__(self) -> None:
        self.client = boto3.client("quicksight", region_name="us-east-1")
        self.stub = Stubber(self.client)


@pytest.fixture
def qs():
    q = QS()
    with q.stub:
        yield q
