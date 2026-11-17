"""RFC 9457 problem details."""

from __future__ import annotations

from fastapi.responses import JSONResponse

PROBLEM_BASE = "https://keystone.lumenfold.example/problems/"


class Problem(Exception):
    def __init__(self, status: int, slug: str, title: str, detail: str = "") -> None:
        super().__init__(detail or title)
        self.status, self.slug, self.title, self.detail = status, slug, title, detail

    def response(self, instance: str) -> JSONResponse:
        body = {"type": PROBLEM_BASE + self.slug, "title": self.title, "status": self.status,
                "detail": self.detail, "instance": instance}
        return JSONResponse(body, status_code=self.status, media_type="application/problem+json")
