"""Woodgrove asset sync: a minimal Dataverse Web API client (reference solution)."""

from __future__ import annotations

import json
import random
import time
import uuid
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
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


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
        other than 429). Raises ThrottledError once max_retries retries are used up."""
        url = self._url(path_or_url)
        attempt = 0
        while True:
            resp = self.session.request(method, url, headers=self._headers(headers),
                                        json=json_body, data=data, timeout=30)
            if resp.status_code != 429:
                return resp
            if attempt >= self.max_retries:
                _raise_for(resp)
            attempt += 1
            ra = resp.headers.get("Retry-After")
            try:
                wait = float(ra) if ra is not None else 2.0 ** attempt
            except ValueError:
                wait = 2.0 ** attempt
            wait = min(max(wait, 0.0), self.max_retry_after)
            time.sleep(wait + random.uniform(0, 0.1))

    # ---- 2. paging -----------------------------------------------------
    def _pages(self, first: str, prefer: str) -> Iterator[dict]:
        url = first
        while url:
            resp = self.request("GET", url, headers={"Prefer": prefer})
            _raise_for(resp)
            body = resp.json()
            yield body
            url = body.get("@odata.nextLink")

    def list_all(self, entity_set: str, select: list[str], page_size: int = 5000) -> list[dict]:
        rows: list[dict] = []
        first = f"{entity_set}?$select={','.join(select)}"
        for body in self._pages(first, f"odata.maxpagesize={page_size}"):
            rows.extend(body.get("value", []))
        return rows

    # ---- 3. upsert -----------------------------------------------------
    def upsert_by_key(self, entity_set: str, key: dict, values: dict, mode: str = "upsert",
                      etag: str | None = None) -> str:
        """Returns "created" or "updated"."""
        if mode not in ("upsert", "create_only", "update_only"):
            raise ValueError(f"unknown mode {mode}")
        key_str = ",".join(f"{k}={_format_key_value(v)}" for k, v in key.items())
        headers = {"Prefer": "return=representation", "Content-Type": "application/json"}
        if etag is not None:
            headers["If-Match"] = etag
        elif mode == "update_only":
            headers["If-Match"] = "*"
        elif mode == "create_only":
            headers["If-None-Match"] = "*"
        body = {k: v for k, v in values.items() if k not in key}
        resp = self.request("PATCH", f"{entity_set}({key_str})?$select={next(iter(key))}",
                            headers=headers, json_body=body)
        _raise_for(resp)
        return "created" if resp.status_code == 201 else "updated"

    # ---- 4. $batch change set ------------------------------------------
    def batch_create(self, entity_set: str, rows: list[dict]) -> list[str]:
        """Create all rows in ONE change set (all or nothing). Returns the new ids in input order."""
        if not rows:
            return []
        if len(rows) > 1000:
            raise ValueError("a batch can contain at most 1000 requests")
        batch = f"batch_{uuid.uuid4()}"
        changeset = f"changeset_{uuid.uuid4()}"
        parts = [f"--{batch}", f"Content-Type: multipart/mixed; boundary={changeset}", ""]
        for i, row in enumerate(rows, start=1):
            parts += [
                f"--{changeset}",
                "Content-Type: application/http",
                "Content-Transfer-Encoding: binary",
                f"Content-ID: {i}",
                "",
                f"POST {self.api_url}/{entity_set} HTTP/1.1",
                "Content-Type: application/json; type=entry",
                "",
                json.dumps(row),
            ]
        parts += [f"--{changeset}--", "", f"--{batch}--", ""]
        payload = "\r\n".join(parts).encode("utf-8")
        resp = self.request("POST", "$batch", data=payload,
                            headers={"Content-Type": f"multipart/mixed; boundary={batch}"})
        results = _parse_batch_response(resp)
        ids: dict[int, str] = {}
        for content_id, status, headers, body in results:
            if status >= 400:
                err = (json.loads(body).get("error", {}) if body.strip().startswith("{") else {})
                idx = int(content_id) - 1 if content_id else None
                raise BatchError(status, err.get("code", ""), err.get("message", body[:200]), idx)
            entity_id = headers.get("odata-entityid", "")
            ids[int(content_id)] = entity_id[entity_id.rfind("(") + 1:entity_id.rfind(")")]
        if resp.status_code >= 400:
            raise BatchError(resp.status_code, "", "batch failed", None)
        return [ids[i] for i in range(1, len(rows) + 1)]

    # ---- 5. change tracking --------------------------------------------
    def sync_changes(self, entity_set: str, select: list[str], store: TokenStore,
                     on_upsert: Callable[[dict], None], on_delete: Callable[[str], None],
                     page_size: int = 5000) -> dict:
        """Initial load when store has no delta link, else delta since the stored link.
        Persists the new delta link only after every page has been applied."""
        prefer = f"odata.track-changes,odata.maxpagesize={page_size}"
        first = store.delta_link or f"{entity_set}?$select={','.join(select)}"
        stats = {"upserts": 0, "deletes": 0}
        new_link = None
        for body in self._pages(first, prefer):
            for item in body.get("value", []):
                if str(item.get("@odata.context", "")).endswith("/$deletedEntity"):
                    on_delete(item["id"])
                    stats["deletes"] += 1
                else:
                    on_upsert(item)
                    stats["upserts"] += 1
            new_link = body.get("@odata.deltaLink") or new_link
        if not new_link:
            raise DataverseError(500, "", "no @odata.deltaLink on the last page; is change tracking enabled?")
        store.save(new_link)
        return stats


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
