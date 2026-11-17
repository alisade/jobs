"""Visible checks. They pass on the broken flow too: the bug is in behaviour, not syntax."""
from flowsim.engine import validate_graph


def test_definition_shape(flow, definition):
    assert flow["properties"]["connectionReferences"], "connection references must stay"
    assert "When_a_PO_is_approved" in definition["triggers"]
    assert {"Try", "Catch"} <= set(definition["actions"])


def test_run_after_graph_is_valid(definition):
    assert validate_graph(definition["actions"]) == []


def test_send_still_inside_try(definition):
    assert "Send_to_Contoso_Parts" in definition["actions"]["Try"]["actions"]
