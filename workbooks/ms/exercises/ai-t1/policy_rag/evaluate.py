"""Retrieval eval: hit@k against expected source documents.
python -m policy_rag.evaluate --config config/app.yaml --questions eval/questions.jsonl --out report.json"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from policy_rag.retriever import Retriever


def evaluate(retriever: Retriever, questions_path: str | Path) -> dict:
    results = []
    for line in Path(questions_path).read_text().splitlines():
        if not line.strip():
            continue
        q = json.loads(line)
        hits = retriever.search(q["question"])
        docs = retriever.top_docs(q["question"])
        results.append({
            "id": q["id"], "question": q["question"], "expected_doc": q["expected_doc"],
            "retrieved_docs": docs, "hit": q["expected_doc"] in docs,
            "top_chunks": hits[:3],
        })
    hit_rate = sum(r["hit"] for r in results) / len(results) if results else 0.0
    return {"query_embedder": retriever.embedder.name, "index_manifest": retriever.manifest,
            "hit_rate": round(hit_rate, 3), "results": results}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/app.yaml")
    ap.add_argument("--questions", default="eval/questions.jsonl")
    ap.add_argument("--out", default="report.json")
    a = ap.parse_args()
    rep = evaluate(Retriever.from_config(a.config), a.questions)
    Path(a.out).write_text(json.dumps(rep, indent=2) + "\n")
    print(f"hit_rate={rep['hit_rate']} query_embedder={rep['query_embedder']} index={rep['index_manifest']['embedder']}")


if __name__ == "__main__":
    main()
