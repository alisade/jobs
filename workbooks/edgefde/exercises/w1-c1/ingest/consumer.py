"""Consumer loop for topic vibration.features.

TODO: poll, validate, write, and only then commit offsets. Invalid messages go to
quarantine (with source "<topic>/<partition>/<offset>") and do not block the
partition. See README "Consumer".
"""

from __future__ import annotations

from dataclasses import dataclass

from .broker import Consumer
from .store import FeatureStore


@dataclass
class BatchResult:
    polled: int
    written: int
    quarantined: int


def run_once(consumer: Consumer, store: FeatureStore, max_records: int = 500) -> BatchResult:
    raise NotImplementedError("TODO")


def run_until_idle(consumer: Consumer, store: FeatureStore, max_records: int = 500, max_batches: int = 10_000) -> BatchResult:
    """Call run_once until a poll returns nothing; return the totals."""
    raise NotImplementedError("TODO")
