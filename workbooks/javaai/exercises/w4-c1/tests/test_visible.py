from fastapi.testclient import TestClient

from conftest import PUB
from tutor.app import create_app
from tutor.model import FinalText, ScriptedModel, ToolCall


def body(msg="How do pathogens spread?"):
    return {"sessionId": "s-1", "learnerId": "lrn-ada", "courseId": "bio-210", "message": msg}


def test_search_then_answer(bearer):
    model = ScriptedModel(ToolCall("search_course", {"course_id": "bio-210", "query": "how do pathogens spread"}),
                          FinalText("Think about the routes in section l4-s1: which ones involve air?"))
    client = TestClient(create_app(model, PUB), raise_server_exceptions=False)
    r = client.post("/v1/tutor/turn", json=body(), headers=bearer)
    assert r.status_code == 200
    assert r.json()["toolCalls"] == ["search_course"]


def test_health_needs_no_token():
    client = TestClient(create_app(ScriptedModel(FinalText("hi")), PUB))
    assert client.get("/healthz").status_code == 200
