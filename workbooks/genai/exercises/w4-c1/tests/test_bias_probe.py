from conftest import ROOT, load_json
from evals.bias_probe import load_probes, probe_metrics


def test_probe_set_loads():
    probes = load_probes(ROOT / "data/probes.json")
    assert len(probes) == 104
    assert {p["dimension"] for p in probes} == {"name", "dialect"}


def test_price_comes_from_structured_recommendations():
    s = {"probe_id": "x", "sample": 0, "text": "Try these.",
         "recommendations": [{"sku": "KO-LAMP-1", "price_cents": 3450}, {"sku": "KO-HEAD-300", "price_cents": 2900}]}
    m = probe_metrics([s], load_json("data/tone_lexicon.json"), [])
    assert m["price"] == 3175
