"""The verified caller context. Built by the API layer from the validated Cognito JWT, never from
the request body or anything the model says."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CallerContext:
    tenant_id: str      # e.g. "acme-foods"; from the token's tenant_id claim
    user_id: str        # the token's sub
    request_id: str     # for log correlation
