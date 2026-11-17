"""Local stand-ins for Azure Blob Storage and the MFH GRC system. Complete; do not edit.

FakeBlobContainer mirrors the parts of azure.storage.blob.ContainerClient that ControlPilot uses:
upload_blob(name, data, overwrite=False) raises ResourceExistsError when the blob exists (the
service enforces this with an If-None-Match: * condition), download_blob(name).readall(),
list_blobs(name_starts_with=...). Every successful write is counted in ``writes``.

FakeGrc mirrors the GRC issues API: POST /issues with an Idempotency-Key header. A repeated key
returns the issue created the first time (HTTP 200 instead of 201); a new key creates a new issue.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field


class ResourceExistsError(Exception):
    """Same name and meaning as azure.core.exceptions.ResourceExistsError (HTTP 409 BlobAlreadyExists)."""


class ResourceNotFoundError(Exception):
    """Same name and meaning as azure.core.exceptions.ResourceNotFoundError (HTTP 404)."""


class CrashInjected(RuntimeError):
    """Raised by the crash-injection hook to simulate the worker process dying."""


@dataclass
class _Downloader:
    data: bytes

    def readall(self) -> bytes:
        return self.data


@dataclass
class BlobProperties:
    name: str
    etag: str
    size: int


class FakeBlobContainer:
    def __init__(self, name: str = "workpapers"):
        self.container_name = name
        self._blobs: dict[str, bytes] = {}
        self.writes: list[str] = []

    def upload_blob(self, name: str, data: bytes | str, overwrite: bool = False) -> dict:
        raw = data.encode() if isinstance(data, str) else bytes(data)
        if name in self._blobs and not overwrite:
            raise ResourceExistsError(f"BlobAlreadyExists: {self.container_name}/{name}")
        self._blobs[name] = raw
        self.writes.append(name)
        return {"etag": '"' + hashlib.sha256(raw).hexdigest()[:16] + '"'}

    def download_blob(self, name: str) -> _Downloader:
        if name not in self._blobs:
            raise ResourceNotFoundError(f"BlobNotFound: {self.container_name}/{name}")
        return _Downloader(self._blobs[name])

    def list_blobs(self, name_starts_with: str | None = None) -> list[BlobProperties]:
        return [BlobProperties(n, '"' + hashlib.sha256(b).hexdigest()[:16] + '"', len(b))
                for n, b in sorted(self._blobs.items()) if not name_starts_with or n.startswith(name_starts_with)]


@dataclass
class Issue:
    issue_id: str
    idempotency_key: str
    payload: dict


@dataclass
class FakeGrc:
    issues: list[Issue] = field(default_factory=list)
    requests: list[dict] = field(default_factory=list)

    def create_issue(self, payload: dict, *, idempotency_key: str) -> dict:
        if not idempotency_key:
            raise ValueError("Idempotency-Key header is required")
        self.requests.append({"key": idempotency_key, "payload": json.loads(json.dumps(payload))})
        for i in self.issues:
            if i.idempotency_key == idempotency_key:
                return {"status": 200, "issue_id": i.issue_id}
        issue = Issue(f"ISS-{7000 + len(self.issues)}", idempotency_key, json.loads(json.dumps(payload)))
        self.issues.append(issue)
        return {"status": 201, "issue_id": issue.issue_id}
