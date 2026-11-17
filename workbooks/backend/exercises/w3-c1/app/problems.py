"""RFC 9457 problem details. Every error the service returns goes through `problem()`."""

from __future__ import annotations

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

PROBLEM_JSON = "application/problem+json"
BASE = "https://errors.keystone.lumenfold.example/"


def problem(status: int, title: str, detail: str = "", type_: str = "about:blank", headers: dict | None = None,
            **extra) -> JSONResponse:
    body = {"type": BASE + type_ if type_ != "about:blank" else type_, "title": title, "status": status}
    if detail:
        body["detail"] = detail
    body.update(extra)
    return JSONResponse(body, status_code=status, media_type=PROBLEM_JSON, headers=headers)


class ProblemError(Exception):
    def __init__(self, status: int, title: str, detail: str = "", type_: str = "about:blank", headers: dict | None = None):
        super().__init__(title)
        self.status, self.title, self.detail, self.type_, self.headers = status, title, detail, type_, headers


def install(app) -> None:  # noqa: ANN001
    @app.exception_handler(ProblemError)
    async def _problem(_req: Request, exc: ProblemError):
        return problem(exc.status, exc.title, exc.detail, exc.type_, exc.headers)

    @app.exception_handler(RequestValidationError)
    async def _validation(_req: Request, exc: RequestValidationError):
        errors = [{"loc": list(e.get("loc", [])), "msg": e.get("msg", "")} for e in exc.errors()]
        return problem(422, "Request body is invalid", type_="validation-error", errors=errors)

    @app.exception_handler(Exception)
    async def _unhandled(_req: Request, exc: Exception):
        return problem(500, "Internal error", "the request failed; it is safe to retry with the same Idempotency-Key",
                       type_="internal")
