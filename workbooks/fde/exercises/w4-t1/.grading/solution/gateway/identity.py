"""Who the current request acts for.

Fixed: the principal lives in a ContextVar. Each request runs in its own task with its
own copy of the context, so a bind in one request is invisible to every other request
in flight, and release() restores the previous value when the request ends.
(PR #388 had moved it into a module-level dict, which every concurrent request shared.)
"""

from __future__ import annotations

from contextvars import ContextVar, Token


class Unauthenticated(Exception):
    pass


_principal: ContextVar[str | None] = ContextVar("gateway_principal", default=None)


def bind(principal: str) -> Token[str | None]:
    """Bind ``principal`` for the request being served; returns a handle for release()."""
    return _principal.set(principal)


def release(handle: Token[str | None]) -> None:
    """End of request: restore whatever was bound before (normally nothing)."""
    _principal.reset(handle)


def current_principal() -> str:
    principal = _principal.get()
    if principal is None:
        raise Unauthenticated("no principal bound to this request")
    return principal
