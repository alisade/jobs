"""Hidden tests for audit/w5-c1: chunking, BM25, hashing vectors, RRF, citation verification."""

from __future__ import annotations

import json
import math

import pytest

from conftest import CAB, DEPLOY, EMAIL, OTHER, claim_104118, claim_104201
from evidencekit.answer import answer, expand
from evidencekit.chunks import build_chunks
from evidencekit.fake_gemini import FakeClient, text_response
from evidencekit.search import bm25_scores, cosine, hash_vector, hybrid_search, rrf
from evidencekit.verify import Resolver, verify


def ask(container, claim, change_id=None):
    client = FakeClient([text_response(json.dumps(claim) if not isinstance(claim, str) else claim)])
    return answer(client, container, change_id or claim["change_id"]), client


# ---------- chunking ----------

def test_table_rows_repeat_header(chunks):
    ids = {c.id: c for c in chunks}
    row = ids[f"{CAB}#p2.t0.r2"]
    assert row.kind == "table_row"
    assert row.locator == {"blob": CAB, "page": 2, "table": 0, "row": 2}
    first, second = row.text.split("\n")
    assert "Change" in first and "Decided at" in first
    assert "CHG-104201" in second and "2026-04-14T15:30:00-05:00" in second
    assert row.cells[2] == "2026-04-14T15:30:00-05:00"
    assert f"{CAB}#p2.t0.r0" not in ids


def test_csv_rows_are_one_based_with_header(chunks):
    ids = {c.id: c for c in chunks}
    r = ids[f"{DEPLOY}#row4"]
    assert r.locator == {"blob": DEPLOY, "row": 4}
    assert r.text.startswith("change_id,pr_number")
    assert r.cells[0] == "CHG-104201" and r.cells[3] == "2026-04-14T18:05:00Z"
    assert sum(1 for c in chunks if c.blob == DEPLOY) == 6


def test_only_layout_and_csv_are_parsed(container):
    chunks = build_chunks(container)
    assert not any(c.blob.endswith(".docx") for c in chunks)
    assert not any(b.endswith(".docx") for b in container.downloads)
    assert {c.kind for c in chunks} == {"paragraph", "table_row", "csv_row"}


# ---------- retrieval ----------

def test_bm25_hand_computed():
    s = bm25_scores(["a b", "a c", "d"], "b")
    idf = math.log((3 - 1 + 0.5) / (1 + 0.5) + 1)
    tf = 1 * 2.5 / (1 + 1.5 * (1 - 0.75 + 0.75 * 2 / (5 / 3)))
    assert s[0] == pytest.approx(idf * tf) and s[1] == 0 and s[2] == 0


def test_bm25_change_id_is_one_token():
    s = bm25_scores(["CHG-104118 approved", "CHG-104190 approved", "approved"], "chg-104118")
    assert s[0] > 0 and s[1] == 0 and s[2] == 0


def test_hash_vector_normalized_and_deterministic():
    v = hash_vector("approved CHG-104118 approved")
    assert sum(x * x for x in v) == pytest.approx(1.0)
    assert v == hash_vector("approved CHG-104118 approved")
    assert cosine(v, v) == pytest.approx(1.0)
    assert hash_vector("") == [0.0] * len(v)


def test_rrf_ordering():
    out = rrf([["a", "b", "c"], ["c", "a"]], k=60)
    assert [x for x, _ in out] == ["a", "c", "b"]
    assert out[0][1] == pytest.approx(1 / 61 + 1 / 62)
    assert out[1][1] == pytest.approx(1 / 63 + 1 / 61)


def test_rrf_ties_by_id():
    assert [x for x, _ in rrf([["y", "x"], ["x", "y"]])] == ["x", "y"]


def test_hybrid_ranks_the_cab_row(chunks):
    top = [c.id for c, _ in hybrid_search(chunks, "CHG-104201 approved CAB decision", top_k=2)]
    assert top[0] == f"{CAB}#p2.t0.r2"


def test_expand_brings_the_email_header(chunks):
    hits = [c for c in chunks if c.id == f"{EMAIL}#p1.para5"]
    ids = [c.id for c in expand(hits, chunks)]
    assert ids[0] == f"{EMAIL}#p1.para5"
    assert f"{EMAIL}#p1.para3" in ids and f"{EMAIL}#p2.para7" not in ids
    assert len(ids) == len(set(ids))


def test_prompt_carries_evidence_as_data(container):
    a, client = ask(container, claim_104118())
    req = client.models.requests[0]
    assert req["config"].temperature == 0
    assert "Date: 2026-03-04" not in str(req["config"].system_instruction)
    user = " ".join(p.text or "" for c in req["contents"] for p in c.parts)
    assert "Date: 2026-03-04T09:15:00-06:00" in user and '"paragraph": 3' in user
    assert f"{EMAIL}#p1.para3" in a.retrieved


# ---------- verification ----------

def test_whitespace_normalized_quote(container):
    c = claim_104118()
    c["citations"][0]["quote"] = "Approved.\n   CHG-104118   may be deployed"
    assert ask(container, c)[0].status == "approved_before_deploy"


def test_fabricated_quote(container):
    c = claim_104118()
    c["citations"][0]["quote"] = "Approved by the CAB. CHG-104118 may be deployed"
    a = ask(container, c)[0]
    assert a.status == "insufficient_evidence" and any("quote" in r for r in a.reasons)


def test_wrong_page(container):
    c = claim_104118()
    c["citations"][0]["page"] = 2
    assert ask(container, c)[0].status == "insufficient_evidence"


def test_table_cell_citation(container):
    a = ask(container, claim_104201())[0]
    assert a.status == "not_approved_before_deploy", a.reasons


def test_table_cell_wrong_column(container):
    c = claim_104201()
    c["citations"][0]["col"] = 1
    assert ask(container, c)[0].status == "insufficient_evidence"


def test_conclusion_contradicting_timestamps(container):
    a = ask(container, claim_104201(conclusion="approved_before_deploy"))[0]
    assert a.status == "insufficient_evidence"


def test_other_change_row_does_not_count(container):
    c = claim_104201()
    c["citations"][0] = {"role": "approval", "blob": CAB, "page": 2, "table": 0, "row": 1, "col": 2, "quote": "2026-04-14T15:05:00-05:00"}
    c["approval_at"] = "2026-04-14T15:05:00-05:00"
    assert ask(container, c)[0].status == "insufficient_evidence"


def test_no_evidence_mention_is_not_approval(container):
    c = {"change_id": "CHG-104305", "conclusion": "approved_before_deploy",
         "approval_at": "2026-05-02T10:00:00-05:00", "deployed_at": "2026-05-04T14:00:00Z",
         "citations": [
             {"role": "approval", "blob": OTHER, "page": 1, "paragraph": 3, "quote": "CHG-104305 is not on this week's agenda"},
             {"role": "approval", "blob": OTHER, "page": 1, "paragraph": 1, "quote": "Date: 2026-05-02T10:00:00-05:00"},
             {"role": "deploy", "blob": DEPLOY, "row": 6, "quote": "CHG-104305,2293,prod,2026-05-04T14:00:00Z"}]}
    assert ask(container, c)[0].status == "insufficient_evidence"


def test_no_citations(container):
    c = claim_104118(citations=[])
    assert ask(container, c)[0].status == "insufficient_evidence"


def test_model_says_insufficient(container):
    c = {"change_id": "CHG-104305", "conclusion": "insufficient_evidence", "approval_at": None, "deployed_at": None, "citations": []}
    assert ask(container, c)[0].status == "insufficient_evidence"


def test_invalid_json_and_wrong_change(container):
    assert ask(container, "not json", "CHG-104118")[0].status == "insufficient_evidence"
    assert ask(container, claim_104201(), "CHG-104118")[0].status == "insufficient_evidence"


def test_resolver_cells_rows_and_missing(chunks):
    r = Resolver(chunks)
    assert r.text({"blob": CAB, "page": 2, "table": 0, "row": 2, "col": 1}) == "approved (retrospective)"
    assert r.text({"blob": DEPLOY, "row": 2}) == "CHG-104118,2231,prod,2026-03-04T16:20:00Z,deploy-88120"
    assert r.text({"blob": DEPLOY, "row": 2, "col": 4}) == "deploy-88120"
    assert r.text({"blob": EMAIL, "page": 1, "paragraph": 99}) is None
    assert r.text({"blob": DEPLOY, "row": 2, "col": 9}) is None
    assert verify({"conclusion": "maybe"}, r, "CHG-104118")[0] == "insufficient_evidence"
