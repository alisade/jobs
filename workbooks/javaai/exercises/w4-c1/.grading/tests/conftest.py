import sys
import time
from pathlib import Path

import jwt
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

CALLER = "catalog-api@kestrel-prod.iam.gserviceaccount.com"
AUD = "https://tutor-agent-7f3k2q-uc.a.run.app"


# Test-only keys (never used outside these tests). caller = the catalog API's Google-signed ID token
# stand-in; attacker = a key the tutor does not trust.
KEYS = Path(__file__).resolve().parent.parent / "tests" / "keys"
PRIV = (KEYS / "caller.pem").read_text()
PUB = (KEYS / "caller.pub.pem").read_text()
OTHER_PRIV = (KEYS / "attacker.pem").read_text()


def id_token(email=CALLER, aud=AUD, iss="https://accounts.google.com", exp_in=600, key=None, alg="RS256", verified=True):
    now = int(time.time())
    claims = {"iss": iss, "aud": aud, "sub": "1093", "email": email, "email_verified": verified, "iat": now, "exp": now + exp_in}
    return jwt.encode(claims, key or PRIV, algorithm=alg)


@pytest.fixture()
def bearer():
    return {"Authorization": "Bearer " + id_token()}
