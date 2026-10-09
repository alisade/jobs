"""Who the current request acts for.

PR #388 (2026-09-30): "Moved the principal off request.state into this module so tool
code deep in the stack (audit, executor factory) can read identity without threading the
request through every call." Middleware binds the principal when a request arrives and
releases it when the request ends; anything in between calls ``current_principal()``.
"""

from __future__ import annotations


class Unauthenticated(Exception):
    pass


# The principal of the request being served.
_current: dict[str, str | None] = {"principal": None}


def bind(principal: str) -> object:
    """Bind ``principal`` for the request being served; returns a handle for release()."""
    _current["principal"] = principal
    return principal


def release(handle: object) -> None:
    """End of request. Kept for symmetry; the next bind() overwrites the slot anyway."""
    return None


def current_principal() -> str:
    principal = _current["principal"]
    if principal is None:
        raise Unauthenticated("no principal bound to this request")
    return principal
