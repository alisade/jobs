"""Hidden checks for w3-t1: no unfiltered Retrieve, thin tenants get a no-answer, guards."""

from __future__ import annotations

import json
import pathlib

from ask_service.answer import NO_ANSWER, answer
from ask_service.retrieval import MIN_SCORE, retrieve_context
from kb_sim.kb import KnowledgeBase, _match

ROOT = pathlib.Path(__file__).resolve().parent.parent
QUESTIONS = [json.loads(x) for x in (ROOT / "evidence" / "questions.jsonl").read_text().splitlines()]
TENANTS = ["acme-foods", "brightline-health", "corvid-logistics", "delta-outfitters"]


def _replay():
    kb = KnowledgeBase()
    out = [(q, answer(kb, q["tenant_id"], q["question"])) for q in QUESTIONS]
    return kb, out


def test_every_retrieve_call_is_scoped_to_the_caller():
    kb = KnowledgeBase()
    for q in QUESTIONS:
        before = len(kb.calls)
        answer(kb, q["tenant_id"], q["question"])
        for call in kb.calls[before:]:
            flt = call["retrievalConfiguration"]["vectorSearchConfiguration"].get("filter")
            assert flt is not None, "a Retrieve call without a filter"
            for other in TENANTS:
                assert _match(flt, {"tenant_id": other}) == (other == q["tenant_id"]), flt


def test_one_retrieve_per_question():
    kb, _ = _replay()
    assert len(kb.calls) == len(QUESTIONS)


def test_no_foreign_citations_anywhere():
    _, out = _replay()
    for q, a in out:
        assert all(c["tenant_id"] == q["tenant_id"] for c in a.citations), (q, a.citations)


def test_thin_tenant_gets_a_no_answer():
    kb = KnowledgeBase()
    for q in ["What is the return window for a kayak bought in store?",
              "How do I file a damage claim for a tent that arrived damaged?",
              "Can I return refrigerated items?"]:
        a = answer(kb, "delta-outfitters", q)
        assert not a.grounded and a.text == NO_ANSWER and a.citations == []


class ForeignKB:
    """A KB that returns a mis-tagged chunk with a high score (e.g. a bad metadata sidecar)."""

    def __init__(self):
        self.calls = []

    def retrieve(self, **p):
        self.calls.append(p)
        return {"retrievalResults": [
            {"content": {"type": "TEXT", "text": "Acme internal pricing sheet"},
             "location": {"type": "S3", "s3Location": {"uri": "s3://b/tenants/acme-foods/docs/pricing.pdf"}},
             "metadata": {"tenant_id": "acme-foods"}, "score": 0.97},
            {"content": {"type": "TEXT", "text": "untagged"},
             "location": {"type": "S3", "s3Location": {"uri": "s3://b/tenants/x/docs/u.pdf"}},
             "metadata": {}, "score": 0.95},
            {"content": {"type": "TEXT", "text": "Delta gift cards never expire."},
             "location": {"type": "S3", "s3Location": {"uri": "s3://b/tenants/delta-outfitters/docs/gift-cards.pdf"}},
             "metadata": {"tenant_id": "delta-outfitters"}, "score": 0.6}]}


def test_defense_in_depth_drops_foreign_and_untagged_chunks():
    got = retrieve_context(ForeignKB(), "delta-outfitters", "gift cards?")
    assert [r["metadata"].get("tenant_id") for r in got] == ["delta-outfitters"]


def test_guard_established_tenants_unchanged():
    _, out = _replay()
    for q, a in out:
        if q["tenant_id"] != "delta-outfitters":
            assert a.grounded, q


def test_guard_delta_answers_what_it_has():
    kb = KnowledgeBase()
    a = answer(kb, "delta-outfitters", "How many loyalty points do members earn per dollar on kayaks?")
    assert a.grounded and "2 points" in a.text
    assert answer(kb, "delta-outfitters", "Do gift cards expire?").grounded


def test_guard_score_floor_kept():
    class Weak:
        def retrieve(self, **p):
            return {"retrievalResults": [{"content": {"type": "TEXT", "text": "x"},
                                          "location": {"type": "S3", "s3Location": {"uri": "s3://b/d.pdf"}},
                                          "metadata": {"tenant_id": "acme-foods"}, "score": MIN_SCORE - 0.01}]}
    assert retrieve_context(Weak(), "acme-foods", "q") == []
