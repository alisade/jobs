"""Woodgrove asset sync: a minimal Dataverse Web API client.

Implement the five TODO methods. Everything else (errors, TokenStore, headers, the multipart
response parser) is provided. Run `make test` for the visible tests; README lists the rules.
"""

from __future__ import annotations

import json
import random  # noqa: F401  (jitter is optional)
import time
import uuid  # noqa: F401
from dataclasses import dataclass, field
from typing import Callable, Iterator

import requests


class DataverseError(Exception):
    """Any non-success response. `status` is the HTTP status, `code` the Dataverse error code."""

    def __init__(self, status: int, code: str, message: str):
        super().__init__(f"{status} {code}: {message}")
        self.status = status
        self.code = code
        self.message = message


class ThrottledError(DataverseError):
    """Raised when 429 responses keep coming after max_retries attempts."""


class RecordNotFoundError(DataverseError):
    """404, e.g. upsert with If-Match: * on a row that does not exist."""


class PreconditionFailedError(DataverseError):
    """412: If-None-Match: * on an existing row, or an ETag mismatch on If-Match."""


class BatchError(DataverseError):
    """A change set failed and was rolled back. `index` is the 0-based row that failed."""

    def __init__(self, status: int, code: str, message: str, index: int | None):
        super().__init__(status, code, message)
        self.index = index


@dataclass
class TokenStore:
    """Where sync_changes persists the delta link between runs (a file or a table in real life)."""

    delta_link: str | None = None
    saves: list[str] = field(default_factory=list)

    def save(self, link: str) -> None:
        self.delta_link = link
        self.saves.append(link)


def _raise_for(resp: requests.Response) -> None:
    if resp.status_code < 400:
        return
    try:
        err = resp.json().get("error", {})
    except ValueError:
        err = {}
    code, msg = err.get("code", ""), err.get("message", resp.text[:200])
    cls = {404: RecordNotFoundError, 412: PreconditionFailedError, 429: ThrottledError}.get(
        resp.status_code, DataverseError)
    raise cls(resp.status_code, code, msg)


def _format_key_value(value) -> str:
    """TODO: OData key literal: strings in single quotes with embedded ' doubled, numbers bare."""
    raise NotImplementedError


class DataverseClient:
    def __init__(self, api_url: str, token_provider: Callable[[], str] = lambda: "fake-token",
                 max_retries: int = 5, max_retry_after: float = 300.0):
        self.api_url = api_url.rstrip("/")
        self.token_provider = token_provider
        self.max_retries = max_retries
        self.max_retry_after = max_retry_after
        self.session = requests.Session()

    def _headers(self, extra: dict | None = None) -> dict:
        h = {
            "Authorization": f"Bearer {self.token_provider()}",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Accept": "application/json",
        }
        h.update(extra or {})
        return h

    def _url(self, path_or_url: str) -> str:
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            return path_or_url
        return f"{self.api_url}/{path_or_url.lstrip('/')}"

    # ---- 1. retry ------------------------------------------------------
    def request(self, method: str, path_or_url: str, headers: dict | None = None,
                json_body=None, data: bytes | None = None) -> requests.Response:
        """Send one request, honouring 429 Retry-After. Returns the final response (any status
        other than 429). Raises ThrottledError once max_retries retries are used up.

        TODO:
        - send with self.session.request(method, self._url(path_or_url), headers=self._headers(headers),
          json=json_body, data=data, timeout=30)
        - on 429: sleep Retry-After seconds (time.sleep; capped at self.max_retry_after), then retry
        - at most self.max_retries retries, then raise ThrottledError (hint: _raise_for)
        """
        raise NotImplementedError

    # ---- 2. paging -----------------------------------------------------
    def list_all(self, entity_set: str, select: list[str], page_size: int = 5000) -> list[dict]:
        """TODO: GET <entity_set>?$select=a,b with Prefer: odata.maxpagesize=<page_size> and follow
        @odata.nextLink until it is absent. Return every row."""
        raise NotImplementedError

    # ---- 3. upsert -----------------------------------------------------
    def upsert_by_key(self, entity_set: str, key: dict, values: dict, mode: str = "upsert",
                      etag: str | None = None) -> str:
        """PATCH <entity_set>(<altkey>=<value>) and return "created" or "updated".

        TODO:
        - mode "upsert" (create or update), "create_only", "update_only"; anything else -> ValueError
        - etag (e.g. 'W/"1234"') means optimistic concurrency on update
        - you must be able to tell created from updated (hint: Prefer: return=representation)
        - 404 -> RecordNotFoundError, 412 -> PreconditionFailedError (hint: _raise_for)
        """
        raise NotImplementedError

    # ---- 4. $batch change set ------------------------------------------
    def batch_create(self, entity_set: str, rows: list[dict]) -> list[str]:
        """Create all rows in ONE change set (all or nothing). Returns the new ids in input order.

        TODO: build the multipart/mixed $batch body (CRLF line endings) with one change set and a
        Content-ID per request; POST it; parse with _parse_batch_response; on a failed change set
        raise BatchError with .index = 0-based position of the failing row.
        """
        raise NotImplementedError

    # ---- 5. change tracking --------------------------------------------
    def sync_changes(self, entity_set: str, select: list[str], store: TokenStore,
                     on_upsert: Callable[[dict], None], on_delete: Callable[[str], None],
                     page_size: int = 5000) -> dict:
        """Initial load when store.delta_link is None, else fetch changes since the stored link.
        Calls on_upsert(row) / on_delete(id). Returns {"upserts": n, "deletes": m}.

        TODO: Prefer: odata.track-changes (and maxpagesize); follow nextLinks; detect deleted rows;
        persist the new @odata.deltaLink with store.save(...) at the right moment.
        """
        raise NotImplementedError


def _parse_batch_response(resp: requests.Response) -> list[tuple[str | None, int, dict, str]]:
    """Flatten a multipart/mixed batch response into (content_id, status, headers, body)."""
    ctype = resp.headers.get("Content-Type", "")
    if "boundary=" not in ctype:
        _raise_for(resp)
        raise DataverseError(resp.status_code, "", "batch response is not multipart")
    boundary = ctype.split("boundary=")[1].strip('"; ')
    return _parse_multipart(resp.text, boundary)


def _parse_multipart(text: str, boundary: str):
    out = []
    text = text.replace("\r\n", "\n")
    for chunk in text.split("--" + boundary):
        c = chunk.strip("\n")
        if not c or c.startswith("--"):
            continue
        head, _, rest = c.partition("\n\n")
        headers = {}
        for line in head.split("\n"):
            k, _, v = line.partition(":")
            headers[k.strip().lower()] = v.strip()
        if headers.get("content-type", "").startswith("multipart/mixed"):
            inner = headers["content-type"].split("boundary=")[1].strip('"; ')
            out.extend(_parse_multipart(rest, inner))
            continue
        status_line, _, after = rest.partition("\n")
        status = int(status_line.split(" ")[1])
        rhead, _, body = after.partition("\n\n")
        rh = {}
        for line in rhead.split("\n"):
            k, _, v = line.partition(":")
            if k:
                rh[k.strip().lower()] = v.strip()
        out.append((headers.get("content-id"), status, rh, body.strip()))
    return out
