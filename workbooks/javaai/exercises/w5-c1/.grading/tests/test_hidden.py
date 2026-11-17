import json
from pathlib import Path

import pytest

from rag import evaluate as ev
from rag.chunking import Chunk, fixed_chunks, heading_chunks
from rag.corpus import Lesson, Section, load_lessons, load_questions
from rag.metrics import dedupe, reciprocal_rank, recall_at_k
from rag.retrieve import Index

LESSONS = load_lessons()
QUESTIONS = load_questions()

TOY = Lesson("c1", "l9", "Toy", (Section("l9-s1", "A", " ".join(f"a{i}" for i in range(30))),
                                  Section("l9-s2", "B", " ".join(f"b{i}" for i in range(50)))))


def test_dedupe_keeps_rank_order():
    assert dedupe(["s2", "s1", "s2", "s3", "s1"]) == ["s2", "s1", "s3"]


def test_recall_counts_distinct_sections():
    ranked = ["s1", "s1", "s1", "s2", "s3"]
    assert recall_at_k(ranked, {"s2"}, 2) == 1.0, "duplicates of s1 must not push s2 out of the top 2"
    assert recall_at_k(ranked, {"s3", "s9"}, 3) == 0.5
    assert recall_at_k([], {"s1"}, 5) == 0.0


def test_reciprocal_rank():
    assert reciprocal_rank(["s1", "s1", "s2"], {"s2"}) == 0.5
    assert reciprocal_rank(["s1"], {"s2"}) == 0.0
    assert reciprocal_rank(["s2"], {"s2"}) == 1.0


def test_fixed_chunks_windows_and_overlap():
    chunks = fixed_chunks(TOY, size=40, overlap=10)
    words = [c.text.split() for c in chunks]
    assert [len(w) for w in words] == [40, 40, 20]
    assert words[0][-10:] == words[1][:10], "neighbours share `overlap` words"
    assert words[-1][-1] == "b49", "no text lost at the end"
    assert [c.section_id for c in chunks] == ["l9-s1", "l9-s2", "l9-s2"], "a chunk cites the section with most of its words"
    assert len({c.chunk_id for c in chunks}) == len(chunks)
    assert all(c.course == "c1" and c.lesson == "l9" for c in chunks)


def test_heading_chunks_prefix_and_split():
    chunks = heading_chunks(TOY, max_words=20)
    assert [c.section_id for c in chunks] == ["l9-s1", "l9-s1", "l9-s2", "l9-s2", "l9-s2"]
    assert all(c.text.startswith("Toy - ") for c in chunks)
    assert chunks[2].text.startswith("Toy - B: b0")
    assert len({c.chunk_id for c in chunks}) == len(chunks)


def test_search_never_crosses_courses():
    index = Index([c for l in LESSONS for c in heading_chunks(l)])
    res = index.search("What is the median and the mean?", 50, "bio-210")
    assert res, "the filtered search still returns the course's chunks"
    assert all(c.course == "bio-210" for c in res)
    res = index.search("vaccine antigen memory cells", 3, "stats-101")
    assert all(c.course == "stats-101" for c in res) and len(res) == 3


def test_search_ranks_by_similarity():
    index = Index([c for l in LESSONS for c in heading_chunks(l)])
    top = index.search("What do mRNA vaccines deliver?", 3, "bio-210")
    assert top[0].section_id == "l5-s3"


def test_evaluate_report_shape_and_values():
    r = ev.evaluate(ev.build("heading"), QUESTIONS)
    assert r["n"] == len(QUESTIONS)
    assert set(r) == {"n", "recall@1", "recall@3", "recall@5", "mrr"}
    assert r["recall@1"] >= 0.85 and r["mrr"] >= 0.9


def test_heading_beats_fixed_on_this_corpus():
    h = ev.evaluate(ev.build("heading"), QUESTIONS)
    f = ev.evaluate(ev.build("fixed"), QUESTIONS)
    assert h["mrr"] > f["mrr"]
    assert h["recall@1"] >= f["recall@1"]


def test_gate_logic():
    base = {"recall@1": 0.86, "mrr": 0.92}
    assert ev.gate({"n": 3, "recall@1": 0.85, "mrr": 0.93}, base) == (True, [])
    ok, reasons = ev.gate({"n": 3, "recall@1": 0.80, "mrr": 0.93}, base)
    assert not ok and any("recall@1" in r for r in reasons)
    ok, reasons = ev.gate({"n": 3, "recall@1": 0.9}, base)
    assert not ok and any("mrr" in r for r in reasons), "a missing metric fails the gate"
    assert ev.gate({"recall@1": 0.70, "mrr": 0.92}, base, tolerance=0.2)[0] is True


def test_cli_gate_passes_on_the_corpus():
    assert ev.main() == 0
