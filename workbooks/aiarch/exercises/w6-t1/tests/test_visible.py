import json
from pathlib import Path

import pytest

from scpsim import evaluate, load_org

ROOT = Path(__file__).resolve().parent.parent
REQS = json.loads((ROOT / "tests" / "requests_visible.json").read_text())


@pytest.fixture(scope="module")
def org():
    return load_org(ROOT / "org/layout.json", ROOT / "policies/attachments.json", ROOT / "policies")


@pytest.mark.parametrize("req", REQS, ids=[r["name"] for r in REQS])
def test_request(org, req):
    d = evaluate(org, req)
    got = "ALLOW" if d.allowed else "DENY"
    assert got == req["expect"], f"{req['name']}: expected {req['expect']}, got {got} ({d.reason} {d.denied_by})"
