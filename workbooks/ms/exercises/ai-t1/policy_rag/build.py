"""python -m policy_rag.build --config config/index.yaml --corpus corpus --out index"""
import argparse

import yaml

from policy_rag.index import build_index


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/index.yaml")
    ap.add_argument("--corpus", default="corpus")
    ap.add_argument("--out", default="index")
    ap.add_argument("--built-at", default=None)
    a = ap.parse_args()
    cfg = yaml.safe_load(open(a.config))
    m = build_index(a.corpus, a.out, cfg["embedder"], cfg["chunk_size"], cfg["chunk_overlap"], a.built_at)
    print(f"built {a.out}: {m['chunk_count']} chunks from {m['doc_count']} docs with {m['embedder']}")


if __name__ == "__main__":
    main()
