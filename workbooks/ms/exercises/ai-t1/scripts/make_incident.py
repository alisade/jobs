"""Generate the incident evidence bundle in incident/. Scenario tooling, not part of the app."""
import json
import shutil
from pathlib import Path

import yaml

from policy_rag.evaluate import evaluate
from policy_rag.index import build_index
from policy_rag.retriever import IndexMismatchError, Retriever

ROOT = Path(__file__).resolve().parent.parent
INC = ROOT / "incident"
USER_QUESTIONS = [
    ("2026-12-07T08:12:44Z", "can I carry over my PTO days"),
    ("2026-12-07T09:30:02Z", "hotel limit in New York"),
    ("2026-12-07T11:05:51Z", "how long is parental leave"),
    ("2026-12-08T07:58:13Z", "do I need approval to work from Spain for two weeks"),
    ("2026-12-08T10:41:27Z", "what happens if I lose my laptop"),
]


def main() -> None:
    if INC.exists():
        shutil.rmtree(INC)
    INC.mkdir()
    # Before the release: the 2026.11.4 index artifact (v1, chunk 200) queried with v1.
    build_index(ROOT / "corpus", INC / "prev-index", "hash-bow-v1", 200, 20, "2026-11-24T02:11:37Z")
    before = evaluate(Retriever(INC / "prev-index", "hash-bow-v1"), ROOT / "eval/questions.jsonl")
    (INC / "eval-2026-11-24.json").write_text(json.dumps(before, indent=2) + "\n")

    shutil.copy(ROOT / "index/manifest.json", INC / "index-manifest-2026-12-07.json")
    shutil.copy(ROOT / "config/app.yaml", INC / "app-config-deployed.yaml")
    cfg = yaml.safe_load((ROOT / "config/app.yaml").read_text())
    try:
        r = Retriever.from_config(ROOT / "config/app.yaml")
    except IndexMismatchError as exc:
        (INC / "startup-error.txt").write_text(f"policy assistant refused to start: {exc}\n")
        print(f"incident: retriever refused to start ({exc})")
        return
    after = evaluate(r, ROOT / "eval/questions.jsonl")
    (INC / "eval-2026-12-07.json").write_text(json.dumps(after, indent=2) + "\n")
    with open(INC / "query-log-2026-12-07.jsonl", "w") as f:
        for ts, q in USER_QUESTIONS:
            hits = r.search(q)[:3]
            f.write(json.dumps({"ts": ts, "question": q, "query_embedder": cfg["query_embedder"],
                                "top_k": hits, "cited": hits[0]["chunk_id"] if hits else None}) + "\n")
    (INC / "ALERT.txt").write_text(
        "[Azure Monitor] Sev2 policy-assistant-retrieval-quality\n"
        f"Nightly retrieval eval hit_rate={after['hit_rate']} (threshold 0.80, previous {before['hit_rate']}).\n"
        "Helpdesk tickets: 'assistant cites the benefits enrollment policy for PTO questions', 'parental"
        " leave answer quotes the remote work policy'.\n")
    print(f"incident: before hit_rate={before['hit_rate']} after hit_rate={after['hit_rate']} -> incident/")


if __name__ == "__main__":
    main()
