"""Test helpers."""
from datetime import datetime, timezone


class Clock:
    def __init__(self):
        self.now = datetime(2026, 11, 2, 9, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.now


def hdrs(key=None, tenant="bu-amer"):
    h = {"X-Tenant-Id": tenant}
    if key is not None:
        h["Idempotency-Key"] = key
    return h
