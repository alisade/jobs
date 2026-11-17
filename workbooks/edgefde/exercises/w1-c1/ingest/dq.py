"""Data quality checks for one archived day. Any issue fails the backfill run.

TODO: implement check_day (README "Data quality").
"""

from __future__ import annotations

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
    raise NotImplementedError("TODO")
