import hashlib
import json

import pytest

from tuneval import data
from tuneval.evaluate import parse_item, percentile, pick, score
from tuneval.tuning import SYSTEM, build_dataset, normalize, to_example

AUTH = data.authored()
HELD = data.heldout()
PRICES = data.prices()
MODELS = data.candidate_models()


def report(name):
    return score(data.candidate(name), HELD, PRICES[MODELS[name]])


def test_example_format():
    ex = to_example(AUTH[7])
    assert set(ex) == {"systemInstruction", "contents"}
    assert ex["systemInstruction"] == {"role": "system", "parts": [{"text": SYSTEM}]}
    user, model = ex["contents"]
    assert user["role"] == "user" and AUTH[7]["sectionText"] in user["parts"][0]["text"]
    assert model["role"] == "model" and json.loads(model["parts"][0]["text"]) == AUTH[7]["item"]


def test_dataset_drops_duplicates_and_leakage():
    train, val, rep = build_dataset(AUTH, HELD)
    assert rep == {"input": 309, "duplicates": 6, "leakage": 3, "train": 270, "validation": 30}
    assert len(train) == 270 and len(val) == 30
    held_texts = {h["sectionText"] for h in HELD}
    for ex in train + val:
        assert not any(t in ex["contents"][0]["parts"][0]["text"] for t in held_texts), "held-out content leaked into tuning data"


def test_split_is_deterministic_and_by_id_hash():
    a = build_dataset(AUTH, HELD)
    b = build_dataset(list(reversed(AUTH)), HELD)
    assert a[0] == b[0] and a[1] == b[1], "input order must not change the split"
    val_ids = {r["id"] for r in AUTH if int(hashlib.sha256(r["id"].encode()).hexdigest(), 16) % 100 < 10}
    val_stems = {json.loads(e["contents"][1]["parts"][0]["text"])["stem"] for e in a[1]}
    assert val_stems <= {r["item"]["stem"] for r in AUTH if r["id"] in val_ids}


@pytest.mark.parametrize("text", [
    '{"stem":"s","options":["a","b","c"],"answerIndex":0,"explanation":"e","sectionId":"x"}',
    '{"stem":"s","options":["a","b","c","d"],"answerIndex":4,"explanation":"e","sectionId":"x"}',
    '{"stem":"s","options":["a","b","c","d"],"answerIndex":"1","explanation":"e","sectionId":"x"}',
    '{"stem":"s","options":["a","b","c","d"],"answerIndex":true,"explanation":"e","sectionId":"x"}',
    '{"stem":"s","options":["a","","c","d"],"answerIndex":1,"explanation":"e","sectionId":"x"}',
    '{"stem":"s","options":["a","b","c","d"],"answerIndex":1,"sectionId":"x"}',
    '["not", "an", "object"]',
    'Sure! Here is a quiz item',
    '{"stem":"s","options":["a","b","c","d"],"answerIn',
])
def test_parse_item_rejects(text):
    assert parse_item(text) is None


def test_percentile_nearest_rank():
    v = [5, 1, 4, 2, 3, 10, 9, 8, 7, 6]
    assert percentile(v, 50) == 5
    assert percentile(v, 95) == 10
    assert percentile([42], 95) == 42


def test_scores_match_the_reference():
    assert report("prompt-flash") == {"n": 50, "format_valid": 0.88, "correct": 0.84, "grounded": 0.84,
                                      "cost_per_1000": 0.9241, "p50_ms": 2336, "p95_ms": 2984}
    assert report("fewshot-flash") == {"n": 50, "format_valid": 0.96, "correct": 0.9, "grounded": 0.88,
                                       "cost_per_1000": 1.4919, "p50_ms": 3053, "p95_ms": 10058}
    assert report("tuned-flashlite") == {"n": 50, "format_valid": 1.0, "correct": 0.9, "grounded": 0.98,
                                         "cost_per_1000": 0.1332, "p50_ms": 995, "p95_ms": 3579}


def test_pick():
    reps = {c: report(c) for c in data.CANDIDATES}
    assert pick(reps) == "tuned-flashlite"
    assert pick(reps, min_correct=0.95) is None
    reps2 = dict(reps)
    reps2["tuned-flashlite"] = {**reps["tuned-flashlite"], "format_valid": 0.9}
    assert pick(reps2) == "fewshot-flash"
