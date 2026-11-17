"""In-process stand-in for MFH's GitHub Enterprise REST API (no network). Do not edit.

Behaves like the real list-pulls endpoint: newest first by updated_at, page-based pagination with a
`Link` header (rel="next" / rel="last"), and a per_page that is silently capped at the server's
maximum (MFH's appliance is configured with max_per_page=50).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

DATA = Path(__file__).resolve().parents[1] / "data"
BASE = "https://ghe.meridianfreight.example/api/v3"


class HTTPError(Exception):
    pass


@dataclass
class Response:
    status: int
    body: list | dict
    headers: dict = field(default_factory=dict)
    url: str = ""

    def json(self):
        return self.body

    def raise_for_status(self) -> None:
        if self.status >= 400:
            raise HTTPError(f"{self.status} for {self.url}")


class FakeGitHub:
    def __init__(self, max_per_page: int = 50, pulls: list | None = None, broken_next: bool = False):
        self.max_per_page = max_per_page
        self.broken_next = broken_next
        self.pulls = pulls if pulls is not None else json.loads((DATA / "tms-core-pulls.json").read_text())
        self.calls: list[str] = []

    def get(self, url: str, params: dict | None = None) -> Response:
        if url.startswith("/"):
            url = BASE + url
        u = urlparse(url)
        q = {k: v[-1] for k, v in parse_qs(u.query).items()}
        q.update({k: str(v) for k, v in (params or {}).items()})
        full = f"{BASE}{u.path[len(urlparse(BASE).path):]}?{urlencode(q)}"
        self.calls.append(full)
        if len(self.calls) > 500:
            return Response(429, {"message": "secondary rate limit"}, url=full)
        if not u.path.endswith("/pulls"):
            return Response(404, {"message": "Not Found"}, url=full)
        state = q.get("state", "open")
        per_page = max(1, min(int(q.get("per_page", 30)), self.max_per_page))
        page = max(1, int(q.get("page", 1)))
        items = [p for p in self.pulls if state == "all" or p["state"] == state]
        items.sort(key=lambda p: p["updated_at"], reverse=True)
        last = max(1, -(-len(items) // per_page))
        chunk = items[(page - 1) * per_page: page * per_page]
        links = []
        if page < last:
            nq = dict(q, per_page=str(per_page), page=str(page if self.broken_next else page + 1))
            links.append(f'<{BASE}{u.path[len(urlparse(BASE).path):]}?{urlencode(nq)}>; rel="next"')
        lq = dict(q, per_page=str(per_page), page=str(last))
        links.append(f'<{BASE}{u.path[len(urlparse(BASE).path):]}?{urlencode(lq)}>; rel="last"')
        return Response(200, chunk, {"Link": ", ".join(links), "X-RateLimit-Remaining": "4870"}, url=full)
