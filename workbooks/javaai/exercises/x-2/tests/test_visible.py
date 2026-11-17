import datetime as dt

from kanban import forecast as f


def test_throughput_has_one_number_per_week():
    tp = f.weekly_throughput(f.load(), dt.date(2026, 8, 3), 12)
    assert len(tp) == 12 and sum(tp) == len(f.load())


def test_percentile_simple():
    assert f.percentile([1, 2, 3, 4], 50) == 2
