from fastapi.testclient import TestClient

from quizsvc import service
from quizsvc.app import create_app
from quizsvc.gemini import ReplayGemini


def test_plain_lesson_generates():
    client = TestClient(create_app(ReplayGemini()), raise_server_exceptions=False)
    r = client.post("/quiz/generate", json={"lessonId": "cs-101-l3"})
    assert r.status_code == 200
    assert len(r.json()["items"]) == 3


def test_request_carries_safety_settings():
    req = service.build_request(service.load_lesson("cs-101-l3"), 3)
    cats = {s["category"] for s in req["safetySettings"]}
    assert "HARM_CATEGORY_DANGEROUS_CONTENT" in cats
