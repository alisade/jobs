from fastapi.testclient import TestClient

from tutorsvc.app import create_app
from tutorsvc.gemini import BlockingGemini


def test_one_turn_works():
    client = TestClient(create_app(BlockingGemini(latency_s=0.01)))
    r = client.post("/v1/tutor/turn", json={"learnerId": "lrn-ada", "message": "What is R0?"})
    assert r.status_code == 200
    assert "R0" in r.json()["reply"]
