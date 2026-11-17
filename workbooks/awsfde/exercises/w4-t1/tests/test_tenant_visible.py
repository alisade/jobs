"""Visible checks for w4-t1. The grader runs more."""

import json
import pathlib

from cognito_sim.pool import issue_tokens, jwt_authorizer, spa_token
from tenant_api import pretoken
from tenant_api.handler import handler

USERS = {u["username"]: u for u in json.loads(
    (pathlib.Path(__file__).resolve().parent.parent / "data" / "users.json").read_text())}


def call(username):
    tokens = issue_tokens(USERS[username], pretoken.handler)
    r = handler(jwt_authorizer(spa_token(tokens)))
    return r["statusCode"], json.loads(r["body"])


def test_acme_user_sees_acme():
    code, body = call("maria.ortiz")
    assert code == 200 and body["tenant_id"] == "acme-foods"


def test_brightline_user_sees_brightline():
    code, body = call("brightline-saml_jlee@brightline.example")
    assert code == 200 and body["tenant_id"] == "brightline-health"
