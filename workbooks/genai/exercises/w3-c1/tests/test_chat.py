import json

from assistant.llm import text, tool_use
from conftest import ana


def test_search_then_answer(make):
    c, llm, store, _, _ = make([
        tool_use("search_products", {"query": "tent"}),
        text("The Ridgeline 2P Tent is $249.00."),
    ])
    r = ana(c, "do you have a two person tent?")
    assert r.status_code == 200
    assert r.json()["reply"] == "The Ridgeline 2P Tent is $249.00."
    results = llm.last_tool_results()
    assert results and results[0]["is_error"] is False
    assert json.loads(results[0]["content"])["results"][0]["sku"] == "KO-TENT-2P"


def test_conversation_id_is_returned_and_reused(make):
    c, llm, _, _, _ = make([text("Hi!"), text("Still here.")])
    cid = ana(c, "hello").json()["conversation_id"]
    r = ana(c, "again", cid)
    assert r.json()["conversation_id"] == cid
    assert len(llm.calls[-1]["messages"]) == 3  # user, assistant, user
