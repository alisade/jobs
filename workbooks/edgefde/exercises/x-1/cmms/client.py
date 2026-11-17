"""CMMS work-order client.

TODO: implement CMMSClient to the contract in README.md: a timeout on every call, retries with
full-jitter exponential backoff on retryable errors only, Retry-After (seconds or HTTP date), a retry
budget, an idempotency key derived from the anomaly, OAuth client credentials with refresh, and
pagination. The draft below is what the prototype did: one POST, no key, no retries.
"""

from __future__ import annotations

import random
from typing import Callable, Literal

from pydantic import BaseModel


class WorkOrder(BaseModel):
    id: str
    asset_id: str
    title: str
    priority: Literal["P1", "P2", "P3"]
    status: str
    idempotency_key: str | None = None


class CMMSError(Exception):
    pass


class PermanentError(CMMSError):
    def __init__(self, status: int, body) -> None:
        self.status, self.body = status, body
        super().__init__(f"CMMS returned {status}: {body}")


class RetryBudgetExceeded(CMMSError):
    pass


class CMMSClient:
    def __init__(self, transport, client_id: str, client_secret: str, clock: Callable[[], float],
                 sleep: Callable[[float], None], rng: random.Random | None = None, max_attempts: int = 6,
                 base_delay: float = 0.5, max_delay: float = 20.0, timeout: float = 5.0,
                 retry_budget_s: float = 60.0) -> None:
        self.t, self.cid, self.secret = transport, client_id, client_secret
        self.clock, self.sleep = clock, sleep
        self.rng = rng or random.Random(0)
        self.max_attempts, self.base, self.cap = max_attempts, base_delay, max_delay
        self.timeout, self.budget = timeout, retry_budget_s

    @staticmethod
    def idempotency_key(machine: str, alert_window_start: str) -> str:
        raise NotImplementedError("TODO")

    def raise_work_order(self, machine: str, alert_window_start: str, title: str, priority: str = "P2") -> WorkOrder:
        tok = self.t.request("POST", "/oauth/token", {}, {"grant_type": "client_credentials",
                                                          "client_id": self.cid, "client_secret": self.secret}).body
        r = self.t.request("POST", "/api/v2/work-orders", {"Authorization": f"Bearer {tok['access_token']}"},
                           {"asset_id": machine, "title": title, "priority": priority, "source": "edge-kit"})
        return WorkOrder.model_validate(r.body)

    def list_work_orders(self, asset_id: str) -> list[WorkOrder]:
        raise NotImplementedError("TODO")
