"""The AgentCore Runtime HTTP contract (protocol HTTP, port 8080, host 0.0.0.0):

    POST /invocations   JSON in, JSON out
    GET  /ping          {"status": "Healthy" | "HealthyBusy", "time_of_last_update": <unix seconds>}

The runtime sends the session id in the X-Amzn-Bedrock-AgentCore-Runtime-Session-Id header and,
because Authorization is on the request header allowlist, the caller's validated bearer token.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable

from botocore.exceptions import ClientError

from . import memory, model
from .identity import bearer_claims, header

log = logging.getLogger("tidewater.runtime")

SESSION_HEADER = "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id"


DEGRADE_CODES = {"ThrottledException", "ServiceException", "RetryableConflictException"}
SESSION_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9-_]{0,99}$")


class AgentApp:
    def __init__(self, memory_client: Any, memory_id: str, *, top_k: int = 5,
                 model_fn: Callable[[str, list[str]], str] = model.answer,
                 clock: Callable[[], float] = time.time) -> None:
        self.memory_client = memory_client
        self.memory_id = memory_id
        self.top_k = top_k
        self.model_fn = model_fn
        self.clock = clock
        self._lock = threading.Lock()
        self._in_flight = 0
        self._status = "Healthy"
        self._changed_at = int(clock())

    # ---- ping -------------------------------------------------------------------------
    def _set_in_flight(self, delta: int) -> None:
        with self._lock:
            self._in_flight += delta
            status = "HealthyBusy" if self._in_flight > 0 else "Healthy"
            if status != self._status:      # time_of_last_update moves only on a real change
                self._status = status
                self._changed_at = int(self.clock())

    def ping(self) -> tuple[int, dict]:
        with self._lock:
            return 200, {"status": self._status, "time_of_last_update": self._changed_at}

    # ---- invocations ------------------------------------------------------------------
    def invoke(self, headers: dict, body: bytes) -> tuple[int, dict]:
        claims = bearer_claims(headers)
        if claims is None:
            return 401, {"error": "unauthorized"}
        try:
            actor = memory.actor_id(claims)
        except memory.IdentityError as e:
            return 403, {"error": "forbidden", "detail": str(e)}
        session_id = header(headers, SESSION_HEADER)
        if not session_id or not SESSION_RE.match(session_id):
            return 400, {"error": "missing_session", "detail": f"{SESSION_HEADER} header is required"}
        try:
            payload = json.loads(body or b"{}")
        except ValueError:
            return 400, {"error": "invalid_json"}
        prompt = payload.get("prompt") if isinstance(payload, dict) else None
        if not isinstance(prompt, str) or not prompt.strip():
            return 400, {"error": "missing_prompt"}
        ignored = sorted(k for k in payload if k in ("actor_id", "actorId", "tenant", "tenant_id", "user_id", "session_id"))
        if ignored:
            log.warning(json.dumps({"event": "ignored_identity_fields", "fields": ignored, "actor": actor}))

        self._set_in_flight(+1)
        try:
            memory_state = "used"
            try:
                memories = memory.recall(self.memory_client, self.memory_id, claims, prompt, self.top_k)
            except ClientError as e:
                if e.response["Error"]["Code"] not in DEGRADE_CODES:
                    raise
                log.warning(json.dumps({"event": "memory_degraded", "op": "RetrieveMemoryRecords",
                                        "code": e.response["Error"]["Code"], "actor": actor}))
                memories, memory_state = [], "degraded"
            text = self.model_fn(prompt, memories)
            try:
                memory.remember(self.memory_client, self.memory_id, claims, session_id, prompt, text,
                                dt.datetime.fromtimestamp(self.clock(), tz=dt.timezone.utc))
            except ClientError as e:
                if e.response["Error"]["Code"] not in DEGRADE_CODES:
                    raise
                log.warning(json.dumps({"event": "memory_degraded", "op": "CreateEvent",
                                        "code": e.response["Error"]["Code"], "actor": actor}))
                memory_state = "degraded"
            return 200, {"response": text, "status": "success", "memory": memory_state, "session_id": session_id}
        except ClientError as e:
            log.error(json.dumps({"event": "memory_error", "code": e.response["Error"]["Code"], "actor": actor}))
            return 500, {"error": "internal_error"}
        finally:
            self._set_in_flight(-1)


def make_server(app: AgentApp, host: str = "0.0.0.0", port: int = 8080) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, payload: dict) -> None:
            data = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/ping":
                self._send(*app.ping())
            else:
                self._send(404, {"error": "not_found"})

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/invocations":
                self._send(404, {"error": "not_found"})
                return
            n = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(n) if n else b""
            self._send(*app.invoke(dict(self.headers.items()), body))

        def log_message(self, fmt: str, *args: Any) -> None:
            log.debug(fmt, *args)

    return ThreadingHTTPServer((host, port), Handler)


if __name__ == "__main__":
    import boto3
    cfg = json.load(open("config.json"))
    srv = make_server(AgentApp(boto3.client("bedrock-agentcore", region_name=cfg["region"]), cfg["memory_id"]))
    srv.serve_forever()
