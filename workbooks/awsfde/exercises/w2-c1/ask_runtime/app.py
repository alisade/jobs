"""The AgentCore Runtime HTTP contract (protocol HTTP, port 8080, host 0.0.0.0):

    POST /invocations   JSON in, JSON out
    GET  /ping          {"status": "Healthy" | "HealthyBusy", "time_of_last_update": <unix seconds>}

The runtime sends the session id in the X-Amzn-Bedrock-AgentCore-Runtime-Session-Id header and,
because Authorization is on the request header allowlist, the caller's validated bearer token.
"""

from __future__ import annotations

import json
import logging
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable

from . import memory, model
from .identity import bearer_claims, header

log = logging.getLogger("tidewater.runtime")

SESSION_HEADER = "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id"


class AgentApp:
    def __init__(self, memory_client: Any, memory_id: str, *, top_k: int = 5,
                 model_fn: Callable[[str, list[str]], str] = model.answer,
                 clock: Callable[[], float] = time.time) -> None:
        self.memory_client = memory_client
        self.memory_id = memory_id
        self.top_k = top_k
        self.model_fn = model_fn
        self.clock = clock
        # TODO: whatever state ping() needs (in-flight count, last status, time of last change)

    def ping(self) -> tuple[int, dict]:
        """TODO: 200 and {"status": "HealthyBusy"} while any invocation is in flight, else "Healthy";
        include time_of_last_update = unix seconds of the last STATUS CHANGE (not of this ping)."""
        raise NotImplementedError

    def invoke(self, headers: dict, body: bytes) -> tuple[int, dict]:
        """TODO (see README): auth and tenant from the verified claims, session id from the header,
        recall -> model -> remember, graceful degradation when Memory throttles."""
        raise NotImplementedError


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
