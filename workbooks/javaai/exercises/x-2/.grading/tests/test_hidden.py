import datetime as dt
import random

import pytest

from kanban import forecast as f

ROWS = f.load()
TP = f.weekly_throughput(ROWS, dt.date(2026, 8, 3), 12)


def test_weekly_throughput_including_zero_week():
    assert TP == [7, 4, 4, 4, 5, 0, 7, 8, 4, 3, 6, 5]


def test_week_boundaries_are_monday_to_sunday():
    rows = [{"done": dt.date(2026, 8, 9), "started": dt.date(2026, 8, 1)},   # Sunday of week 1
            {"done": dt.date(2026, 8, 10), "started": dt.date(2026, 8, 1)},  # Monday of week 2
            {"done": dt.date(2026, 7, 30), "started": dt.date(2026, 7, 1)}]  # before the window
    assert f.weekly_throughput(rows, dt.date(2026, 8, 3), 2) == [1, 1]


def test_cycle_times_and_percentiles():
    ct = f.cycle_times(ROWS)
    assert len(ct) == 57
    assert (f.percentile(ct, 50), f.percentile(ct, 85)) == (6, 12)
    assert f.percentile([5, 1, 4, 2, 3], 100) == 5 and f.percentile([9], 1) == 9


def test_simulation_is_seeded_and_sampled_with_replacement():
    assert f.simulate_weeks([3, 0, 5], 10, 5, random.Random(7)) == [5, 3, 4, 6, 3]


def test_simulation_rejects_empty_history_and_caps():
    with pytest.raises(ValueError):
        f.simulate_weeks([0, 0, 0], 10, 3, random.Random(1))
    assert f.simulate_weeks([0, 1], 1000, 2, random.Random(1), cap=50) == [50, 50]


def test_finish_dates_by_confidence():
    weeks = f.simulate_weeks(TP, 40, 10000, random.Random(2026))
    start = dt.date(2026, 10, 26)
    assert [f.finish_date(start, weeks, c) for c in (50, 85, 95)] == [dt.date(2026, 12, 28), dt.date(2027, 1, 4), dt.date(2027, 1, 11)]


def test_items_by_uses_the_low_end():
    assert f.items_by(TP, 4, 10000, random.Random(2026), 85) == 15
    assert f.items_by([3, 0, 5], 2, 7, random.Random(7), 85) == 5


def test_littles_law():
    assert f.littles_law_cycle_time(6, 0.75) == 8
    with pytest.raises(ValueError):
        f.littles_law_cycle_time(6, 0)
