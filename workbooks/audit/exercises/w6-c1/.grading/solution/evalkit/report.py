"""Report, markdown summary and regression gate for one control."""

from __future__ import annotations

from . import metrics as m


def build_report(labels: dict[str, dict], runs: list[dict], prices: dict, *, expected_runs: int = 5, control: str = "CM-03") -> dict:
    present = {(r["sample_id"], r["run"]) for r in runs}
    missing = [{"sample_id": s, "run": k} for s in sorted(labels) for k in range(1, expected_runs + 1) if (s, k) not in present]
    unlabeled = sorted({r["sample_id"] for r in runs} - set(labels))
    return {
        "control": control,
        "samples": len(labels),
        "runs_scored": len(m.scored_rows(labels, runs)),
        "missing_runs": missing,
        "unlabeled_samples": unlabeled,
        "accuracy": {f: m.accuracy(labels, runs, f) for f in m.FIELDS},
        "exceptions": {f: m.exception_scores(labels, runs, f) for f in m.FIELDS},
        "consistency": {
            "agreement": m.agreement(runs, "overall"),
            "fleiss_kappa": m.fleiss_kappa(runs, "overall", expected_runs),
        },
        "cost": m.cost(runs, prices),
        "latency": m.latency(runs),
    }


def gate(report: dict, baseline: dict, thresholds: dict) -> list[str]:
    failures = []
    rec = report["exceptions"]["overall"]["recall"]
    if rec is None:
        failures.append("exception recall undefined: the eval set has no labeled exceptions")
    elif rec < thresholds["min_exception_recall"]:
        failures.append(f"exception recall {rec:.3f} < {thresholds['min_exception_recall']}")
    acc = report["accuracy"]["overall"]
    floor = baseline["accuracy_overall"] - thresholds["max_accuracy_drop"]
    if acc is None or acc < floor - 1e-12:
        failures.append(f"overall accuracy {acc} < baseline {baseline['accuracy_overall']} - {thresholds['max_accuracy_drop']}")
    return failures


def _f(x, pct=False):
    if x is None:
        return "n/a"
    return f"{100 * x:.1f}%" if pct else f"{x:.3f}"


def to_markdown(report: dict) -> str:
    lines = [f"# Eval report: {report['control']}", "",
             f"Samples: {report['samples']}; runs scored: {report['runs_scored']}; missing runs: {len(report['missing_runs'])}; "
             f"unlabeled samples: {len(report['unlabeled_samples'])}", "",
             "| Field | Accuracy | Exception recall | Exception precision | Exceptions (support) |", "|---|---|---|---|---|"]
    for f in m.FIELDS:
        e = report["exceptions"][f]
        lines.append(f"| {f} | {_f(report['accuracy'][f], True)} | {_f(e['recall'], True)} | {_f(e['precision'], True)} | {e['support']} |")
    c = report["consistency"]
    lines += ["", f"Consistency (overall): mean modal agreement {_f(c['agreement']['mean_modal_agreement'], True)}, "
              f"fully consistent samples {_f(c['agreement']['fully_consistent_share'], True)}, Fleiss kappa {_f(c['fleiss_kappa']['kappa'])} "
              f"over {c['fleiss_kappa']['subjects']} samples", "",
              f"Cost: ${report['cost']['total_usd']:.4f} total, ${report['cost']['per_100_samples_usd'] or 0:.4f} per 100 samples; "
              f"latency p50 {report['latency']['p50_ms']} ms, p95 {report['latency']['p95_ms']} ms", ""]
    if "gate" in report:
        lines.append("Gate: " + ("PASSED" if report["gate"]["passed"] else "FAILED - " + "; ".join(report["gate"]["failures"])))
        lines.append("")
    return "\n".join(lines)
