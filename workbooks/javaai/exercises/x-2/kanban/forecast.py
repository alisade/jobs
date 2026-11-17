"""Flow metrics and a Monte Carlo forecast for the tutor portfolio board.

    python -m kanban.forecast      # forecast for the remaining backlog
"""

from __future__ import annotations

import csv
import datetime as dt
import math
import random
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "done_items.csv"


def load(path: Path = DATA) -> list[dict]:
    with open(path, newline="") as f:
        return [{"item": r["item"], "started": dt.date.fromisoformat(r["started"]), "done": dt.date.fromisoformat(r["done"]),
                 "type": r["type"]} for r in csv.DictReader(f)]


def weekly_throughput(rows: list[dict], first_monday: dt.date, weeks: int) -> list[int]:
    """Items finished in each of `weeks` weeks starting `first_monday` (Mon-Sun), zero weeks included.
    TODO(x-2)"""
    return []


def cycle_times(rows: list[dict]) -> list[int]:
    """Calendar days from started to done, per item. TODO(x-2)"""
    return []


def percentile(values: list[float], p: float) -> float:
    """Nearest rank: the smallest value with at least p% of values <= it. TODO(x-2)"""
    return 0.0


def simulate_weeks(throughput: list[int], backlog: int, runs: int, rng: random.Random, cap: int = 520) -> list[int]:
    """For each run, draw weekly throughput samples with replacement (rng.choice) until the sum reaches
    `backlog`; record the number of weeks. Raise ValueError if every sample is zero. Never loop past `cap`
    weeks in a run (record cap). TODO(x-2)"""
    return []


def finish_date(start: dt.date, weeks: list[int], confidence: float) -> dt.date:
    """The date by which the work is done with `confidence` percent probability:
    start + 7 * percentile(weeks, confidence) days. TODO(x-2)"""
    return start


def items_by(throughput: list[int], weeks: int, runs: int, rng: random.Random, confidence: float) -> int:
    """How many items will be done in `weeks` weeks with `confidence` percent probability: simulate the sum
    of `weeks` samples per run and take the (100 - confidence) percentile of the sums. TODO(x-2)"""
    return 0


def littles_law_cycle_time(avg_wip: float, throughput_per_day: float) -> float:
    """Average cycle time predicted by Little's law, in days. TODO(x-2)"""
    return 0.0


def main() -> None:
    rows = load()
    tp = weekly_throughput(rows, dt.date(2026, 8, 3), 12)
    weeks = simulate_weeks(tp, 40, 10000, random.Random(2026))
    print("weekly throughput:", tp)
    for c in (50, 85, 95):
        print(f"{c}% confidence: done by {finish_date(dt.date(2026, 10, 26), weeks, c)}")
    print("items in 4 weeks at 85%:", items_by(tp, 4, 10000, random.Random(2026), 85))
    ct = cycle_times(rows)
    print("cycle time p50/p85:", percentile(ct, 50), percentile(ct, 85))


if __name__ == "__main__":
    main()
