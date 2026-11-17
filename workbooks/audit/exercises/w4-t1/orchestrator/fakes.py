"""Local stand-ins: the MFH GRC issues API (with fault injection), an Azure append blob and a
simulated clock. These model the real systems faithfully; the bug is not in this file.

FakeGrcServer.handle() behaves like POST /api/v2/issues on the GRC system:
  - 201 + new issue for a new Idempotency-Key, 200 + the original issue for a key it has seen;
  - faults by request number (1-based): "429" (rate limited, Retry-After), "timeout" (request lost
    before the server saw it), "commit_timeout" (the server COMMITS the issue, then the response
    is lost and the client sees a timeout), "commit_crash" (the server commits, then the worker
    process dies before it reads the response).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field


class GrcTimeout(Exception):
    """The HTTP client gave up waiting for the response (read timeout)."""


class ProcessCrash(BaseException):
    """The worker process died (OOM kill, node recycle). BaseException: nothing should catch it."""


class Clock:
    def __init__(self, start: float = 1_790_820_000.0):  # 2026-10-01T02:00:00Z
        self.now = start

    def sleep(self, seconds: float) -> None:
        self.now += seconds

    def iso(self) -> str:
        import datetime as dt
        return dt.datetime.fromtimestamp(self.now, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class FakeGrcServer:
    faults: dict[int, str] = field(default_factory=dict)
    clock: Clock = field(default_factory=Clock)
    issues: list[dict] = field(default_factory=list)
    log: list[str] = field(default_factory=list)
    n: int = 0

    def handle(self, method: str, path: str, headers: dict, body: dict) -> tuple[int, dict, dict]:
        self.n += 1
        rid = f"r-{self.n:04d}"
        self.clock.sleep(0.4)
        fault = self.faults.get(self.n)
        key = headers.get("Idempotency-Key")
        if fault == "timeout":
            self.log.append(f"{self.clock.iso()} req={rid} {method} {path} -> (no request received: connection reset)")
            raise GrcTimeout(f"{rid}: read timed out")
        if fault == "429":
            self.log.append(f"{self.clock.iso()} req={rid} {method} {path} key={key} -> 429 rate limited, Retry-After: 2")
            return 429, {"Retry-After": "2", "x-request-id": rid}, {"error": "rate_limited"}
        if not key:
            self.log.append(f"{self.clock.iso()} req={rid} {method} {path} -> 400 missing Idempotency-Key")
            return 400, {"x-request-id": rid}, {"error": "Idempotency-Key required"}
        for i in self.issues:
            if i["idempotency_key"] == key:
                self.log.append(f"{self.clock.iso()} req={rid} {method} {path} key={key} -> 200 replay {i['issue_id']}")
                return 200, {"x-request-id": rid}, {"issue_id": i["issue_id"]}
        issue = {"issue_id": f"ISS-{7400 + len(self.issues)}", "idempotency_key": key, "request_id": rid,
                 "sample_id": body.get("sample_id"), "run_id": body.get("run_id"), "payload": json.loads(json.dumps(body))}
        self.issues.append(issue)
        if fault in ("commit_timeout", "commit_crash"):
            self.clock.sleep(30)
            self.log.append(f"{self.clock.iso()} req={rid} {method} {path} key={key} -> 201 {issue['issue_id']} "
                            f"(response not delivered: client disconnected after 30.0s)")
            if fault == "commit_crash":
                raise ProcessCrash(f"worker killed while waiting for {rid}")
            raise GrcTimeout(f"{rid}: read timed out after 30s")
        self.log.append(f"{self.clock.iso()} req={rid} {method} {path} key={key} -> 201 {issue['issue_id']}")
        return 201, {"x-request-id": rid}, {"issue_id": issue["issue_id"]}


class FakeAppendBlob:
    """Mirrors azure.storage.blob.BlobClient for an append blob: append_block() adds bytes at the end."""

    def __init__(self, name: str):
        self.name = name
        self._data = b""
        self.appends = 0

    def append_block(self, data: bytes | str) -> dict:
        self._data += data.encode() if isinstance(data, str) else data
        self.appends += 1
        return {"blob_append_offset": str(len(self._data))}

    def download_blob(self):
        data = self._data

        class _D:
            def readall(self_inner) -> bytes:
                return data
        return _D()

    def rows(self) -> list[dict]:
        return [json.loads(x) for x in self._data.decode().splitlines() if x.strip()]
