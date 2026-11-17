"""Hidden checks for w3-c1."""

from __future__ import annotations

import json
import pathlib

import pytest
from botocore.exceptions import ParamValidationError

from kb_eval.fake_kb import RecordedKnowledgeBase
from kb_eval.harness import compare, evaluate, gate, leaks, recall_at_k, reciprocal_rank
from kb_eval.request import build_retrieve_request

FIX = pathlib.Path(__file__).resolve().parent.parent / "fixtures"
CAT = {"equals": {"key": "doc_type", "value": "sop"}}
YEAR = {"greaterThanOrEquals": {"key": "year", "value": 2025}}


def res(uri: str, tenant: str | None, score: float = 0.5) -> dict:
    md = {"x-amz-bedrock-kb-source-uri": uri}
    if tenant is not None:
        md["tenant_id"] = tenant
    return {"content": {"text": "t", "type": "TEXT"}, "location": {"type": "S3", "s3Location": {"uri": uri}},
            "metadata": md, "score": score}


def flt(req):
    return req["retrievalConfiguration"]["vectorSearchConfiguration"]["filter"]


def test_one_user_filter_is_anded():
    f = flt(build_retrieve_request("KBTIDEWATER01", "acme-foods", "q", [CAT]))
    assert f == {"andAll": [{"equals": {"key": "tenant_id", "value": "acme-foods"}}, CAT]}


def test_two_user_filters_flat_and():
    f = flt(build_retrieve_request("KBTIDEWATER01", "acme-foods", "q", [CAT, YEAR]))
    assert f["andAll"][0] == {"equals": {"key": "tenant_id", "value": "acme-foods"}}
    assert f["andAll"][1:] == [CAT, YEAR]


def test_user_or_stays_inside_the_and():
    orf = {"orAll": [CAT, {"equals": {"key": "doc_type", "value": "policy"}}]}
    f = flt(build_retrieve_request("KBTIDEWATER01", "acme-foods", "q", [orf]))
    assert "andAll" in f and orf in f["andAll"]
    assert "orAll" not in f, "an OR at the top level would let the user filter bypass the tenant filter"


@pytest.mark.parametrize("bad", [
    {"equals": {"key": "tenant_id", "value": "brightline-health"}},
    {"orAll": [CAT, {"equals": {"key": "tenant_id", "value": "x"}}]},
    {"notEquals": {"key": "tenant_id", "value": "acme-foods"}},
])
def test_user_filter_on_tenant_rejected(bad):
    with pytest.raises(ValueError):
        build_retrieve_request("KBTIDEWATER01", "acme-foods", "q", [bad])


@pytest.mark.parametrize("k", [0, 101])
def test_k_bounds(k):
    with pytest.raises(ValueError):
        build_retrieve_request("KBTIDEWATER01", "acme-foods", "q", None, k)


def test_empty_query_rejected():
    with pytest.raises(ValueError):
        build_retrieve_request("KBTIDEWATER01", "acme-foods", "   ")


def test_requests_pass_service_model_validation():
    golden = json.loads((FIX / "golden.json").read_text())
    kb = RecordedKnowledgeBase.from_fixtures("hierarchical")
    for q in golden[:3]:
        kb.retrieve(**build_retrieve_request("KBTIDEWATER01", q["tenant_id"], q["question"], [CAT, YEAR]))
    with pytest.raises(ParamValidationError):  # sanity: the fake does validate
        kb.retrieve(knowledgeBaseId="KBTIDEWATER01", retrievalQuery={"text": "x"},
                    retrievalConfiguration={"vectorSearchConfiguration": {"filter": {"andAll": [CAT]}}})


def test_recall_counts_documents_not_chunks():
    ranked = ["a", "b", "c", "d", "e", "f"]
    assert recall_at_k(["a", "f"], ranked, 5) == 0.5
    assert recall_at_k(["x"], [], 5) == 0.0
    assert reciprocal_rank(["x"], ranked) == 0.0


def test_missing_tenant_metadata_is_a_leak():
    out = leaks("acme-foods", [res("s3://b/a", "acme-foods"), res("s3://b/u", None), res("s3://b/o", "corvid-logistics")])
    assert out == ["s3://b/u", "s3://b/o"]


class FakeKB:
    def __init__(self, by_text):
        self.by_text, self.requests = by_text, []

    def retrieve(self, **p):
        self.requests.append(p)
        return {"retrievalResults": self.by_text.get(p["retrievalQuery"]["text"], [])}


def test_evaluate_report_shape_and_dedupe():
    golden = [{"id": "q1", "tenant_id": "acme-foods", "question": "one", "expected_uris": ["s3://b/a", "s3://b/b"]},
              {"id": "q2", "tenant_id": "corvid-logistics", "question": "two", "expected_uris": ["s3://b/c"]}]
    kb = FakeKB({"one": [res("s3://b/a", "acme-foods"), res("s3://b/a", "acme-foods"), res("s3://b/x", "acme-foods"),
                         res("s3://b/b", "acme-foods")],
                 "two": []})
    rep = evaluate(kb, "KBTIDEWATER01", golden, k=5, config_name="t")
    assert rep["questions"] == 2 and rep["config"] == "t"
    q1 = next(p for p in rep["per_question"] if p["id"] == "q1")
    assert q1["ranked"] == ["s3://b/a", "s3://b/x", "s3://b/b"] and q1["rr"] == 1.0
    assert rep["recall_at_k"] == 0.5 and rep["mrr"] == 0.5
    assert rep["per_tenant"]["corvid-logistics"]["recall_at_k"] == 0.0
    for r in kb.requests:
        assert flt(r)["equals"]["key"] == "tenant_id"


def test_fixture_run_and_gate():
    golden = json.loads((FIX / "golden.json").read_text())
    fixed = evaluate(RecordedKnowledgeBase.from_fixtures("fixed"), "KBTIDEWATER01", golden, 5, "fixed")
    hier = evaluate(RecordedKnowledgeBase.from_fixtures("hierarchical"), "KBTIDEWATER01", golden, 5, "hierarchical")
    assert fixed["recall_at_k"] == pytest.approx(0.725, abs=1e-4)
    assert hier["recall_at_k"] == pytest.approx(0.95, abs=1e-4)
    assert [x["id"] for x in fixed["leaks"]] == ["q09"]
    ok_f, why_f = gate(fixed)
    ok_h, _ = gate(hier)
    assert not ok_f and ok_h
    assert any("tenant" in w.lower() or "leak" in w.lower() for w in why_f)
    c = compare(fixed, hier)
    assert c["recall_at_k"] == pytest.approx(0.225, abs=1e-4)
    assert set(c["per_tenant"]) == {"acme-foods", "brightline-health", "corvid-logistics"}


def test_gate_leak_alone_is_no_go():
    rep = {"k": 5, "recall_at_k": 1.0, "mrr": 1.0, "per_tenant": {"a": {"recall_at_k": 1.0, "mrr": 1.0}},
           "leaks": [{"id": "q1", "tenant_id": "a", "uris": ["s3://b/x"]}]}
    ok, why = gate(rep)
    assert not ok and len(why) == 1


def test_gate_per_tenant_floor():
    rep = {"k": 5, "recall_at_k": 0.9, "mrr": 0.9, "leaks": [],
           "per_tenant": {"a": {"recall_at_k": 1.0, "mrr": 1.0}, "b": {"recall_at_k": 0.6, "mrr": 0.6}}}
    ok, why = gate(rep)
    assert not ok and any("b" in w for w in why)
