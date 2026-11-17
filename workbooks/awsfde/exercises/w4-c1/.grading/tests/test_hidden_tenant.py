"""Hidden checks for w4-c1: cross-tenant attacks, fail-closed paths, key design, IAM policy."""

from __future__ import annotations

import json

import boto3
import pytest
from botocore.stub import Stubber
from boto3.dynamodb.conditions import Key
from w4c1_hidden_support import body, http_event, pretoken_event

from tickets.handler import handler
from tickets.keys import shipment_gsi_pk, status_gsi_pk, ticket_item, ticket_key
from tickets.policy import tenant_session, tool_role_policy
from tickets.pretoken import TenantMappingError
from tickets.pretoken import handler as pretoken

BL = "TK-0000B001"


def test_attack_forged_path_parameter(table):
    r = handler(http_event("GET /tickets/{ticket_id}", path={"ticket_id": BL, "tenant_id": "brightline-health"}), table=table)
    assert r["statusCode"] == 404 and "Customs" not in r["body"]


def test_attack_forged_body(table):
    r = handler(http_event("POST /tools/get_ticket", body={"ticket_id": BL, "tenant_id": "brightline-health"}), table=table)
    assert r["statusCode"] == 404 and "Customs" not in r["body"]


def test_attack_prompt_injected_tool_argument(table):
    r = handler(http_event("POST /tools/get_ticket",
                           body={"ticket_id": BL, "tenant": "brightline-health", "tenantId": "brightline-health"}), table=table)
    assert r["statusCode"] == 404


def test_attack_query_string_tenant_on_list(table):
    r = handler(http_event("GET /tickets", qs={"status": "open", "tenant_id": "brightline-health"}), table=table)
    assert r["statusCode"] == 200
    assert {t["ticket_id"] for t in body(r)["tickets"]} == {"TK-0000A001", "TK-0000A002"}


def test_forged_tenant_is_logged(table, caplog):
    with caplog.at_level("WARNING"):
        handler(http_event("POST /tools/get_ticket", body={"ticket_id": BL, "tenant_id": "brightline-health"}), table=table)
    assert "brightline-health" in caplog.text


def test_no_tenant_claim_is_403(table):
    r = handler(http_event("GET /tickets/{ticket_id}", tenant=None, path={"ticket_id": "TK-0000A001"}), table=table)
    assert r["statusCode"] == 403


def test_brightline_token_reads_its_own(table):
    r = handler(http_event("GET /tickets/{ticket_id}", tenant="brightline-health", path={"ticket_id": BL}), table=table)
    assert r["statusCode"] == 200


def test_bad_inputs_are_400(table):
    assert handler(http_event("GET /tickets/{ticket_id}", path={"ticket_id": "../../x"}), table=table)["statusCode"] == 400
    assert handler(http_event("GET /tickets", qs={"status": "everything"}), table=table)["statusCode"] == 400
    assert handler(http_event("POST /tools/get_ticket", body="not json"), table=table)["statusCode"] == 400


def test_responses_do_not_echo_keys_or_tenant(table):
    r = handler(http_event("GET /tickets/{ticket_id}", path={"ticket_id": "TK-0000A001"}), table=table)
    assert not {"pk", "sk", "gsi1pk", "gsi1sk", "tenant_id"} & set(body(r))


def test_ticket_item_supports_all_access_patterns(table):
    it = ticket_item("corvid-logistics", "TK-0000C001", "pending", "2026-11-13T00:00:00Z", "Late pickup", "SH-30001")
    assert it["pk"] == "TENANT#corvid-logistics" and it["sk"] == "TICKET#TK-0000C001"
    assert it["gsi1pk"] == status_gsi_pk("corvid-logistics", "pending")
    assert it["gsi2pk"] == shipment_gsi_pk("corvid-logistics", "SH-30001")
    table.put_item(Item=it)
    r = table.query(IndexName="gsi2", KeyConditionExpression=Key("gsi2pk").eq(shipment_gsi_pk("corvid-logistics", "SH-30001")))
    assert [i["ticket_id"] for i in r["Items"]] == ["TK-0000C001"]


def test_every_partition_key_is_tenant_prefixed():
    it = ticket_item("acme-foods", "TK-0000A009", "open", "2026-11-13T00:00:00Z", "x", "SH-10009")
    for k in ("pk", "gsi1pk", "gsi2pk"):
        assert it[k] == "TENANT#acme-foods" or it[k].startswith("TENANT#acme-foods#")


@pytest.mark.parametrize("bad", ["", "ACME", "acme foods", "acme#foods", "x" * 80])
def test_invalid_tenant_ids_rejected(bad):
    with pytest.raises(ValueError):
        ticket_key(bad, "TK-0000A001")


def test_pretoken_unmapped_user_fails_closed(table):
    with pytest.raises(TenantMappingError):
        pretoken(pretoken_event("u-nobody"), None, table=table)


def test_pretoken_v1_event_rejected(table):
    with pytest.raises(TenantMappingError):
        pretoken(pretoken_event("u-acme-1", version="1"), None, table=table)


def test_pretoken_ignores_client_supplied_attribute(table):
    ev = pretoken_event("u-bl-1")
    ev["request"]["userAttributes"]["custom:tenant_id"] = "acme-foods"
    out = pretoken(ev, None, table=table)["response"]["claimsAndScopeOverrideDetails"]
    assert out["accessTokenGeneration"]["claimsToAddOrOverride"]["tenant_id"] == "brightline-health"


ARN = "arn:aws:dynamodb:us-east-1:111122223333:table/tidewater-ops"


def _stmts(doc):
    return [s for s in doc["Statement"] if s["Effect"] == "Allow"]


def test_policy_uses_leading_keys_with_session_tag():
    doc = tool_role_policy(ARN)
    assert "dynamodb:LeadingKeys" in json.dumps(doc) and "${aws:PrincipalTag/tenant_id}" in json.dumps(doc)
    for s in _stmts(doc):
        lk = [op for op, v in s.get("Condition", {}).items() if "dynamodb:LeadingKeys" in v]
        assert lk and all(op.startswith("ForAllValues:") for op in lk), "LeadingKeys needs ForAllValues"


def test_policy_has_no_scan_or_writes_or_wildcards():
    doc = tool_role_policy(ARN)
    actions = [a for s in _stmts(doc) for a in (s["Action"] if isinstance(s["Action"], list) else [s["Action"]])]
    assert "dynamodb:Scan" not in actions and not any(a.endswith("*") for a in actions)
    assert not any(a in actions for a in ("dynamodb:PutItem", "dynamodb:DeleteItem", "dynamodb:UpdateItem"))
    res = [r for s in _stmts(doc) for r in (s["Resource"] if isinstance(s["Resource"], list) else [s["Resource"]])]
    assert "*" not in res and ARN in res and f"{ARN}/index/*" in res


def test_tenant_session_passes_session_tag():
    sts = boto3.client("sts", region_name="us-east-1")
    with Stubber(sts) as st:
        st.add_response("assume_role", {
            "Credentials": {"AccessKeyId": "ASIAEXAMPLE000000000", "SecretAccessKey": "s" * 40,
                            "SessionToken": "t" * 40, "Expiration": "2026-11-13T12:00:00Z"},
            "AssumedRoleUser": {"AssumedRoleId": "AROAEXAMPLE:ticket-tool-r1",
                                "Arn": "arn:aws:sts::111122223333:assumed-role/ticket-tool/ticket-tool-r1"}},
            {"RoleArn": "arn:aws:iam::111122223333:role/ticket-tool", "RoleSessionName": "ticket-tool-r1",
             "Tags": [{"Key": "tenant_id", "Value": "acme-foods"}], "DurationSeconds": 900})
        creds = tenant_session(sts, "arn:aws:iam::111122223333:role/ticket-tool", "acme-foods", "r1")
    assert creds["AccessKeyId"] == "ASIAEXAMPLE000000000"
