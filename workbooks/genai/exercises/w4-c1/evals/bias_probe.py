"""Bias probes for the Kestrel gift recommender.

This is the eval that has been running in CI since the beta. It compares group averages and it has
always passed. Your task (README.md) is to replace it with a paired analysis that would have caught
what the support team found.

CLI:
  python -m evals.bias_probe --probes data/probes.json --responses data/responses.jsonl \
      --config config.json --out report.json --md report.md
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

METRICS = ("price", "refusal", "tone")
_PRICE = re.compile(r"\$([0-9]+(?:\.[0-9]{2})?)")


def load_probes(path: str | Path) -> list[dict]:
    return json.loads(Path(path).read_text())["probes"]


def load_responses(path: str | Path) -> tuple[dict[str, list[dict]], int]:
    """Return ({probe_id: [samples]}, malformed_line_count)."""
    # TODO: skip blank lines; count and skip malformed lines instead of crashing
    out: dict[str, list[dict]] = defaultdict(list)
    for line in Path(path).read_text().splitlines():
        row = json.loads(line)
        out[row["probe_id"]].append(row)
    return dict(out), 0


def is_refusal(sample: dict, markers: list[str]) -> bool:
    # TODO: README "Metrics" defines a refusal
    return False


def tone_score(text: str, lexicon: dict) -> float:
    # TODO: README "Metrics"
    return 0.0


def probe_metrics(samples: list[dict], lexicon: dict, markers: list[str]) -> dict:
    """Metrics for one probe over its samples. See README "Metrics"."""
    prices = [float(m) * 100 for s in samples for m in _PRICE.findall(s.get("text", ""))]
    return {
        "price": statistics.fmean(prices) if prices else None,
        "refusal": 0.0,
        "tone": 0.0,
        "n": len(samples),
    }


def sign_flip_test(diffs: list[float], n_perm: int = 10000, seed: int = 0) -> float | None:
    """Two-sided paired permutation (sign-flip) test of mean(diffs) == 0. See README."""
    raise NotImplementedError


def bootstrap_ci(diffs: list[float], n_boot: int = 2000, seed: int = 0, alpha: float = 0.05) -> tuple[float, float] | None:
    """Percentile bootstrap CI of mean(diffs). See README."""
    raise NotImplementedError


def analyze(probes: list[dict], responses: dict[str, list[dict]], config: dict, lexicon: dict,
            malformed: int = 0) -> dict:
    markers = [m.lower() for m in config.get("refusal_markers", [])]
    metrics = {p["probe_id"]: probe_metrics(responses.get(p["probe_id"], []), lexicon, markers) for p in probes}
    aggregate: dict = {}
    violations = []
    for dim in sorted({p["dimension"] for p in probes}):
        aggregate[dim] = {}
        for metric in METRICS:
            vals = {"a": [], "b": []}
            for p in probes:
                v = metrics[p["probe_id"]][metric]
                if p["dimension"] == dim and v is not None:
                    vals[p["group"]].append(v)
            ga = statistics.fmean(vals["a"]) if vals["a"] else None
            gb = statistics.fmean(vals["b"]) if vals["b"] else None
            diff = gb - ga if ga is not None and gb is not None else None
            aggregate[dim][metric] = {"group_a": ga, "group_b": gb, "diff": diff}
            cfg = config["metrics"][metric]
            if diff is not None and cfg["gated"] and abs(diff) >= cfg["threshold"]:
                violations.append(f"{dim}/all/{metric}")
    # TODO: paired results per dimension x category x metric, missing probes, see README "Report"
    return {
        "version": 1,
        "n_probes": len(probes),
        "n_samples": sum(len(v) for v in responses.values()),
        "malformed_lines": malformed,
        "missing_probes": [],
        "aggregate": aggregate,
        "results": [],
        "violations": violations,
    }


def render_markdown(report: dict) -> str:
    # TODO: the system card section, see README "Report"
    return "## Bias probe results\n\nGate: " + ("FAILED" if report["violations"] else "passed") + ".\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="bias probes")
    ap.add_argument("--probes", default="data/probes.json")
    ap.add_argument("--responses", default="data/responses.jsonl")
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--lexicon", default="data/tone_lexicon.json")
    ap.add_argument("--out", default="report.json")
    ap.add_argument("--md", default="report.md")
    a = ap.parse_args(argv)
    probes = load_probes(a.probes)
    responses, bad = load_responses(a.responses)
    config = json.loads(Path(a.config).read_text())
    lexicon = json.loads(Path(a.lexicon).read_text())
    report = analyze(probes, responses, config, lexicon, bad)
    Path(a.out).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    Path(a.md).write_text(render_markdown(report))
    print(f"bias_probe: {len(report['violations'])} gated violation(s)")
    # TODO: exit 1 when a gated metric has a violation (the CI gate)
    return 0


if __name__ == "__main__":
    sys.exit(main())
