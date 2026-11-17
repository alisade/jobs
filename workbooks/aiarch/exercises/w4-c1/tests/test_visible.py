from obo import api
from obo.fakeidp import ISSUER
from util import make


def test_tool_reaches_api_as_the_user():
    idp, client, _ = make()
    user = idp.user_token("lwong", "openid access.request.write")
    down = client.get_downstream_token(user, "access-requests")
    seen = api.verify(down, idp.jwks(), ISSUER)
    assert seen["acting_for"] == "lwong" and seen["actor"] == "lighthouse-agent"


def test_user_token_replayed_at_api_fails_on_audience():
    import jwt
    import pytest
    idp, _, _ = make()
    user = idp.user_token("lwong", "access.request.write")
    with pytest.raises(jwt.InvalidAudienceError):
        api.verify(user, idp.jwks(), ISSUER)
