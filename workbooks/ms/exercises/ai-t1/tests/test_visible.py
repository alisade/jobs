"""Visible tests. Run `make setup` first (it builds index/)."""
from pathlib import Path

import pytest

from policy_rag.chunker import chunk_words
from policy_rag.evaluate import evaluate
from policy_rag.retriever import Retriever

ROOT = Path(__file__).resolve().parent.parent


def test_chunker_overlap():
    words = " ".join(f"w{i}" for i in range(10))
    assert chunk_words(words, 4, 1) == ["w0 w1 w2 w3", "w3 w4 w5 w6", "w6 w7 w8 w9"]


def test_retrieval_eval_meets_target():
    if not (ROOT / "index/manifest.json").exists():
        pytest.skip("run make setup first")
    rep = evaluate(Retriever.from_config(ROOT / "config/app.yaml"), ROOT / "eval/questions.jsonl")
    assert rep["hit_rate"] >= 0.8, [r["id"] for r in rep["results"] if not r["hit"]]
