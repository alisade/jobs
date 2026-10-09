"""A small, local fake of the Dataverse Web API (v9.2) for one table: contoso_assets.

Provided infrastructure: you do not need to edit this file. It models the behaviours the
sync client must handle, following the shapes documented on learn.microsoft.com:

- Paging: `Prefer: odata.maxpagesize=N` -> `@odata.nextLink` carrying an opaque `$skiptoken`.
  The skiptoken is a URL-encoded paging cookie (XML), so a client that decodes or rebuilds the
  link breaks it. The fake rejects a modified token with 400. The Prefer header must be sent
  again on every page (otherwise the default page size of 5000 applies).
- Service protection limits: `throttle(n, retry_after)` makes the next n requests return
  429 Too Many Requests with a `Retry-After` header (seconds) and error code 0x80072322.
- Create: POST /contoso_assets -> 204 + OData-EntityId (or 201 + body with
  `Prefer: return=representation`). `contoso_name` is required (400 0x80044331 otherwise).
- Upsert by alternate key: PATCH /contoso_assets(contoso_assetcode='A-1').
  `If-Match: *` prevents create (404), `If-None-Match: *` prevents update (412),
  `If-Match: W/"<n>"` is optimistic concurrency (412 on mismatch).
  `Prefer: return=representation` -> 201 on create, 200 on update.
- $batch: multipart/mixed with change sets. A change set is atomic: the first failing
  operation rolls back the change set and the batch returns 400 with that error, unless
  `Prefer: odata.continue-on-error` is set (only changes behaviour between top-level items).
  Content-ID values are required inside change sets; `$<id>` references in
  `@odata.bind` values resolve to the URI created earlier in the same change set.
- Change tracking: `Prefer: odata.track-changes` on a collection GET returns
  `@odata.deltaLink` (with `$deltatoken`) on the LAST page only. GET on the delta link returns
  new/updated rows followed by deleted rows shaped as
  {"@odata.context": ".../$metadata#contoso_assets/$deletedEntity", "id": "...", "reason": "deleted"}.
  $filter/$orderby/$expand/$top are rejected when tracking changes.
"""

from __future__ import annotations

import copy
import json
import re
import threading
import urllib.parse
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

API = "/api/data/v9.2"
ENTITY_SET = "contoso_assets"
PK = "contoso_assetid"
ALT_KEY = "contoso_assetcode"
DEFAULT_PAGE = 5000


class ODataError(Exception):
    def __init__(self, status: int, code: str, message: str, headers: dict | None = None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.headers = headers or {}


class FakeDataverse:
    """In-memory table + change log. Thread-safe via one lock."""

    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.rows: dict[str, dict] = {}
        self.version = 1000
        self.changes: list[tuple[int, str, str]] = []  # (version, op, id) op in upsert/delete
        self.requests: list[dict] = []  # every request: method, target (raw path+query), headers
        self._throttle_left = 0
        self._throttle_retry_after = 0
        self.base_url = ""
        self.fail_on_names: set[str] = set()  # contoso_name values that make create fail (validation)

    # ---- test controls -------------------------------------------------
    def throttle(self, count: int, retry_after: int = 2) -> None:
        with self.lock:
            self._throttle_left = count
            self._throttle_retry_after = retry_after

    def seed(self, n: int, prefix: str = "A-") -> list[str]:
        ids = []
        for i in range(1, n + 1):
            ids.append(self.create({ALT_KEY: f"{prefix}{i:04d}", "contoso_name": f"Pump {i}",
                                    "contoso_site": "Redmond" if i % 2 else "Dublin"}))
        return ids

    def delete_row(self, row_id: str) -> None:
        with self.lock:
            if row_id not in self.rows:
                raise ODataError(404, "0x80040217", f"contoso_asset With Id = {row_id} Does Not Exist")
            del self.rows[row_id]
            self.version += 1
            self.changes.append((self.version, "delete", row_id))

    def update_row(self, row_id: str, values: dict) -> None:
        with self.lock:
            self.rows[row_id].update(values)
            self._touch(row_id)

    def count(self) -> int:
        return len(self.rows)

    def by_code(self, code: str) -> dict | None:
        for r in self.rows.values():
            if r.get(ALT_KEY) == code:
                return r
        return None

    # ---- data ops ------------------------------------------------------
    def _touch(self, row_id: str) -> None:
        self.version += 1
        self.rows[row_id]["versionnumber"] = self.version
        self.changes.append((self.version, "upsert", row_id))

    def create(self, body: dict, row_id: str | None = None) -> str:
        with self.lock:
            name = body.get("contoso_name")
            if not name:
                raise ODataError(400, "0x80044331",
                                 "A validation error occurred. The value for 'contoso_name' is required.")
            if name in self.fail_on_names:
                raise ODataError(400, "0x80044331",
                                 f"A validation error occurred. contoso_name '{name}' is not allowed.")
            code = body.get(ALT_KEY)
            if code and self.by_code(code):
                raise ODataError(412, "0x80060892", "A record with matching key values already exists.")
            row_id = row_id or str(uuid.uuid4())
            row = {PK: row_id}
            row.update({k: v for k, v in body.items() if "@" not in k})
            for k, v in body.items():
                if k.endswith("@odata.bind"):
                    row["_" + k.split("@")[0] + "_value"] = v
            self.rows[row_id] = row
            self._touch(row_id)
            return row_id

    def entity_uri(self, row_id: str) -> str:
        return f"{self.base_url}{API}/{ENTITY_SET}({row_id})"

    def public(self, row: dict, select: list[str] | None) -> dict:
        out = {"@odata.etag": f'W/"{row["versionnumber"]}"'}
        keys = select or [k for k in row if k != "versionnumber"]
        for k in keys:
            out[k] = row.get(k)
        out[PK] = row[PK]
        return out


def _parse_key(segment: str) -> tuple[str, str]:
    """contoso_assets(<guid>) or contoso_assets(contoso_assetcode='A-1') -> (kind, value)."""
    m = re.fullmatch(r"\(([0-9a-fA-F-]{36})\)", segment)
    if m:
        return "id", m.group(1)
    m = re.fullmatch(r"\(" + ALT_KEY + r"='((?:[^']|'')*)'\)", segment)
    if m:
        return "alt", m.group(1).replace("''", "'")
    raise ODataError(400, "0x80060888", f"Bad key segment: {segment}")


class _Handler(BaseHTTPRequestHandler):
    server_version = "FakeDataverse/9.2"
    protocol_version = "HTTP/1.1"
    fake: FakeDataverse  # set on subclass

    def log_message(self, *args) -> None:  # keep pytest output clean
        pass

    # ---- plumbing -------------------------------------------------------
    def _body(self) -> bytes:
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    def _send(self, status: int, body: bytes = b"", headers: dict | None = None,
              ctype: str = "application/json; odata.metadata=minimal") -> None:
        self.send_response(status)
        self.send_header("OData-Version", "4.0")
        if body:
            self.send_header("Content-Type", ctype)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _error(self, e: ODataError) -> None:
        body = json.dumps({"error": {"code": e.code, "message": e.message}}).encode()
        self._send(e.status, body, e.headers)

    def _dispatch(self, method: str) -> None:
        fake = self.fake
        body = self._body()
        with fake.lock:
            fake.requests.append({"method": method, "target": self.path,
                                  "headers": {k.lower(): v for k, v in self.headers.items()}})
            if fake._throttle_left > 0:
                fake._throttle_left -= 1
                ra = fake._throttle_retry_after
                self._error(ODataError(429, "0x80072322",
                                       "Number of requests exceeded the limit of 6000 over time window of 300 seconds.",
                                       {"Retry-After": str(ra)}))
                return
        try:
            status, payload, headers, ctype = self.fake_route(method, self.path, dict(self.headers), body,
                                                              top_level=True)
            self._send(status, payload, headers, ctype)
        except ODataError as e:
            self._error(e)

    do_GET = lambda self: self._dispatch("GET")  # noqa: E731
    do_POST = lambda self: self._dispatch("POST")  # noqa: E731
    do_PATCH = lambda self: self._dispatch("PATCH")  # noqa: E731
    do_DELETE = lambda self: self._dispatch("DELETE")  # noqa: E731

    # ---- routing ---------------------------------------------------------
    def fake_route(self, method: str, target: str, headers: dict, body: bytes, top_level: bool):
        fake = self.fake
        h = {k.lower(): v for k, v in headers.items()}
        if target.startswith(fake.base_url):
            target = target[len(fake.base_url):]
        path, _, query = target.partition("?")
        if not path.startswith(API + "/"):
            raise ODataError(404, "0x8006088a", f"Resource not found for the segment '{path}'.")
        rest = path[len(API) + 1:]
        if rest == "$batch" and method == "POST" and top_level:
            return self._batch(h, body)
        if not rest.startswith(ENTITY_SET):
            raise ODataError(404, "0x8006088a", f"Resource not found for the segment '{rest}'.")
        key_part = rest[len(ENTITY_SET):]
        if key_part == "":
            if method == "GET":
                return self._collection(query, h)
            if method == "POST":
                return self._create(h, body)
        else:
            kind, value = _parse_key(urllib.parse.unquote(key_part))
            if method == "PATCH":
                return self._patch(kind, value, h, body)
            if method == "GET":
                row = self._find(kind, value)
                return 200, json.dumps(fake.public(row, None)).encode(), {}, "application/json; odata.metadata=minimal"
            if method == "DELETE":
                row = self._find(kind, value)
                fake.delete_row(row[PK])
                return 204, b"", {}, ""
        raise ODataError(405, "0x80060888", f"Method {method} not supported on {rest}")

    def _find(self, kind: str, value: str) -> dict:
        fake = self.fake
        row = fake.rows.get(value) if kind == "id" else fake.by_code(value)
        if row is None:
            raise ODataError(404, "0x80040217", f"contoso_asset With Id = {value} Does Not Exist")
        return row

    # ---- collection GET / paging / change tracking ----------------------
    def _collection(self, query: str, h: dict):
        fake = self.fake
        q = urllib.parse.parse_qs(query, keep_blank_values=True)
        prefer = h.get("prefer", "")
        track = "odata.track-changes" in prefer
        m = re.search(r"odata\.maxpagesize=(\d+)", prefer)
        page_size = int(m.group(1)) if m else DEFAULT_PAGE
        select = q.get("$select", [""])[0]
        select_cols = [c for c in select.split(",") if c] or None
        if (track or "$deltatoken" in q) and any(k in q for k in ("$filter", "$orderby", "$expand", "$top")):
            bad = next(k for k in ("$filter", "$orderby", "$expand", "$top") if k in q)
            raise ODataError(400, "0x80060888",
                             f"The \"{bad}\" query parameter isn't supported when Change Tracking is enabled.")
        with fake.lock:
            if "$deltatoken" in q:
                token = q["$deltatoken"][0]
                since = int(token.split("!")[0])
                items = self._delta_items(since, select_cols)
                snapshot = fake.version
            elif "$skiptoken" in q:
                items = None
            else:
                rows = sorted(fake.rows.values(), key=lambda r: r[ALT_KEY])
                items = [fake.public(r, select_cols) for r in rows]
                snapshot = fake.version
            # paging state is kept server-side, keyed by the paging cookie
            if items is None:
                cookie = q["$skiptoken"][0]
                state = _PAGING.get(cookie)
                if state is None:
                    raise ODataError(400, "0x80040203",
                                     "Invalid paging cookie: the $skiptoken was modified or has expired.")
                items, snapshot, track, select, delta_ctx = state
                is_delta = delta_ctx
            else:
                is_delta = "$deltatoken" in q
            page, remaining = items[:page_size], items[page_size:]
            ctx = f"{fake.base_url}{API}/$metadata#{ENTITY_SET}" + (f"({select})" if select else "")
            if is_delta:
                ctx += "/$delta"
            out = {"@odata.context": ctx, "value": page}
            headers = {}
            if remaining:
                cookie_xml = (f'<cookie pagenumber="{len(_PAGING) + 2}" pagingcookie="'
                              f'&lt;cookie page=&quot;1&quot;&gt;&lt;contoso_assetcode last=&quot;'
                              f'{page[-1].get(ALT_KEY, "") if page else ""}&quot; /&gt;&lt;/cookie&gt;" '
                              f'istracking="{str(track).lower()}" seq="{uuid.uuid4().hex[:8]}" />')
                _PAGING[cookie_xml] = (remaining, snapshot, track, select, is_delta)
                qs = (f"$select={select}&" if select else "") + "$skiptoken=" + urllib.parse.quote(cookie_xml, safe="")
                out["@odata.nextLink"] = f"{fake.base_url}{API}/{ENTITY_SET}?{qs}"
            elif track or is_delta:
                token = f"{snapshot}!10/09/2026 08:10:44"
                qs = (f"$select={select}&" if select else "") + "$deltatoken=" + urllib.parse.quote(token, safe="")
                out["@odata.deltaLink"] = f"{fake.base_url}{API}/{ENTITY_SET}?{qs}"
            if track and "$skiptoken" not in q:
                headers["Preference-Applied"] = "odata.track-changes"
            return 200, json.dumps(out).encode(), headers, "application/json; odata.metadata=minimal"

    def _delta_items(self, since: int, select_cols):
        fake = self.fake
        upserted, deleted = [], []
        # last operation per id after `since` wins
        last: dict[str, str] = {}
        for version, op, rid in fake.changes:
            if version > since:
                last[rid] = op
        for rid, op in last.items():
            if op == "delete" or rid not in fake.rows:
                deleted.append({"@odata.context": f"{fake.base_url}{API}/$metadata#{ENTITY_SET}/$deletedEntity",
                                "id": rid, "reason": "deleted"})
            else:
                upserted.append(fake.public(fake.rows[rid], select_cols))
        upserted.sort(key=lambda r: r.get("@odata.etag"))
        return upserted + deleted

    # ---- writes ----------------------------------------------------------
    def _create(self, h: dict, body: bytes):
        fake = self.fake
        data = json.loads(body or b"{}")
        rid = fake.create(data)
        headers = {"OData-EntityId": fake.entity_uri(rid), "Location": fake.entity_uri(rid)}
        if "return=representation" in h.get("prefer", ""):
            return 201, json.dumps(fake.public(fake.rows[rid], None)).encode(), headers, \
                "application/json; odata.metadata=minimal"
        return 204, b"", headers, ""

    def _patch(self, kind: str, value: str, h: dict, body: bytes):
        fake = self.fake
        data = json.loads(body or b"{}")
        with fake.lock:
            row = fake.rows.get(value) if kind == "id" else fake.by_code(value)
            if_match = h.get("if-match")
            if_none = h.get("if-none-match")
            rep = "return=representation" in h.get("prefer", "")
            if row is None:
                if if_match:
                    raise ODataError(404, "0x80040217", f"contoso_asset With Id = {value} Does Not Exist")
                if kind == "alt":
                    data = dict(data)
                    data.setdefault(ALT_KEY, value)
                    rid = fake.create(data)
                else:
                    rid = fake.create(data, row_id=value)
                status = 201 if rep else 204
            else:
                if if_none == "*":
                    raise ODataError(412, "0x80060892", "A record with matching key values already exists.")
                if if_match and if_match != "*" and if_match != f'W/"{row["versionnumber"]}"':
                    raise ODataError(412, "0x80060882",
                                     "The version of the existing record doesn't match the RowVersion property provided.")
                if not data.get("contoso_name", "x"):
                    raise ODataError(400, "0x80044331", "A validation error occurred. The value for 'contoso_name' is required.")
                upd = {k: v for k, v in data.items() if k != ALT_KEY and "@" not in k}
                row.update(upd)
                fake._touch(row[PK])
                rid = row[PK]
                status = 200 if rep else 204
            uri = (f"{fake.base_url}{API}/{ENTITY_SET}({ALT_KEY}='{value}')" if kind == "alt"
                   else fake.entity_uri(rid))
            headers = {"OData-EntityId": uri}
            if rep:
                return status, json.dumps(fake.public(fake.rows[rid], None)).encode(), headers, \
                    "application/json; odata.metadata=minimal"
            return status, b"", headers, ""

    # ---- $batch ----------------------------------------------------------
    def _batch(self, h: dict, body: bytes):
        fake = self.fake
        ctype = h.get("content-type", "")
        m = re.search(r'boundary="?([^";]+)"?', ctype)
        if not ctype.startswith("multipart/mixed") or not m:
            raise ODataError(400, "0x80060888", "The batch request must have a multipart/mixed Content-Type with a boundary.")
        continue_on_error = "odata.continue-on-error" in h.get("prefer", "")
        text = body.decode("utf-8")
        resp_boundary = "batchresponse_" + str(uuid.uuid4())
        out_parts: list[str] = []
        overall = 200
        for part in _split_multipart(text, m.group(1)):
            phead, pbody = _split_head(part)
            pct = phead.get("content-type", "")
            if pct.startswith("multipart/mixed"):
                cm = re.search(r'boundary="?([^";]+)"?', pct)
                ok, rendered = self._changeset(pbody, cm.group(1) if cm else "")
            else:
                ok, rendered = self._single(pbody, None, {})
            out_parts.append(rendered)
            if not ok and not continue_on_error:
                overall = 400
                break
        payload = "".join(f"--{resp_boundary}\r\n{p}" for p in out_parts) + f"--{resp_boundary}--\r\n"
        return overall, payload.encode(), {}, f"multipart/mixed; boundary={resp_boundary}"

    def _changeset(self, text: str, boundary: str):
        fake = self.fake
        with fake.lock:
            saved = (copy.deepcopy(fake.rows), fake.version, list(fake.changes))
            refs: dict[str, str] = {}
            cs_boundary = "changesetresponse_" + str(uuid.uuid4())
            rendered = []
            for part in _split_multipart(text, boundary):
                phead, pbody = _split_head(part)
                cid = phead.get("content-id")
                if cid is None:
                    fake.rows, fake.version, fake.changes = saved
                    return False, _render_error(400, "0x80060888",
                                                "Content-ID header is required for requests inside a change set.")
                ok, resp = self._single(pbody, cid, refs)
                if not ok:
                    fake.rows, fake.version, fake.changes = saved
                    return False, resp
                rendered.append(resp)
            inner = "".join(f"--{cs_boundary}\r\n{r}" for r in rendered) + f"--{cs_boundary}--\r\n"
            return True, f"Content-Type: multipart/mixed; boundary={cs_boundary}\r\n\r\n{inner}"

    def _single(self, http_text: str, content_id, refs: dict):
        fake = self.fake
        lines = http_text.split("\r\n")
        request_line = lines[0]
        try:
            method, url, _ = request_line.split(" ", 2)
        except ValueError:
            return False, _render_error(400, "0x80060888", f"Malformed request line: {request_line!r}")
        headers, i = {}, 1
        while i < len(lines) and lines[i] != "":
            k, _, v = lines[i].partition(":")
            headers[k.strip()] = v.strip()
            i += 1
        body = "\r\n".join(lines[i + 1:]).strip()
        if method == "GET" and content_id is not None:
            return False, _render_error(400, "0x80060888", "GET requests aren't allowed within change sets.")
        if url.startswith("$"):
            ref = url.split("/")[0]
            if ref[1:] not in refs:
                return False, _render_error(400, "0x80060888", f"Content-ID Reference: '{ref}' does not exist in the batch context.")
            url = refs[ref[1:]] + url[len(ref):]
        if body:
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                return False, _render_error(400, "0x80060888", "Request body is not valid JSON.")
            for k, v in list(data.items()):
                if k.endswith("@odata.bind") and isinstance(v, str) and v.startswith("$"):
                    if v[1:] not in refs:
                        return False, _render_error(400, "0x80060888",
                                                    f"Content-ID Reference: '{v}' does not exist in the batch context.")
                    data[k] = refs[v[1:]]
            body = json.dumps(data)
        try:
            status, payload, rh, ctype = self.fake_route(method, url, headers, body.encode(), top_level=False)
        except ODataError as e:
            return False, _render_error(e.status, e.code, e.message, content_id)
        if content_id is not None and "OData-EntityId" in rh:
            refs[content_id] = rh["OData-EntityId"]
        head = "Content-Type: application/http\r\nContent-Transfer-Encoding: binary\r\n"
        if content_id is not None:
            head += f"Content-ID: {content_id}\r\n"
        reason = {200: "OK", 201: "Created", 204: "No Content"}.get(status, "OK")
        resp = f"HTTP/1.1 {status} {reason}\r\nOData-Version: 4.0\r\n"
        for k, v in rh.items():
            resp += f"{k}: {v}\r\n"
        if payload:
            resp += f"Content-Type: {ctype}\r\n\r\n{payload.decode()}\r\n"
        else:
            resp += "\r\n"
        return True, f"{head}\r\n{resp}\r\n"


_PAGING: dict[str, tuple] = {}


def _render_error(status: int, code: str, message: str, content_id=None) -> str:
    reason = {400: "Bad Request", 404: "Not Found", 412: "Precondition Failed"}.get(status, "Error")
    head = "Content-Type: application/http\r\nContent-Transfer-Encoding: binary\r\n"
    if content_id is not None:
        head += f"Content-ID: {content_id}\r\n"
    body = json.dumps({"error": {"code": code, "message": message}})
    return (f"{head}\r\nHTTP/1.1 {status} {reason}\r\nContent-Type: application/json; odata.metadata=minimal\r\n"
            f"OData-Version: 4.0\r\n\r\n{body}\r\n")


def _split_multipart(text: str, boundary: str) -> list[str]:
    text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    parts = []
    for chunk in text.split("--" + boundary):
        c = chunk.strip("\r\n")
        if not c or c == "--" or c.startswith("--"):
            continue
        parts.append(c)
    return parts


def _split_head(part: str) -> tuple[dict, str]:
    head, _, body = part.partition("\r\n\r\n")
    headers = {}
    for line in head.split("\r\n"):
        if ":" in line:
            k, _, v = line.partition(":")
            headers[k.strip().lower()] = v.strip()
    return headers, body


class FakeServer:
    """Start/stop the fake on 127.0.0.1:<random port> in a background thread."""

    def __init__(self) -> None:
        self.fake = FakeDataverse()
        handler = type("Handler", (_Handler,), {"fake": self.fake})
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.fake.base_url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        self.thread = threading.Thread(target=self.httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)

    @property
    def base_url(self) -> str:
        return self.fake.base_url

    @property
    def api_url(self) -> str:
        return self.fake.base_url + API

    def __enter__(self) -> "FakeServer":
        self.thread.start()
        return self

    def __exit__(self, *exc) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        _PAGING.clear()
