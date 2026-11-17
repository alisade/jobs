"""Visible checks for w3-t1. The grader runs more."""

from ask_service.answer import answer
from kb_sim.kb import KnowledgeBase


def test_established_tenant_still_answers():
    a = answer(KnowledgeBase(), "acme-foods", "What temperature must reefer trailers hold?")
    assert a.grounded and all(c["tenant_id"] == "acme-foods" for c in a.citations)


def test_delta_never_cites_another_tenant():
    kb = KnowledgeBase()
    for q in ["What is the return window for a kayak bought in store?",
              "How do I file a damage claim for a tent that arrived damaged?"]:
        a = answer(kb, "delta-outfitters", q)
        assert all(c["tenant_id"] == "delta-outfitters" for c in a.citations), a.citations
