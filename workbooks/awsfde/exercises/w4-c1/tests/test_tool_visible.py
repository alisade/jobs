"""Visible checks for w4-c1 (happy paths). The grader runs more."""

from w4c1_support import body, http_event, pretoken_event

from tickets.handler import handler
from tickets.pretoken import handler as pretoken


def test_get_own_ticket(table):
    r = handler(http_event("GET /tickets/{ticket_id}", path={"ticket_id": "TK-0000A001"}), table=table)
    assert r["statusCode"] == 200 and body(r)["summary"] == "Pallet damaged at Denver dock"


def test_list_open_newest_first(table):
    r = handler(http_event("GET /tickets", qs={"status": "open"}), table=table)
    assert [t["ticket_id"] for t in body(r)["tickets"]] == ["TK-0000A002", "TK-0000A001"]


def test_pretoken_adds_claim_to_both_tokens(table):
    ev = pretoken(pretoken_event("u-acme-1"), None, table=table)
    d = ev["response"]["claimsAndScopeOverrideDetails"]
    assert d["idTokenGeneration"]["claimsToAddOrOverride"]["tenant_id"] == "acme-foods"
    assert d["accessTokenGeneration"]["claimsToAddOrOverride"]["tenant_id"] == "acme-foods"
