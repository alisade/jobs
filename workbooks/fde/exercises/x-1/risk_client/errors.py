"""The client's error vocabulary. Given; do not change.

Callers (the trust mixin's fail policy) catch ``RiskUnavailable`` and get every way the
risk API can be down: an HTTP 5xx/429, a transport error, the budget running out, the
breaker being open. ``RiskError`` alone (not a ``RiskUnavailable``) means the API is up and
refused this request (a 4xx other than 401): a bug to fix, not an outage to ride out.
No httpx exception ever leaves the client.
"""

from __future__ import annotations


class RiskError(Exception):
    """The risk API answered, and refused the request (4xx other than 401)."""


class RiskUnavailable(RiskError):
    """The risk API is down, slow, unreachable, or answered something unusable."""


class RiskTimeout(RiskUnavailable):
    """The per-call budget ran out (token fetch + assess + any retry, together)."""


class CircuitOpen(RiskUnavailable):
    """The breaker is open: no network call was made."""
