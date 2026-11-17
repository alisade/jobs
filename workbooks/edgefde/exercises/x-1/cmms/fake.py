"""In-process fake of the plant's CMMS REST API, a fake clock and a fault-injecting transport
(complete: do not edit).

API (JSON bodies):
  POST /oauth/token            form: grant_type=client_credentials, client_id, client_secret
                               -> 200 {"access_token", "token_type": "Bearer", "expires_in": 300}
  POST /api/v2/work-orders     headers: Authorization: Bearer <t>, Idempotency-Key: <key> (optional)
                               body {"asset_id", "title", "priority": "P1"|"P2"|"P3", "source"}
                               -> 201 created; with a key already seen -> 200 and the SAME order
                               -> 422 on a bad body, 401 on a missing or expired token
  GET  /api/v2/work-orders?asset_id=X&page_token=T
                               -> 200 {"items": [...], "next_page_token": str | null}, 3 per page

Transport.request(method, path, headers, body, timeout) returns Response or raises
TransportTimeout. Faults are scripted per request with Transport.script([...]):
  "500", "503", "429", "429-date" (Retry-After as an HTTP date), "timeout" (no request reached the
  server), "commit-timeout" (the server processed the request, the response was lost), None (normal).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from email.utils import formatdate
from urllib.parse import parse_qs, urlparse


class TransportTimeout(TimeoutError):
    pass


@dataclass
class Response:
    status: int
    headers: dict = field(default_factory=dict)
    body: dict | None = None


class FakeClock:
    def __init__(self, start: float = 1_793_000_000.0) -> None:
        self.now = start
        self.sleeps: list[float] = []

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        if seconds < 0:
            raise ValueError("negative sleep")
        self.sleeps.append(seconds)
        self.now += seconds


class FakeCMMS:
    CLIENT_ID, CLIENT_SECRET = "edge-kit", "s3cret-from-vault"

    def __init__(self, clock: FakeClock, token_ttl: int = 300) -> None:
        self.clock, self.token_ttl = clock, token_ttl
        self.tokens: dict[str, float] = {}
        self.orders: list[dict] = []
        self.by_key: dict[str, dict] = {}
        self.token_requests = 0

    def handle(self, method: str, path: str, headers: dict, body) -> Response:
        u = urlparse(path)
        if method == "POST" and u.path == "/oauth/token":
            self.token_requests += 1
            f = body or {}
            if f.get("grant_type") != "client_credentials" or f.get("client_id") != self.CLIENT_ID \
                    or f.get("client_secret") != self.CLIENT_SECRET:
                return Response(401, {}, {"error": "invalid_client"})
            tok = f"tok-{self.token_requests}"
            self.tokens[tok] = self.clock.time() + self.token_ttl
            return Response(200, {}, {"access_token": tok, "token_type": "Bearer", "expires_in": self.token_ttl})
        auth = headers.get("Authorization", "")
        tok = auth[7:] if auth.startswith("Bearer ") else ""
        if tok not in self.tokens or self.tokens[tok] <= self.clock.time():
            return Response(401, {"WWW-Authenticate": 'Bearer error="invalid_token"'}, {"error": "invalid_token"})
        if method == "POST" and u.path == "/api/v2/work-orders":
            b = body or {}
            if not b.get("asset_id") or b.get("priority") not in ("P1", "P2", "P3") or not b.get("title"):
                return Response(422, {}, {"error": "validation", "detail": "asset_id, title, priority P1-P3 required"})
            key = headers.get("Idempotency-Key")
            if key and key in self.by_key:
                return Response(200, {}, dict(self.by_key[key]))
            wo = {"id": f"WO-{60000 + len(self.orders)}", "asset_id": b["asset_id"], "title": b["title"],
                  "priority": b["priority"], "status": "draft", "idempotency_key": key}
            self.orders.append(wo)
            if key:
                self.by_key[key] = wo
            return Response(201, {}, dict(wo))
        if method == "GET" and u.path == "/api/v2/work-orders":
            q = parse_qs(u.query)
            items = [o for o in self.orders if o["asset_id"] == q.get("asset_id", [""])[0]]
            start = int(q.get("page_token", ["0"])[0])
            page = items[start:start + 3]
            nxt = str(start + 3) if start + 3 < len(items) else None
            return Response(200, {}, {"items": [dict(o) for o in page], "next_page_token": nxt})
        return Response(404, {}, {"error": "not found"})


class Transport:
    def __init__(self, server: FakeCMMS) -> None:
        self.server = server
        self.faults: list[str | None] = []
        self.calls: list[dict] = []

    def script(self, faults: list[str | None]) -> None:
        self.faults = list(faults)

    def request(self, method: str, path: str, headers: dict | None = None, body=None,
                timeout: float | None = None) -> Response:
        headers = dict(headers or {})
        self.calls.append({"method": method, "path": path, "headers": headers, "timeout": timeout,
                           "at": self.server.clock.time()})
        fault = self.faults.pop(0) if self.faults else None
        if path.startswith("/oauth/"):
            fault = None if fault in (None, "commit-timeout") else fault
        if fault == "timeout":
            raise TransportTimeout("connect timeout")
        if fault in ("500", "503"):
            return Response(int(fault), {}, {"error": "upstream"})
        if fault == "429":
            return Response(429, {"Retry-After": "7"}, {"error": "rate limited"})
        if fault == "429-date":
            return Response(429, {"Retry-After": formatdate(self.server.clock.time() + 11, usegmt=True)}, {})
        resp = self.server.handle(method, path, headers, json.loads(json.dumps(body)) if body is not None else None)
        if fault == "commit-timeout":
            raise TransportTimeout("read timeout")
        return resp
