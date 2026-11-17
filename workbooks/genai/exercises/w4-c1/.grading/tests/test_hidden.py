"""Hidden checks for genai/w4-c1: statistics, metrics, detection on the fixture, gate, determinism."""

import json

import pytest

from conftest import ROOT, config, lexicon, load_json, sample  # noqa: F401
from evals import bias_probe as bp

MARKERS = ["i'm not able", "i can't help"]


def run_fixture(cfg):
    probes = bp.load_probes(ROOT / "data/probes.json")
    responses, bad = bp.load_responses(ROOT / "data/responses.jsonl")
    return bp.analyze(probes, responses, cfg, load_json("data/tone_lexicon.json"), bad)


def row(report, dim, cat, metric):
    return next(r for r in report["results"] if (r["dimension"], r["category"], r["metric"]) == (dim, cat, metric))


def test_sign_flip_exact_small_case():
    assert bp.sign_flip_test([1, 2, 3]) == pytest.approx(0.25)
    assert bp.sign_flip_test([0, 0, 0]) == pytest.approx(1.0)
    assert bp.sign_flip_test([]) is None


def test_sign_flip_large_case_is_seeded_and_significant():
    diffs = [5.0 + i % 3 for i in range(20)]
    p1 = bp.sign_flip_test(diffs, n_perm=2000, seed=3)
    p2 = bp.sign_flip_test(diffs, n_perm=2000, seed=3)
    assert p1 == p2
    assert 0 < p1 < 0.01


def test_bootstrap_ci():
    assert bp.bootstrap_ci([], 100, 1) is None
    assert bp.bootstrap_ci([4.0] * 8, 200, 1) == (pytest.approx(4.0), pytest.approx(4.0))
    d = [1, 2, 3, 4, 10, -2, 5, 6]
    lo, hi = bp.bootstrap_ci(d, 1000, 9)
    assert lo <= sum(d) / len(d) <= hi
    assert bp.bootstrap_ci(d, 1000, 9) == (lo, hi)


def test_refusals_count_for_refusal_rate_not_for_price(lexicon):
    ss = [sample("p", [10000, 12000]), sample("p", [], "I'm not able to help with that.", 1),
          sample("p", [11000], "Great picks", 2)]
    m = bp.probe_metrics(ss, lexicon, MARKERS)
    assert m["refusal"] == pytest.approx(1 / 3)
    assert m["price"] == pytest.approx(11000)


def test_price_ignores_dollar_amounts_in_text(lexicon):
    m = bp.probe_metrics([sample("p", [3000], "Or splurge on our $449.00 Lodge 6P tent.")], lexicon, MARKERS)
    assert m["price"] == pytest.approx(3000)


def test_all_refused_and_no_samples(lexicon):
    m = bp.probe_metrics([sample("p", [], "I can't help with gifts.")], lexicon, MARKERS)
    assert m["price"] is None and m["refusal"] == 1.0
    e = bp.probe_metrics([], lexicon, MARKERS)
    assert e["price"] is None and e["refusal"] is None


def test_tone_lexicon_score(lexicon):
    assert bp.tone_score("Great! Happy to help, wonderful.", lexicon) == 3
    assert bp.tone_score("Unfortunately we only have basic ones.", lexicon) == -3


def test_malformed_lines_are_counted_not_fatal():
    responses, bad = bp.load_responses(ROOT / "data/responses.jsonl")
    assert bad == 2
    assert sum(len(v) for v in responses.values()) == 309


def test_fixture_detects_coworker_price_gap(config):
    r = run_fixture(config)
    cell = row(r, "name", "coworker", "price")
    assert cell["n_pairs"] == 10
    assert cell["mean_diff"] < -2000
    assert cell["p_value"] < 0.01
    assert cell["ci_high"] < 0
    assert cell["violation"] is True
    assert r["violations"] == ["name/coworker/price"]


def test_aggregate_hides_the_gap(config):
    r = run_fixture(config)
    assert abs(r["aggregate"]["name"]["price"]["diff"]) < config["metrics"]["price"]["threshold"]


def test_missing_probe_listed_and_pair_skipped(config):
    r = run_fixture(config)
    assert r["missing_probes"] == ["p104"]
    assert row(r, "dialect", "partner", "price")["n_pairs"] == 5


def test_results_cover_every_cell(config):
    r = run_fixture(config)
    cells = {(x["dimension"], x["category"], x["metric"]) for x in r["results"]}
    assert len(cells) == (4 + 2) * 3
    assert row(r, "name", "coworker", "tone")["gated"] is False


def test_cli_gate_and_outputs(tmp_path, config):
    args = ["--probes", str(ROOT / "data/probes.json"), "--responses", str(ROOT / "data/responses.jsonl"),
            "--config", str(ROOT / "config.json"), "--lexicon", str(ROOT / "data/tone_lexicon.json"),
            "--out", str(tmp_path / "r.json"), "--md", str(tmp_path / "r.md")]
    assert bp.main(args) == 1
    md = (tmp_path / "r.md").read_text()
    assert "coworker" in md and "VIOLATION" in md
    loose = dict(config)
    loose["metrics"] = {k: dict(v, threshold=10 ** 6) for k, v in config["metrics"].items()}
    (tmp_path / "loose.json").write_text(json.dumps(loose))
    args[5] = str(tmp_path / "loose.json")
    assert bp.main(args) == 0


def test_deterministic_and_no_names_in_outputs(tmp_path, config):
    a = json.dumps(run_fixture(config), sort_keys=True)
    b = json.dumps(run_fixture(config), sort_keys=True)
    assert a == b
    md = bp.render_markdown(run_fixture(config))
    names = {p["name"] for p in bp.load_probes(ROOT / "data/probes.json") if p.get("name")}
    leaked = [n for n in names if n in a or n in md]
    assert not leaked, f"customer-like names in the report: {leaked[:3]}"
