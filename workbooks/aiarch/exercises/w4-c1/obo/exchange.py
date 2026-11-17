"""On-behalf-of token exchange (RFC 8693) for Lighthouse tools.

The agent receives the user's access token (audience lighthouse-gateway). A tool that calls the
access-requests API must present a token for THAT API, carrying the user as subject and the
agent as actor, with no more scope than the user has and the tool needs.

TODO: implement validate_inbound, build_exchange_request and OboClient.get_downstream_token
(see README for the full contract). The current version forwards the user's token unchanged,
which the access-requests API rightly rejects.
"""
from __future__ import annotations

import time
from typing import Callable

import jwt  # noqa: F401  (PyJWT: jwt.decode, jwt.get_unverified_header, jwt.PyJWK)

EXCHANGE = "urn:ietf:params:oauth:grant-type:token-exchange"
ACCESS_TOKEN = "urn:ietf:params:oauth:token-type:access_token"
JWT_TYPE = "urn:ietf:params:oauth:token-type:jwt"
ALLOWED_ALGS = ["RS256"]
LEEWAY = 60


class TokenError(Exception):
    """Inbound or exchanged token rejected."""


class InsufficientScope(TokenError):
    pass


def validate_inbound(token: str, jwks: dict, *, issuer: str, audience: str, now: float | None = None) -> dict:
    raise NotImplementedError("TODO")


def build_exchange_request(subject_token: str, *, audience: str, resource: str | None, scopes: list[str],
                           actor_token: str | None = None) -> dict:
    raise NotImplementedError("TODO")


class OboClient:
    def __init__(self, token_endpoint: Callable[[dict], dict], jwks: dict, issuer: str, targets: dict,
                 inbound_audience: str = "lighthouse-gateway", actor_token: Callable[[], str] | None = None,
                 agent_client_id: str | None = None, clock: Callable[[], float] = time.time):
        self.token_endpoint = token_endpoint
        self.jwks = jwks
        self.issuer = issuer
        self.targets = targets
        self.inbound_audience = inbound_audience
        self.actor_token = actor_token
        self.agent_client_id = agent_client_id
        self.clock = clock

    def get_downstream_token(self, inbound_token: str, target: str) -> str:
        return inbound_token  # TODO: token passthrough is the bug; exchange it instead
