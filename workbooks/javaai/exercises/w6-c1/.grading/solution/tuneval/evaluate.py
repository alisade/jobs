"""Compare candidates on the 50-item held-out set: format, correctness, grounding, cost, latency.

    python -m tuneval.evaluate
"""

from __future__ import annotations

import json
import math
import sys

from . import data


def parse_item(text: str) -> dict | None:
    """The item if `text` is a JSON object with stem (str), options (exactly 4 non-empty str),
    answerIndex (int, 0-3), explanation (str) and sectionId (str); else None."""
    try:
        obj = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(obj, dict):
        return None
    opts = obj.get("options")
    idx = obj.get("answerIndex")
    ok = (isinstance(obj.get("stem"), str) and isinstance(obj.get("explanation"), str) and isinstance(obj.get("sectionId"), str)
          and isinstance(opts, list) and len(opts) == 4 and all(isinstance(o, str) and o.strip() for o in opts)
          and isinstance(idx, int) and not isinstance(idx, bool) and 0 <= idx < 4)
    return obj if ok else None


def percentile(values: list[float], p: float) -> float:
    """Nearest-rank percentile: the smallest value with at least p% of values <= it."""
    if not values:
        raise ValueError("no values")
    s = sorted(values)
    rank = max(1, math.ceil(p / 100 * len(s)))
    return s[rank - 1]


def score(records: list[dict], heldout: list[dict], price: dict) -> dict:
    """Return {"n", "format_valid", "correct", "grounded", "cost_per_1000", "p50_ms", "p95_ms"}.

    - format_valid: share of outputs parse_item accepts
    - correct: share where the item is valid and options[answerIndex] equals the held-out "answer"
    - grounded: share where the item is valid and sectionId equals the held-out "sectionId"
    - cost_per_1000: USD for 1,000 items at the mean tokens per item (every output costs, valid or not)
    - shares rounded to 4 places, cost to 4 places, latency percentiles as ints
    Records and held-out items are matched by "id".
    """
    by_id = {h["id"]: h for h in heldout}
    n = len(records)
    valid = correct = grounded = 0
    tin = tout = 0
    lat = []
    for r in records:
        h = by_id[r["id"]]
        tin += r["inputTokens"]
        tout += r["outputTokens"]
        lat.append(r["latencyMs"])
        it = parse_item(r["output"])
        if it is None:
            continue
        valid += 1
        correct += it["options"][it["answerIndex"]].strip() == h["answer"].strip()
        grounded += it["sectionId"] == h["sectionId"]
    per_item = (tin / n) * price["input"] / 1e6 + (tout / n) * price["output"] / 1e6
    return {"n": n, "format_valid": round(valid / n, 4), "correct": round(correct / n, 4), "grounded": round(grounded / n, 4),
            "cost_per_1000": round(per_item * 1000, 4), "p50_ms": int(percentile(lat, 50)), "p95_ms": int(percentile(lat, 95))}


def pick(reports: dict[str, dict], min_valid: float = 0.95, min_correct: float = 0.85) -> str | None:
    """The cheapest candidate meeting both thresholds (ties: higher correct), or None."""
    ok = [(r["cost_per_1000"], -r["correct"], name) for name, r in reports.items()
          if r["format_valid"] >= min_valid and r["correct"] >= min_correct]
    return min(ok)[2] if ok else None


def main() -> int:
    held = data.heldout()
    models = data.candidate_models()
    prices = data.prices()
    reports = {c: score(data.candidate(c), held, prices[models[c]]) for c in data.CANDIDATES}
    for c, r in reports.items():
        print(f"{c:16} {json.dumps(r)}")
    print("pick:", pick(reports))
    return 0


if __name__ == "__main__":
    sys.exit(main())
