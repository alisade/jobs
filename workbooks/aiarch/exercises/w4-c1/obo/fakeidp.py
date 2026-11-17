"""A fake IdP for offline tests (works as shipped): signs user tokens and answers RFC 8693
token-exchange requests. ``faults`` lets tests make it misbehave the way real IdPs sometimes do."""
from __future__ import annotations

import time
import uuid

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

ISSUER = "https://idp.harborpoint.example/oauth2/lighthouse"
EXCHANGE = "urn:ietf:params:oauth:grant-type:token-exchange"
ACCESS_TOKEN = "urn:ietf:params:oauth:token-type:access_token"
JWT_TYPE = "urn:ietf:params:oauth:token-type:jwt"


class FakeIdP:
    def __init__(self, kid: str = "k1", clock=time.time):
        self.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.kid = kid
        self.clock = clock
        self.requests: list[dict] = []
        self.faults: set[str] = set()

    # ---- keys
    def jwks(self) -> dict:
        pub = jwt.algorithms.RSAAlgorithm.to_jwk(self.key.public_key(), as_dict=True)
        pub.update({"kid": self.kid, "use": "sig", "alg": "RS256"})
        return {"keys": [pub]}

    def pem(self) -> bytes:
        return self.key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                      serialization.NoEncryption())

    # ---- tokens
    def sign(self, claims: dict, kid: str | None = None, alg: str = "RS256", key=None) -> str:
        return jwt.encode(claims, key if key is not None else self.pem(), algorithm=alg, headers={"kid": kid or self.kid})

    def user_token(self, sub: str, scope: str, aud: str = "lighthouse-gateway", ttl: int = 900, **extra) -> str:
        now = int(self.clock())
        return self.sign({"iss": ISSUER, "sub": sub, "aud": aud, "scope": scope, "iat": now, "nbf": now,
                          "exp": now + ttl, "jti": str(uuid.uuid4()), "client_id": "lighthouse-portal", **extra})

    # ---- token endpoint (RFC 8693)
    def token_endpoint(self, form: dict) -> dict:
        self.requests.append(dict(form))
        if form.get("grant_type") != EXCHANGE:
            return {"error": "unsupported_grant_type"}
        if form.get("subject_token_type") != ACCESS_TOKEN:
            return {"error": "invalid_request", "error_description": "subject_token_type"}
        try:
            subject = jwt.decode(form["subject_token"], self.key.public_key(), algorithms=["RS256"],
                                 audience="lighthouse-gateway", issuer=ISSUER,
                                 options={"verify_exp": False, "verify_nbf": False, "verify_iat": False})
        except jwt.PyJWTError as e:
            return {"error": "invalid_grant", "error_description": str(e)}
        granted = sorted(set(form.get("scope", "").split()) & set(subject.get("scope", "").split()))
        if "extra_scope" in self.faults:
            granted.append("access.request.admin")
        if not granted:
            return {"error": "invalid_scope"}
        now = int(self.clock())
        claims = {"iss": ISSUER, "sub": subject["sub"], "aud": form.get("audience"), "scope": " ".join(granted),
                  "iat": now, "nbf": now, "exp": now + 300, "jti": str(uuid.uuid4())}
        if form.get("actor_token"):
            actor = jwt.decode(form["actor_token"], self.key.public_key(), algorithms=["RS256"],
                               options={"verify_aud": False, "verify_exp": False, "verify_iat": False}, issuer=ISSUER)
            claims["act"] = {"sub": actor["sub"]}
        if "wrong_aud" in self.faults:
            claims["aud"] = "lighthouse-gateway"
        if "wrong_sub" in self.faults:
            claims["sub"] = "svc-lighthouse-agent"
        return {"access_token": self.sign(claims), "issued_token_type": ACCESS_TOKEN, "token_type": "Bearer",
                "expires_in": 300, "scope": " ".join(granted)}

    def agent_token(self, client_id: str = "lighthouse-agent") -> str:
        now = int(self.clock())
        return self.sign({"iss": ISSUER, "sub": client_id, "aud": ISSUER, "iat": now, "exp": now + 900})
