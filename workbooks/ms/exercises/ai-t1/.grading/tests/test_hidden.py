"""Hidden tests for ms/ai-t1. They build fresh indexes in tmp dirs from the learner's configs."""
import json
from pathlib import Path

import pytest
import yaml

from policy_rag.evaluate import evaluate
from policy_rag.index import build_index
from policy_rag.retriever import IndexMismatchError, Retriever

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = ROOT / "eval/questions.jsonl"


def load(name):
    return yaml.safe_load((ROOT / "config" / name).read_text())


@pytest.fixture
def prod_index(tmp_path):
    cfg = load("index.yaml")
    build_index(ROOT / "corpus", tmp_path / "index", cfg["embedder"], cfg["chunk_size"], cfg["chunk_overlap"])
    return tmp_path / "index"


def test_query_embedder_matches_index_build_config():
    assert load("app.yaml")["query_embedder"] == load("index.yaml")["embedder"]


def test_eval_hit_rate_with_app_config(prod_index):
    app = load("app.yaml")
    r = Retriever(prod_index, app["query_embedder"], app.get("top_k", 3), app.get("min_score", 0.0))
    assert evaluate(r, QUESTIONS)["hit_rate"] >= 0.8


def test_from_config_serves_the_built_index(tmp_path, prod_index):
    (tmp_path / "config").mkdir()
    app = load("app.yaml")
    app["index_dir"] = str(prod_index)
    (tmp_path / "config/app.yaml").write_text(yaml.safe_dump(app))
    r = Retriever.from_config(tmp_path / "config/app.yaml")
    assert evaluate(r, QUESTIONS)["hit_rate"] >= 0.8


def test_guard_refuses_mismatched_embedder(tmp_path):
    build_index(ROOT / "corpus", tmp_path / "v2", "hash-bow-v2", 120, 20)
    with pytest.raises(IndexMismatchError) as exc:
        Retriever(tmp_path / "v2", "hash-bow-v1")
    msg = str(exc.value)
    assert "hash-bow-v1" in msg and "hash-bow-v2" in msg


def test_guard_refuses_unknown_index_embedder(tmp_path):
    build_index(ROOT / "corpus", tmp_path / "idx", "hash-bow-v2", 120, 20)
    m = json.loads((tmp_path / "idx/manifest.json").read_text())
    m["embedder"] = "text-embedding-3-small"
    (tmp_path / "idx/manifest.json").write_text(json.dumps(m))
    with pytest.raises(IndexMismatchError):
        Retriever(tmp_path / "idx", "hash-bow-v2")


def test_guard_refuses_dimension_drift(tmp_path):
    build_index(ROOT / "corpus", tmp_path / "idx", "hash-bow-v2", 120, 20)
    m = json.loads((tmp_path / "idx/manifest.json").read_text())
    m["dims"] = 1536
    (tmp_path / "idx/manifest.json").write_text(json.dumps(m))
    with pytest.raises(IndexMismatchError):
        Retriever(tmp_path / "idx", "hash-bow-v2")


def test_guard_has_no_false_positive_on_v1(tmp_path):
    build_index(ROOT / "corpus", tmp_path / "v1", "hash-bow-v1", 200, 20)
    assert evaluate(Retriever(tmp_path / "v1", "hash-bow-v1"), QUESTIONS)["hit_rate"] >= 0.8


def test_answer_names_the_root_cause():
    text = (ROOT / "ANSWER.md").read_text().lower()
    root = text.split("## root cause", 1)[-1].split("## fix", 1)[0]
    assert "v1" in root and "v2" in root and ("embedder" in root or "embedding" in root)
