"""Helpers shared by the visible tests: a manual clock and a client wired to respx routes."""

from __future__ import annotations

import httpx
import respx

from risk_client import CircuitBreaker, HalyardRiskClient

TOKEN_URL = "https://auth.halyard.example/oauth2/token"
RISK_BASE = "https://risk.halyard.example"
ASSESS_URL = RISK_BASE + "/v1/assess"
CLIENT_ID = "northwind-agent"
CLIENT_SECRET = "s3cr3t-not-real"
PAYLOAD = {"hook": "add_to_cart", "session_digest": "a1b2c3d4e5f60718", "quantity": 1}
ALLOW = {"decision": "allow", "decision_id": "dec-1", "reason_codes": []}


class FakeClock:
    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def token_json(value: str = "tok-1", expires_in: int = 300) -> dict:
    return {"access_token": value, "token_type": "Bearer", "expires_in": expires_in}


def make_client(
    http: httpx.AsyncClient,
    clock: FakeClock,
    *,
    budget_s: float = 0.25,
    token_skew_s: float = 30.0,
    breaker: CircuitBreaker | None = None,
) -> HalyardRiskClient:
    return HalyardRiskClient(
        http=http,
        base_url=RISK_BASE,
        token_url=TOKEN_URL,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        budget_s=budget_s,
        token_skew_s=token_skew_s,
        breaker=breaker or CircuitBreaker(failure_threshold=3, reset_timeout_s=30.0, clock=clock),
        clock=clock,
    )


def routes(router: respx.MockRouter):
    """(token_route, assess_route) registered on ``router``; set side effects per test."""
    return router.post(TOKEN_URL), router.post(ASSESS_URL)
