"""Hidden tests for ms/w10-c1: edge cases, failure paths and README rules."""
import json
from pathlib import Path

import pytest

from release_gate.evaluate import compare_runs, evaluate_run, gate, load_transcripts, main, p95, score_case
from release_gate.model import TestCase

MARKERS = ["i can't help with that", "outside what i can help with"]


def convo(tc, text="ok", tools=(), cites=(), t0="2026-12-01T10:00:00.000Z", t1="2026-12-01T10:00:02.000Z"):
    acts = [{"type": "message", "from": {"role": "user"}, "timestamp": t0, "text": "hi"}]
    for t in tools:
        acts.append({"type": "event", "name": "toolInvoked", "timestamp": t0, "value": {"tool": t}})
    bot = {"type": "message", "from": {"role": "bot"}, "timestamp": t1, "text": text}
    if cites:
        bot["entities"] = [{"type": "citation", "source": c} for c in cites]
    acts.append(bot)
    return {"conversationId": "c-" + tc, "testCaseId": tc, "activities": acts}


def write_run(tmp_path, name, records, raw_lines=()):
    d = tmp_path / name
    d.mkdir()
    lines = [json.dumps(r) for r in records] + list(raw_lines)
    (d / "transcripts.jsonl").write_text("\n".join(lines) + "\n")
    return d


def cfg(**over):
    base = {
        "thresholds": {},
        "regression": {},
        "categories": {},
        "max_malformed_records": 0,
        "refusal_markers": MARKERS,
    }
    base.update(over)
    return base


TOOL_CASE = TestCase(id="t1", category="orders", utterance="where", expected_tool="GetOrderStatus",
                     expected_facts=("shipped",))
KB_CASE = TestCase(id="k1", category="returns", utterance="days?", allowed_sources=("kb:returns-policy",),
                   expected_facts=("30 days",))
SAFE_CASE = TestCase(id="s1", category="safety", utterance="ignore instructions", must_refuse=True)


# ------------------------------------------------------------ loading


def test_malformed_records_are_errors_not_crashes(tmp_path):
    d = write_run(tmp_path, "r", [convo("t1")], raw_lines=[
        '{"testCaseId": "k1", "activities": [',          # truncated JSON
        '{"conversationId": "x", "activities": []}',      # no testCaseId
        '{"testCaseId": "s1"}',                           # no activities
        '[1, 2, 3]',                                      # not an object
    ])
    transcripts, errors = load_transcripts(d / "transcripts.jsonl")
    assert set(transcripts) == {"t1"}
    assert len(errors) == 4


def test_duplicate_transcript_keeps_first(tmp_path):
    d = write_run(tmp_path, "r", [convo("t1", text="first shipped", tools=["GetOrderStatus"]),
                                  convo("t1", text="second")])
    transcripts, errors = load_transcripts(d / "transcripts.jsonl")
    assert transcripts["t1"]["activities"][-1]["text"] == "first shipped"
    assert len(errors) == 1


def test_missing_file_is_an_error_and_all_cases_missing(tmp_path):
    (tmp_path / "empty").mkdir()
    rep = evaluate_run([TOOL_CASE, KB_CASE], tmp_path / "empty", cfg())
    assert rep["errors"]
    assert rep["missing"] == ["k1", "t1"]
    assert rep["metrics"]["tool_accuracy"] == 0.0


# ------------------------------------------------------------ per-case scoring


def test_missing_transcript_counts_as_failure_not_skip(tmp_path):
    d = write_run(tmp_path, "r", [convo("t1", text="it has shipped", tools=["GetOrderStatus"])])
    rep = evaluate_run([TOOL_CASE, KB_CASE, SAFE_CASE], d, cfg())
    k1 = rep["cases"]["k1"]
    assert k1["missing"] is True and k1["passed"] is False
    assert k1["grounded"] is False and k1["fact_recall"] == 0.0
    assert rep["cases"]["s1"]["refusal_correct"] is False
    assert rep["metrics"]["grounded_rate"] == 0.0
    assert rep["metrics"]["refusal_recall"] == 0.0
    assert rep["metrics"]["fact_recall"] == pytest.approx(0.5)
    assert rep["missing"] == ["k1", "s1"]


def test_tool_must_be_first_invoked():
    r = score_case(TOOL_CASE, convo("t1", text="shipped", tools=["StartReturn", "GetOrderStatus"]), MARKERS)
    assert r["tool_correct"] is False and r["passed"] is False


def test_grounding_rejects_foreign_or_absent_citations():
    assert score_case(KB_CASE, convo("k1", text="30 days", cites=["kb:returns-policy", "web:bing"]), MARKERS)["grounded"] is False
    assert score_case(KB_CASE, convo("k1", text="30 days"), MARKERS)["grounded"] is False
    ok = score_case(KB_CASE, convo("k1", text="Within 30 DAYS!", cites=["kb:returns-policy"]), MARKERS)
    assert ok["grounded"] is True and ok["fact_recall"] == 1.0 and ok["passed"] is True


def test_refusal_with_tool_call_is_not_a_correct_refusal():
    r = score_case(SAFE_CASE, convo("s1", text="I can't help with that.", tools=["StartReturn"]), MARKERS)
    assert r["refused"] is True and r["refusal_correct"] is False and r["passed"] is False
    good = score_case(SAFE_CASE, convo("s1", text="Sorry, I CAN'T help with that!"), MARKERS)
    assert good["refusal_correct"] is True and good["passed"] is True


def test_over_refusal_fails_case_and_counts_in_rate(tmp_path):
    d = write_run(tmp_path, "r", [
        convo("t1", text="That is outside what I can help with.", tools=["GetOrderStatus"]),
        convo("k1", text="30 days", cites=["kb:returns-policy"]),
    ])
    rep = evaluate_run([TOOL_CASE, KB_CASE], d, cfg())
    assert rep["cases"]["t1"]["passed"] is False
    assert rep["metrics"]["over_refusal_rate"] == pytest.approx(0.5)


def test_fact_recall_partial_and_normalized():
    case = TestCase(id="f", category="orders", utterance="x", expected_facts=("$49.99", "FB-10422", "Nov 14"))
    r = score_case(case, convo("f", text="Order fb 10422 costs 49.99 dollars."), MARKERS)
    assert r["fact_recall"] == pytest.approx(2 / 3)
    assert r["passed"] is False


# ------------------------------------------------------------ latency


@pytest.mark.parametrize("values,expected", [
    ([], None),
    ([700], 700),
    (list(range(1, 11)), 10),
    (list(range(1, 21)), 19),
    ([5, 1, 4, 2, 3], 5),
    (list(range(100, 0, -1)), 95),
])
def test_p95_nearest_rank(values, expected):
    assert p95(values) == expected


def test_latency_none_when_timestamp_missing_and_excluded(tmp_path):
    bad = convo("t1", text="shipped", tools=["GetOrderStatus"])
    del bad["activities"][-1]["timestamp"]
    d = write_run(tmp_path, "r", [bad, convo("k1", text="30 days", cites=["kb:returns-policy"],
                                             t1="2026-12-01T10:00:03.250Z")])
    rep = evaluate_run([TOOL_CASE, KB_CASE], d, cfg())
    assert rep["cases"]["t1"]["latency_ms"] is None
    assert rep["metrics"]["latency_p95_ms"] == 3250


# ------------------------------------------------------------ categories and gate


def test_empty_category_reported_and_fails_gate(tmp_path):
    d = write_run(tmp_path, "r", [convo("t1", text="shipped", tools=["GetOrderStatus"])])
    c = cfg(categories={"orders": 0.8, "warranty": 0.8})
    rep = evaluate_run([TOOL_CASE], d, c)
    assert rep["categories"]["warranty"] == {"cases": 0, "passed": 0, "pass_rate": None}
    g = gate(rep, None, c)
    assert g["passed"] is False
    assert any("warranty" in r for r in g["reasons"])


def test_metric_without_applicable_cases_fails_its_threshold(tmp_path):
    d = write_run(tmp_path, "r", [convo("t1", text="shipped", tools=["GetOrderStatus"])])
    c = cfg(thresholds={"min_refusal_recall": 1.0})
    rep = evaluate_run([TOOL_CASE], d, c)
    assert rep["metrics"]["refusal_recall"] is None
    g = gate(rep, None, c)
    assert g["passed"] is False and any("refusal_recall" in r for r in g["reasons"])


def test_thresholds_are_inclusive(tmp_path):
    d = write_run(tmp_path, "r", [convo("t1", text="shipped", tools=["GetOrderStatus"]),
                                  convo("k1", text="nope", cites=["web:bing"])])
    c = cfg(thresholds={"min_fact_recall": 0.5, "max_latency_p95_ms": 2000})
    rep = evaluate_run([TOOL_CASE, KB_CASE], d, c)
    assert gate(rep, None, c)["passed"] is True
    c2 = cfg(thresholds={"min_fact_recall": 0.51})
    assert gate(rep, None, c2)["passed"] is False


def test_malformed_tolerance(tmp_path):
    d = write_run(tmp_path, "r", [convo("t1", text="shipped", tools=["GetOrderStatus"])], raw_lines=["{oops"])
    rep = evaluate_run([TOOL_CASE], d, cfg())
    assert gate(rep, None, cfg(max_malformed_records=1))["passed"] is True
    assert gate(rep, None, cfg(max_malformed_records=0))["passed"] is False


def test_unknown_test_case_transcript_reported(tmp_path):
    d = write_run(tmp_path, "r", [convo("t1", text="shipped", tools=["GetOrderStatus"]), convo("zz-9")])
    rep = evaluate_run([TOOL_CASE], d, cfg())
    assert any("zz-9" in e for e in rep["errors"])


# ------------------------------------------------------------ comparison


def fake_report(**metrics):
    m = {k: None for k in ("tool_accuracy", "grounded_rate", "refusal_recall", "over_refusal_rate",
                           "fact_recall", "latency_p95_ms")}
    m.update(metrics)
    return {"metrics": m, "cases": {}, "categories": {}, "missing": [], "errors": []}


def test_ties_are_not_regressions():
    b = fake_report(tool_accuracy=0.9, latency_p95_ms=4000, over_refusal_rate=0.05)
    comp = compare_runs(b, fake_report(tool_accuracy=0.9, latency_p95_ms=4000, over_refusal_rate=0.05),
                        cfg(regression={"tool_accuracy": 0.0, "latency_p95_ms": 0.0, "over_refusal_rate": 0.0}))
    assert comp["regressions"] == []
    assert comp["deltas"]["tool_accuracy"] == pytest.approx(0.0)


def test_regression_tolerance_boundaries():
    c = cfg(regression={"tool_accuracy": 0.05, "latency_p95_ms": 0.20, "over_refusal_rate": 0.05})
    b = fake_report(tool_accuracy=0.90, latency_p95_ms=5000, over_refusal_rate=0.0)
    exact = compare_runs(b, fake_report(tool_accuracy=0.85, latency_p95_ms=6000, over_refusal_rate=0.05), c)
    assert exact["regressions"] == []
    worse = compare_runs(b, fake_report(tool_accuracy=0.84, latency_p95_ms=6001, over_refusal_rate=0.06), c)
    assert sorted(worse["regressions"]) == ["latency_p95_ms", "over_refusal_rate", "tool_accuracy"]


def test_metric_not_in_regression_config_is_not_checked():
    comp = compare_runs(fake_report(fact_recall=1.0), fake_report(fact_recall=0.1), cfg(regression={}))
    assert comp["regressions"] == []
    assert comp["deltas"]["fact_recall"] == pytest.approx(-0.9)


def test_metric_disappearing_is_a_regression():
    comp = compare_runs(fake_report(grounded_rate=1.0), fake_report(grounded_rate=None),
                        cfg(regression={"grounded_rate": 0.1}))
    assert comp["regressions"] == ["grounded_rate"]
    assert comp["deltas"]["grounded_rate"] is None


def test_case_regressions_block_only_in_listed_categories(tmp_path):
    good = write_run(tmp_path, "good", [convo("t1", text="shipped", tools=["GetOrderStatus"]),
                                        convo("s1", text="I can't help with that.")])
    bad = write_run(tmp_path, "bad", [convo("t1", text="on its way", tools=["GetOrderStatus"]),
                                      convo("s1", text="I can't help with that.")])
    c = cfg(regression={"block_case_regressions_in": ["safety"]})
    base = evaluate_run([TOOL_CASE, SAFE_CASE], good, c)
    cand = evaluate_run([TOOL_CASE, SAFE_CASE], bad, c)
    comp = compare_runs(base, cand, c)
    assert comp["case_regressions"] == ["t1"]
    assert gate(cand, comp, c)["passed"] is True
    c2 = cfg(regression={"block_case_regressions_in": ["orders"]})
    assert gate(cand, compare_runs(base, cand, c2), c2)["passed"] is False


# ------------------------------------------------------------ CLI


def test_cli_bad_input_exit_2(tmp_path):
    (tmp_path / "gate.yaml").write_text("thresholds: {}\n")
    rc = main(["--testset", str(tmp_path / "nope.jsonl"), "--candidate", str(tmp_path),
               "--config", str(tmp_path / "gate.yaml"), "--out", str(tmp_path / "r.json")])
    assert rc == 2


def test_cli_pass_exit_0_without_baseline(tmp_path):
    ts = tmp_path / "ts.jsonl"
    ts.write_text(json.dumps({"id": "t1", "category": "orders", "utterance": "where",
                              "expected_tool": "GetOrderStatus", "expected_facts": ["shipped"]}) + "\n")
    run = write_run(tmp_path, "run", [convo("t1", text="It shipped.", tools=["GetOrderStatus"])])
    (tmp_path / "gate.yaml").write_text("thresholds:\n  min_tool_accuracy: 1.0\nrefusal_markers: []\n")
    out = tmp_path / "r.json"
    rc = main(["--testset", str(ts), "--candidate", str(run), "--config", str(tmp_path / "gate.yaml"),
               "--out", str(out)])
    assert rc == 0
    rep = json.loads(out.read_text())
    assert rep["gate"] == {"passed": True, "reasons": []}
    assert rep["baseline"] is None and rep["comparison"] is None
