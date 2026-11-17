"""Data quality checks for one archived day. Any issue fails the backfill run."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date

from .models import FeatureRecord

RMS_LIMIT_G = 50.0


@dataclass(frozen=True)
class Issue:
    check: str
    detail: str


class DataQualityError(RuntimeError):
    def __init__(self, issues: list[Issue]):
        self.issues = issues
        super().__init__("; ".join(f"{i.check}: {i.detail}" for i in issues))


def check_day(records: list[FeatureRecord], day: date, expected_devices: list[str],
              window_s: int = 60, min_completeness: float = 0.95, max_outlier_rate: float = 0.01) -> list[Issue]:
    issues: list[Issue] = []
    iso = day.isoformat()
    outside = [r for r in records if r.window_start.date() != day]
    if outside:
        issues.append(Issue("in_partition", f"{len(outside)} records outside {iso}"))
    inside = [r for r in records if r.window_start.date() == day]
    distinct = {r.key for r in inside}
    per_dev = Counter(dev for dev, _ in distinct)
    expected = 86400 // window_s
    for dev in expected_devices:
        n = per_dev.get(dev, 0)
        if n == 0:
            issues.append(Issue("device_present", f"{dev} has no records on {iso}"))
        elif n / expected < min_completeness:
            issues.append(Issue("completeness", f"{dev} has {n}/{expected} windows ({n / expected:.1%})"))
    unknown = sorted(set(per_dev) - set(expected_devices))
    if unknown:
        issues.append(Issue("unknown_device", ", ".join(unknown)))
    if inside:
        rate = sum(1 for r in inside if r.rms > RMS_LIMIT_G) / len(inside)
        if rate > max_outlier_rate:
            issues.append(Issue("rms_range", f"{rate:.2%} of windows have rms > {RMS_LIMIT_G} g"))
    return issues
