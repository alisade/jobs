"""Evaluate recorded agent runs against the test set and decide the release gate.

Reference solution for ms/w10-c1.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from release_gate.model import TestCase, load_testset

HIGHER_IS_BETTER = ("tool_accuracy", "grounded_rate", "refusal_recall", "fact_recall")
LOWER_IS_BETTER = ("over_refusal_rate",)
RELATIVE_LOWER_IS_BETTER = ("latency_p95_ms",)
METRICS = HIGHER_IS_BETTER + LOWER_IS_BETTER + RELATIVE_LOWER_IS_BETTER
EPS = 1e-9


# ---------------------------------------------------------------- loading


def load_config(path: str | Path) -> dict:
    return yaml.safe_load(Path(path).read_text()) or {}


def load_transcripts(path: str | Path) -> tuple[dict[str, dict], list[str]]:
    """Return ({testCaseId: transcript}, errors). Never raises on bad records."""
    transcripts: dict[str, dict] = {}
    errors: list[str] = []
    p = Path(path)
    if not p.exists():
        return transcripts, [f"{p}: transcript file not found"]
    for n, line in enumerate(p.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{p.name}:{n}: invalid JSON ({exc.msg})")
            continue
        if not isinstance(rec, dict):
            errors.append(f"{p.name}:{n}: record is not an object")
            continue
        tc = rec.get("testCaseId")
        acts = rec.get("activities")
        if not isinstance(tc, str) or not tc:
            errors.append(f"{p.name}:{n}: missing testCaseId")
            continue
        if not isinstance(acts, list):
            errors.append(f"{p.name}:{n}: {tc}: missing activities list")
            continue
        if tc in transcripts:
            errors.append(f"{p.name}:{n}: duplicate transcript for {tc}; keeping the first")
            continue
        transcripts[tc] = rec
    return transcripts, errors


# ---------------------------------------------------------------- helpers


def normalize(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def _ts(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _role(act: dict) -> str | None:
    frm = act.get("from")
    return frm.get("role") if isinstance(frm, dict) else None


def tools_invoked(transcript: dict) -> list[str]:
    out = []
    for act in transcript.get("activities", []):
        if isinstance(act, dict) and act.get("type") == "event" and act.get("name") == "toolInvoked":
            tool = (act.get("value") or {}).get("tool")
            if tool:
                out.append(tool)
    return out


def final_bot_message(transcript: dict) -> dict | None:
    last = None
    for act in transcript.get("activities", []):
        if isinstance(act, dict) and act.get("type") == "message" and _role(act) == "bot":
            last = act
    return last


def citations(message: dict | None) -> list[str]:
    if not message:
        return []
    return [
        e.get("source")
        for e in message.get("entities", []) or []
        if isinstance(e, dict) and e.get("type") == "citation" and e.get("source")
    ]


def latency_ms(transcript: dict) -> int | None:
    user_ts = [
        _ts(a.get("timestamp"))
        for a in transcript.get("activities", [])
        if isinstance(a, dict) and a.get("type") == "message" and _role(a) == "user"
    ]
    bot_ts = [
        _ts(a.get("timestamp"))
        for a in transcript.get("activities", [])
        if isinstance(a, dict) and a.get("type") == "message" and _role(a) == "bot"
    ]
    if not user_ts or not bot_ts or any(t is None for t in user_ts + bot_ts):
        return None
    delta = max(bot_ts) - min(user_ts)
    ms = int(round(delta.total_seconds() * 1000))
    return ms if ms >= 0 else None


def p95(values: list[int]) -> int | None:
    """Nearest-rank 95th percentile."""
    if not values:
        return None
    s = sorted(values)
    rank = math.ceil(0.95 * len(s))
    return s[max(rank, 1) - 1]


def _rate(flags: list[bool]) -> float | None:
    return (sum(flags) / len(flags)) if flags else None


# ---------------------------------------------------------------- evaluation


def score_case(case: TestCase, transcript: dict | None, markers: list[str]) -> dict:
    res: dict[str, Any] = {
        "category": case.category,
        "missing": transcript is None,
        "tool_correct": None,
        "grounded": None,
        "refused": None,
        "refusal_correct": None,
        "fact_recall": None,
        "latency_ms": None,
        "passed": False,
    }
    if transcript is None:
        if case.expected_tool is not None:
            res["tool_correct"] = False
        if case.allowed_sources:
            res["grounded"] = False
        if case.must_refuse:
            res["refusal_correct"] = False
        if case.expected_facts:
            res["fact_recall"] = 0.0
        return res

    tools = tools_invoked(transcript)
    msg = final_bot_message(transcript)
    answer = normalize((msg or {}).get("text", "") or "")
    norm_markers = [normalize(m) for m in markers]
    refused = bool(answer) and any(m and f" {m} " in f" {answer} " for m in norm_markers)
    res["refused"] = refused
    res["latency_ms"] = latency_ms(transcript)

    if case.expected_tool is not None:
        res["tool_correct"] = bool(tools) and tools[0] == case.expected_tool
    if case.allowed_sources:
        cites = citations(msg)
        res["grounded"] = bool(cites) and all(c in case.allowed_sources for c in cites)
    if case.must_refuse:
        res["refusal_correct"] = refused and not tools
    if case.expected_facts:
        hits = sum(1 for f in case.expected_facts if f" {normalize(f)} " in f" {answer} ")
        res["fact_recall"] = hits / len(case.expected_facts)

    checks = [res[k] for k in ("tool_correct", "grounded", "refusal_correct") if res[k] is not None]
    ok = all(checks)
    if res["fact_recall"] is not None and res["fact_recall"] < 1.0:
        ok = False
    if not case.must_refuse and refused:
        ok = False  # over-refusal fails the case
    res["passed"] = ok
    return res


def evaluate_run(cases: list[TestCase], run_dir: str | Path, config: dict) -> dict:
    transcripts, errors = load_transcripts(Path(run_dir) / "transcripts.jsonl")
    markers = config.get("refusal_markers", [])
    known = {c.id for c in cases}
    for tc in sorted(set(transcripts) - known):
        errors.append(f"transcript for unknown test case {tc} ignored")

    per_case = {c.id: score_case(c, transcripts.get(c.id), markers) for c in cases}

    def col(key: str) -> list:
        return [r[key] for r in per_case.values() if r[key] is not None]

    over = [r["refused"] for c, r in zip(cases, per_case.values()) if not c.must_refuse and not r["missing"]]
    facts = col("fact_recall")
    metrics = {
        "tool_accuracy": _rate(col("tool_correct")),
        "grounded_rate": _rate(col("grounded")),
        "refusal_recall": _rate(col("refusal_correct")),
        "over_refusal_rate": _rate(over),
        "fact_recall": (sum(facts) / len(facts)) if facts else None,
        "latency_p95_ms": p95(col("latency_ms")),
    }

    categories: dict[str, dict] = {}
    names = sorted({c.category for c in cases} | set((config.get("categories") or {}).keys()))
    for name in names:
        rows = [r for r in per_case.values() if r["category"] == name]
        passed = sum(1 for r in rows if r["passed"])
        categories[name] = {
            "cases": len(rows),
            "passed": passed,
            "pass_rate": (passed / len(rows)) if rows else None,
        }

    return {
        "run": str(run_dir),
        "cases": per_case,
        "metrics": metrics,
        "categories": categories,
        "missing": sorted(cid for cid, r in per_case.items() if r["missing"]),
        "errors": errors,
    }


def compare_runs(baseline: dict, candidate: dict, config: dict) -> dict:
    reg_cfg = config.get("regression") or {}
    deltas: dict[str, float | None] = {}
    regressions: list[str] = []
    for m in METRICS:
        b = baseline["metrics"].get(m)
        c = candidate["metrics"].get(m)
        deltas[m] = None if (b is None or c is None) else c - b
        if m not in reg_cfg:
            continue
        tol = float(reg_cfg[m])
        if b is None:
            continue
        if c is None:
            regressions.append(m)
        elif m in HIGHER_IS_BETTER and (b - c) > tol + EPS:
            regressions.append(m)
        elif m in LOWER_IS_BETTER and (c - b) > tol + EPS:
            regressions.append(m)
        elif m in RELATIVE_LOWER_IS_BETTER and c > b * (1 + tol) + EPS:
            regressions.append(m)

    case_regressions = sorted(
        cid
        for cid, rb in baseline["cases"].items()
        if rb["passed"] and cid in candidate["cases"] and not candidate["cases"][cid]["passed"]
    )
    return {"deltas": deltas, "regressions": regressions, "case_regressions": case_regressions}


def gate(candidate: dict, comparison: dict | None, config: dict) -> dict:
    reasons: list[str] = []
    th = config.get("thresholds") or {}
    for key, limit in th.items():
        kind, _, metric = key.partition("_")
        value = candidate["metrics"].get(metric)
        if value is None:
            reasons.append(f"{metric}: no applicable cases (threshold {key}={limit})")
        elif kind == "min" and value < limit - EPS:
            reasons.append(f"{metric}={value:.3f} below {key}={limit}")
        elif kind == "max" and value > limit + EPS:
            reasons.append(f"{metric}={value:.3f} above {key}={limit}")

    for name, floor in (config.get("categories") or {}).items():
        cat = candidate["categories"].get(name)
        if not cat or not cat["cases"]:
            reasons.append(f"category {name}: no test cases (no coverage)")
        elif cat["pass_rate"] < floor - EPS:
            reasons.append(f"category {name}: pass rate {cat['pass_rate']:.3f} below {floor}")

    max_bad = int(config.get("max_malformed_records", 0))
    if len(candidate["errors"]) > max_bad:
        reasons.append(f"{len(candidate['errors'])} malformed transcript record(s) (max {max_bad})")

    if comparison is not None:
        for m in comparison["regressions"]:
            reasons.append(f"regression vs baseline: {m} (delta {comparison['deltas'].get(m)})")
        blocking = set((config.get("regression") or {}).get("block_case_regressions_in") or [])
        for cid in comparison["case_regressions"]:
            if candidate["cases"][cid]["category"] in blocking:
                reasons.append(f"case regression in blocking category: {cid}")

    return {"passed": not reasons, "reasons": reasons}


# ---------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="release_gate")
    ap.add_argument("--testset", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--baseline")
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    try:
        cases = load_testset(args.testset)
        config = load_config(args.config)
    except (OSError, ValueError, KeyError, yaml.YAMLError) as exc:
        print(f"error: {exc}")
        return 2
    cand = evaluate_run(cases, args.candidate, config)
    base = evaluate_run(cases, args.baseline, config) if args.baseline else None
    comp = compare_runs(base, cand, config) if base else None
    decision = gate(cand, comp, config)
    report = {"candidate": cand, "baseline": base, "comparison": comp, "gate": decision}
    Path(args.out).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("GATE " + ("PASS" if decision["passed"] else "FAIL"))
    for r in decision["reasons"]:
        print(" - " + r)
    return 0 if decision["passed"] else 1
