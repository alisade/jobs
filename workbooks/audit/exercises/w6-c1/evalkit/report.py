"""Report, markdown summary and regression gate for one control. to_markdown is complete; build_report
and gate are yours (README tasks 2 and 3)."""

from __future__ import annotations

from . import metrics as m


def build_report(labels: dict[str, dict], runs: list[dict], prices: dict, *, expected_runs: int = 5, control: str = "CM-03") -> dict:
    """Return the report dict with exactly the keys listed in the README (task 2)."""
    raise NotImplementedError("TODO: README task 2")


def gate(report: dict, baseline: dict, thresholds: dict) -> list[str]:
    """Return a list of human-readable failure reasons; empty list means the gate passed (task 3)."""
    raise NotImplementedError("TODO: README task 3")


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
