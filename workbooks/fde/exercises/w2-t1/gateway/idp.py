"""A stand-in for the Northwind IdP (login.northwind.example), run locally by make setup.

- GET  /.well-known/jwks.json   the published signing keys
- POST /oauth/token             client-credentials style: returns a fresh access token
- POST /admin/rotate            starts the monthly key rollover: publishes the next key
                                and moves token signing to it in stages
- GET  /admin/state             which keys are published and which kid signs

Keys persist in run/idp-keys.json so a restart keeps them. The IdP's clock runs ~2 s
ahead of the gateway host (it stamps iat a little in the future), as it does in prod.
"""

from __future__ import annotations

import itertools
import json
import os
import time
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

RUN_DIR = Path(os.environ.get("IDP_RUN_DIR", Path(__file__).resolve().parents[1] / "run"))
ISSUER = os.environ.get("IDP_ISSUER", "http://127.0.0.1:18210/")
AUDIENCE = "https://mcp.northwind.example/mcp"
OLD_KID, NEW_KID = "k-2026-09", "k-2026-10"
CLOCK_AHEAD_S = 2


def _load_keys() -> dict[str, rsa.RSAPrivateKey]:
    path = RUN_DIR / "idp-keys.json"
    if path.exists():
        pems = json.loads(path.read_text())
        return {k: serialization.load_pem_private_key(v.encode(), None) for k, v in pems.items()}
    keys = {kid: rsa.generate_private_key(public_exponent=65537, key_size=2048)
            for kid in (OLD_KID, NEW_KID)}
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        kid: key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                               serialization.NoEncryption()).decode()
        for kid, key in keys.items()
    }))
    return keys


KEYS = _load_keys()
STATE_FILE = RUN_DIR / "idp-state.json"
_counter = itertools.count()
_signing = itertools.count()


def _state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"published": [OLD_KID], "rollover": False}


def _public_jwk(kid: str) -> dict:
    jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(KEYS[kid].public_key()))
    jwk.update({"kid": kid, "use": "sig", "alg": "RS256"})
    return jwk


async def jwks(_: Request) -> JSONResponse:
    return JSONResponse({"keys": [_public_jwk(k) for k in _state()["published"]]},
                        headers={"cache-control": "public, max-age=300"})


async def token(request: Request) -> JSONResponse:
    form = await request.form()
    client = str(form.get("client_id", "managed-agents"))
    sub = str(form.get("sub", f"cust-{1000 + next(_counter) % 50}"))
    state = _state()
    # Staged rollover: half of the new tokens move to the next key.
    kid = NEW_KID if state["rollover"] and next(_signing) % 2 == 0 else OLD_KID
    now = int(time.time()) + CLOCK_AHEAD_S
    claims = {"iss": ISSUER, "aud": AUDIENCE, "sub": sub, "client_id": client,
              "scope": "cart:read cart:write", "iat": now, "nbf": now - 5, "exp": now + 900}
    access = jwt.encode(claims, KEYS[kid], algorithm="RS256", headers={"kid": kid})
    return JSONResponse({"access_token": access, "token_type": "Bearer", "expires_in": 900})


async def rotate(_: Request) -> JSONResponse:
    state = {"published": [OLD_KID, NEW_KID], "rollover": True}
    STATE_FILE.write_text(json.dumps(state))
    return JSONResponse(state)


async def admin_state(_: Request) -> JSONResponse:
    return JSONResponse(_state())


app = Starlette(routes=[
    Route("/.well-known/jwks.json", jwks),
    Route("/oauth/token", token, methods=["POST"]),
    Route("/admin/rotate", rotate, methods=["POST"]),
    Route("/admin/state", admin_state),
])
