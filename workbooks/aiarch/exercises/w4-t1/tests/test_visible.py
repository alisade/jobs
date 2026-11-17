import json
from pathlib import Path

import pytest

from authz.engine import authorize

ROOT = Path(__file__).resolve().parent.parent
CASES = [json.loads(l) for l in (ROOT / "tests/requests_visible.jsonl").read_text().splitlines() if l.strip()]


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_decision(case):
    r = authorize(case["claims"], case["tool"], case["input"])
    assert r.decision == case["expect"], f"{case['name']}: got {r.decision} reasons={r.reasons} errors={r.errors}"
