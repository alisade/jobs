"""Retrieval eval for the criteria agent (given). A hit = a top-k chunk of the right policy that
contains the expected text (a whole criteria row for row queries), whitespace-normalised."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .chunker import chunk_policy
from .search import BM25

ROOT = Path(__file__).resolve().parent.parent


def norm(s: str) -> str:
    return " ".join(s.split())


def load_chunks(policy_dir: Path = ROOT / "policies"):
    chunks = []
    for p in sorted(policy_dir.glob("*.md")):
        chunks.extend(chunk_policy(p.read_text(), p.stem))
    return chunks


def row_line(policy_dir: Path, policy_id: str, prefix: str) -> str:
    for line in (policy_dir / f"{policy_id}.md").read_text().splitlines():
        if line.startswith(prefix):
            return line
    return prefix


def run(k: int = 5, policy_dir: Path = ROOT / "policies", queries_path: Path = ROOT / "fixtures" / "queries.json") -> dict:
    chunks = load_chunks(policy_dir)
    index = BM25([c.section_path + "\n" + c.text for c in chunks])
    queries = json.loads(Path(queries_path).read_text())
    by_kind: dict[str, list[int]] = {}
    misses = []
    for q in queries:
        want = norm(row_line(policy_dir, q["policy_id"], q["must_contain"]) if q["kind"] == "row" else q["must_contain"])
        hit = any(chunks[i].policy_id == q["policy_id"] and want in norm(chunks[i].text) for i in index.top(q["text"], k))
        by_kind.setdefault(q["kind"], []).append(int(hit))
        if not hit:
            misses.append(q["id"])
    allq = [h for v in by_kind.values() for h in v]
    return {"chunks": len(chunks), f"recall@{k}": round(sum(allq) / len(allq), 3),
            "by_kind": {kk: round(sum(v) / len(v), 3) for kk, v in by_kind.items()}, "misses": misses}


if __name__ == "__main__":
    print(json.dumps(run(int(sys.argv[1]) if len(sys.argv) > 1 else 5), indent=2))
