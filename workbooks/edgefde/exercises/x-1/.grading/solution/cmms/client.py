"""CMMS work-order client: timeouts, retries with full-jitter backoff, Retry-After, a retry budget,
idempotency keys and OAuth client-credentials with refresh."""

from __future__ import annotations

import hashlib
import random
from email.utils import parsedate_to_datetime
from typing import Callable, Literal

from pydantic import BaseModel, ValidationError

from .fake import Response, TransportTimeout

RETRYABLE = {429, 500, 502, 503, 504}


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
        self._token: str | None = None
        self._expires = 0.0

    @staticmethod
    def idempotency_key(machine: str, alert_window_start: str) -> str:
        """Same anomaly -> same key, across retries, restarts and gateways."""
        return "wo-" + hashlib.sha256(f"{machine}|{alert_window_start}".encode()).hexdigest()[:32]

    # ---- auth ------------------------------------------------------------------------
    def _get_token(self, force: bool = False) -> str:
        if force or self._token is None or self.clock() >= self._expires - 30:
            r = self._send("POST", "/oauth/token", {}, {"grant_type": "client_credentials",
                                                        "client_id": self.cid, "client_secret": self.secret},
                           auth=False)
            self._token = r.body["access_token"]
            self._expires = self.clock() + float(r.body.get("expires_in", 300))
        return self._token

    # ---- core retry loop ----------------------------------------------------------------
    def _retry_after(self, r: Response) -> float | None:
        v = r.headers.get("Retry-After")
        if v is None:
            return None
        try:
            return max(0.0, float(v))
        except ValueError:
            try:
                return max(0.0, parsedate_to_datetime(v).timestamp() - self.clock())
            except (TypeError, ValueError):
                return None

    def _send(self, method: str, path: str, headers: dict, body=None, auth: bool = True) -> Response:
        slept = 0.0
        refreshed = False
        last = "no attempt"
        attempt = 0
        while attempt < self.max_attempts:
            h = dict(headers)
            if auth:
                h["Authorization"] = f"Bearer {self._get_token()}"
            try:
                r = self.t.request(method, path, h, body, timeout=self.timeout)
            except TransportTimeout as exc:
                r, last = None, f"timeout: {exc}"
            if r is not None:
                if r.status == 401 and auth and not refreshed:
                    refreshed = True
                    self._get_token(force=True)
                    continue  # a refresh is not a failed attempt
                if r.status < 400:
                    return r
                if r.status not in RETRYABLE:
                    raise PermanentError(r.status, r.body)
                last = f"HTTP {r.status}"
            attempt += 1
            if attempt >= self.max_attempts:
                break
            delay = self._retry_after(r) if r is not None else None
            if delay is None:
                delay = self.rng.uniform(0, min(self.cap, self.base * 2 ** attempt))
            if slept + delay > self.budget:
                raise RetryBudgetExceeded(f"{method} {path}: next wait {delay:.1f}s exceeds the {self.budget}s budget ({last})")
            self.sleep(delay)
            slept += delay
        raise RetryBudgetExceeded(f"{method} {path}: gave up after {self.max_attempts} attempts ({last})")

    # ---- api -------------------------------------------------------------------------
    def raise_work_order(self, machine: str, alert_window_start: str, title: str, priority: str = "P2") -> WorkOrder:
        key = self.idempotency_key(machine, alert_window_start)
        r = self._send("POST", "/api/v2/work-orders", {"Idempotency-Key": key, "Content-Type": "application/json"},
                       {"asset_id": machine, "title": title, "priority": priority, "source": "edge-kit"})
        try:
            return WorkOrder.model_validate(r.body)
        except ValidationError as exc:
            raise CMMSError(f"unexpected work order payload: {exc.errors()[0]['msg']}") from None

    def list_work_orders(self, asset_id: str) -> list[WorkOrder]:
        out: list[WorkOrder] = []
        token: str | None = None
        for _ in range(1000):
            path = f"/api/v2/work-orders?asset_id={asset_id}" + (f"&page_token={token}" if token else "")
            body = self._send("GET", path, {}).body
            out += [WorkOrder.model_validate(i) for i in body["items"]]
            token = body.get("next_page_token")
            if not token:
                break
        return out
