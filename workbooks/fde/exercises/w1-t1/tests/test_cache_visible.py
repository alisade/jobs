"""Visible tests: the symptom, measured. Every worker process must send the same cached
prefix, and the replayed morning must read from cache like the previous release did."""

from __future__ import annotations

from datetime import datetime

from w1t1_support import EXERCISE, FLAGS, prefix_in_process

from replay.simulate import replay


def test_every_worker_process_sends_the_same_static_prefix():
    seen = {prefix_in_process(seed)["digest"] for seed in (0, 1, 2, 3, 4, 5)}
    assert len(seen) == 1, f"{len(seen)} different tools+system prefixes across 6 processes"


def test_replayed_traffic_reads_from_cache_again():
    stats = replay(EXERCISE, FLAGS, datetime(2026, 10, 6, 13, 0))
    assert stats.hit_rate > 0.80, f"hit rate {stats.hit_rate:.1%} (previous release: ~89%)"
    assert stats.opening_hit_rate > 0.85, f"turn-opening reads {stats.opening_hit_rate:.1%}"
