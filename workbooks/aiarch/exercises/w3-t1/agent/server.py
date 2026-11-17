"""Lighthouse helpdesk agent container entrypoint: the AgentCore Runtime HTTP contract.

POST /invocations  (JSON in, JSON out)   GET /ping  -> {"status": "Healthy"}   port 8080.
The Strands agent is stubbed here; the contract is what matters for this exercise.
"""
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STARTED = time.time()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # noqa: N802
        if self.path == "/ping":
            self._send(200, {"status": "Healthy", "time_of_last_update": int(STARTED)})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):  # noqa: N802
        if self.path != "/invocations":
            self._send(404, {"error": "not found"})
            return
        n = int(self.headers.get("Content-Length") or 0)
        try:
            payload = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            self._send(400, {"error": "body must be JSON"})
            return
        prompt = payload.get("prompt", "")
        self._send(200, {"result": f"(stub agent) you asked: {prompt[:200]}"})

    def log_message(self, *args):
        pass


def serve(port=8080):
    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    return srv


if __name__ == "__main__":
    serve().serve_forever()
