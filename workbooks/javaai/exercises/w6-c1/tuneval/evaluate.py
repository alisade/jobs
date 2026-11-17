"""Compare candidates on the 50-item held-out set: format, correctness, grounding, cost, latency.

    python -m tuneval.evaluate
"""

from __future__ import annotations

import json
import sys

from . import data


def parse_item(text: str) -> dict | None:
    """The item if `text` is a JSON object with stem (str), options (exactly 4 non-empty str),
    answerIndex (int, 0-3), explanation (str) and sectionId (str); else None.

    TODO(w6-c1): the notebook version only checks that it is JSON.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def percentile(values: list[float], p: float) -> float:
    """Nearest-rank percentile: the smallest value with at least p% of values <= it. TODO(w6-c1)"""
    return 0.0


def score(records: list[dict], heldout: list[dict], price: dict) -> dict:
    """Return {"n", "format_valid", "correct", "grounded", "cost_per_1000", "p50_ms", "p95_ms"}.

    - format_valid: share of outputs parse_item accepts
    - correct: share where the item is valid and options[answerIndex] equals the held-out "answer"
    - grounded: share where the item is valid and sectionId equals the held-out "sectionId"
    - cost_per_1000: USD for 1,000 items at the mean tokens per item (every output costs, valid or not)
    - shares rounded to 4 places, cost to 4 places, latency percentiles as ints
    Records and held-out items are matched by "id". TODO(w6-c1)
    """
    return {}


def pick(reports: dict[str, dict], min_valid: float = 0.95, min_correct: float = 0.85) -> str | None:
    """The cheapest candidate meeting both thresholds (ties: higher correct), or None. TODO(w6-c1)"""
    return None


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
