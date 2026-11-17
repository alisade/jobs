import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from obo.exchange import (ACCESS_TOKEN, EXCHANGE, JWT_TYPE, InsufficientScope, TokenError, build_exchange_request,
                          validate_inbound)
from obo.fakeidp import ISSUER
from util import make


def test_exchange_request_shape():
    f = build_exchange_request("subj", audience="https://a", resource="https://a/api", scopes=["b", "a"], actor_token="act")
    assert f["grant_type"] == EXCHANGE and f["subject_token"] == "subj" and f["subject_token_type"] == ACCESS_TOKEN
    assert f["requested_token_type"] == ACCESS_TOKEN and f["audience"] == "https://a" and f["resource"] == "https://a/api"
    assert set(f["scope"].split()) == {"a", "b"} and f["actor_token"] == "act" and f["actor_token_type"] == JWT_TYPE


def test_no_actor_fields_without_actor():
    f = build_exchange_request("subj", audience="https://a", resource=None, scopes=["a"])
    assert "actor_token" not in f and "actor_token_type" not in f and "resource" not in f


def test_scope_narrowed_to_user_and_target():
    idp, client, _ = make()
    client.get_downstream_token(idp.user_token("lwong", "openid profile access.request.read hr.read"), "access-requests")
    assert idp.requests[-1]["scope"] == "access.request.read"


def test_no_matching_scope_raises_without_calling_idp():
    idp, client, _ = make()
    with pytest.raises(InsufficientScope):
        client.get_downstream_token(idp.user_token("lwong", "openid hr.read"), "access-requests")
    assert idp.requests == []


@pytest.mark.parametrize("fault,needle", [("wrong_aud", "aud"), ("wrong_sub", "lwong"), ("extra_scope", "admin")])
def test_misbehaving_idp_is_caught(fault, needle):
    idp, client, _ = make(faults=[fault])
    with pytest.raises(TokenError) as e:
        client.get_downstream_token(idp.user_token("lwong", "access.request.write"), "access-requests")
    assert needle in str(e.value).lower()


def test_actor_required_when_configured():
    from obo.exchange import OboClient
    from util import TARGETS, Clock
    from obo.fakeidp import FakeIdP
    clock = Clock()
    idp = FakeIdP(clock=clock)
    client = OboClient(idp.token_endpoint, idp.jwks(), ISSUER, TARGETS, clock=clock, actor_token=None,
                       agent_client_id="lighthouse-agent")
    with pytest.raises(TokenError):
        client.get_downstream_token(idp.user_token("lwong", "access.request.write"), "access-requests")


def test_cache_hit_and_expiry():
    idp, client, clock = make()
    user = idp.user_token("lwong", "access.request.write", ttl=3600)
    a = client.get_downstream_token(user, "access-requests")
    b = client.get_downstream_token(user, "access-requests")
    assert a == b and len(idp.requests) == 1
    clock.t += 250  # exchanged tokens live 300 s; refresh inside the 60 s skew
    c = client.get_downstream_token(user, "access-requests")
    assert c != a and len(idp.requests) == 2


def test_cache_is_per_user():
    idp, client, _ = make()
    a = client.get_downstream_token(idp.user_token("lwong", "access.request.write"), "access-requests")
    b = client.get_downstream_token(idp.user_token("mchen", "access.request.write"), "access-requests")
    assert jwt.decode(a, options={"verify_signature": False})["sub"] == "lwong"
    assert jwt.decode(b, options={"verify_signature": False})["sub"] == "mchen"


def test_inbound_wrong_audience_rejected():
    idp, client, _ = make()
    with pytest.raises(TokenError):
        client.get_downstream_token(idp.user_token("lwong", "access.request.write", aud="some-other-app"), "access-requests")


def test_inbound_expired_rejected():
    idp, client, clock = make()
    user = idp.user_token("lwong", "access.request.write", ttl=30)
    clock.t += 200
    with pytest.raises(TokenError):
        client.get_downstream_token(user, "access-requests")


def test_inbound_hs256_rejected():
    idp, client, _ = make()
    forged = jwt.encode({"iss": ISSUER, "sub": "admin", "aud": "lighthouse-gateway", "exp": 9999999999,
                         "scope": "access.request.write"}, "secret", algorithm="HS256", headers={"kid": "k1"})
    with pytest.raises(TokenError):
        client.get_downstream_token(forged, "access-requests")


def test_inbound_signed_by_other_key_rejected():
    idp, client, _ = make()
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    from cryptography.hazmat.primitives import serialization
    pem = other.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    tok = idp.sign({"iss": ISSUER, "sub": "lwong", "aud": "lighthouse-gateway", "exp": 9999999999,
                    "scope": "access.request.write"}, key=pem)
    with pytest.raises(TokenError):
        client.get_downstream_token(tok, "access-requests")


def test_unknown_kid_rejected():
    idp, client, _ = make()
    tok = idp.sign({"iss": ISSUER, "sub": "lwong", "aud": "lighthouse-gateway", "exp": 9999999999,
                    "scope": "access.request.write"}, kid="rotated-away")
    with pytest.raises(TokenError):
        validate_inbound(tok, idp.jwks(), issuer=ISSUER, audience="lighthouse-gateway")


def test_idp_error_surfaces():
    idp, client, _ = make()
    idp.token_endpoint = lambda form: {"error": "invalid_grant", "error_description": "delegation not allowed"}
    client.token_endpoint = idp.token_endpoint
    with pytest.raises(TokenError) as e:
        client.get_downstream_token(idp.user_token("lwong", "access.request.write"), "access-requests")
    assert "invalid_grant" in str(e.value)


def test_unknown_target():
    idp, client, _ = make()
    with pytest.raises(TokenError):
        client.get_downstream_token(idp.user_token("lwong", "access.request.write"), "payroll")
