"""Visible tests: chunk locators, retrieval, one verified answer. Run: make test"""

from __future__ import annotations

import json

from conftest import DEPLOY, EMAIL, claim_104118
from evidencekit.answer import answer
from evidencekit.fake_gemini import FakeClient, text_response
from evidencekit.search import hybrid_search


def test_email_paragraph_chunks_keep_page_and_index(chunks):
    ids = {c.id: c for c in chunks}
    body = ids[f"{EMAIL}#p1.para5"]
    assert body.locator == {"blob": EMAIL, "page": 1, "paragraph": 5}
    assert f"{EMAIL}#p1.para0" not in ids  # page header skipped


def test_hybrid_search_finds_the_approval_and_the_deploy(chunks):
    top = [c.id for c, _ in hybrid_search(chunks, "CHG-104118 approved deployed", top_k=3)]
    assert f"{EMAIL}#p1.para5" in top and f"{DEPLOY}#row2" in top


def test_verified_answer_104118(container):
    client = FakeClient([text_response(json.dumps(claim_104118()))])
    a = answer(client, container, "CHG-104118")
    assert a.status == "approved_before_deploy", a.reasons
    assert len(a.citations) == 3
