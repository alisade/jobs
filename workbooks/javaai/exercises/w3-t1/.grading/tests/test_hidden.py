import yaml
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from quizsvc import service
from quizsvc.app import create_app
from quizsvc.gemini import ReplayGemini

ROOT = Path(__file__).resolve().parent.parent
ALL = sorted(service.json.loads((ROOT / "fixtures" / "lessons.json").read_text()))
CATS = {"HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"}


@pytest.fixture()
def http():
    service.time.sleep = lambda s: None
    return TestClient(create_app(ReplayGemini()), raise_server_exceptions=False)


@pytest.mark.parametrize("lesson", ALL)
def test_no_lesson_produces_a_500(http, lesson):
    r = http.post("/quiz/generate", json={"lessonId": lesson})
    assert r.status_code in (200, 422), f"{lesson}: {r.status_code} {r.text[:200]}"


@pytest.mark.parametrize("lesson", ["bio-210-l4", "bio-210-l5", "hist-220-l2", "hist-220-l3", "lit-210-l4", "psych-101-l6"])
def test_ordinary_university_content_generates_again(http, lesson):
    r = http.post("/quiz/generate", json={"lessonId": lesson})
    assert r.status_code == 200, f"{lesson} is ordinary course content for adults and must not be blocked: {r.text[:200]}"
    assert len(r.json()["items"]) == 3


def test_high_risk_answer_is_blocked_gracefully(http):
    r = http.post("/quiz/generate", json={"lessonId": "chem-330-l2"})
    assert r.status_code == 422
    body = r.json()
    assert body.get("status") == "blocked", body
    assert body.get("category") == "HARM_CATEGORY_DANGEROUS_CONTENT", body
    assert "Traceback" not in r.text and "KeyError" not in r.text
    assert body.get("message"), "give the author a human-readable message"


def test_prompt_level_block_is_handled(monkeypatch):
    # a stricter profile makes the prompt itself blocked: no candidates at all
    strict = [{"category": c, "threshold": "BLOCK_LOW_AND_ABOVE"} for c in CATS]
    monkeypatch.setattr(service, "load_safety_settings", lambda *a, **k: strict)
    out = service.generate_quiz(ReplayGemini(), "chem-101-l7")
    assert out["status"] == "blocked"
    assert out.get("source") == "prompt", "say whether the prompt or the answer was blocked"


def test_answer_level_block_reports_source():
    out = service.generate_quiz(ReplayGemini(), "chem-330-l2")
    assert out["status"] == "blocked" and out.get("source") == "response"


def test_profile_is_right_for_adult_learners():
    th = yaml.safe_load((ROOT / "config" / "safety.yaml").read_text())["thresholds"]
    assert set(th) == CATS, "keep a threshold for every category"
    for cat, t in th.items():
        assert t in ("BLOCK_MEDIUM_AND_ABOVE", "BLOCK_ONLY_HIGH"), f"{cat}: {t} (LOW blocks ordinary course content; NONE/OFF removes the filter)"


def test_rate_limit_retry_still_works(http):
    r = http.post("/quiz/generate", json={"lessonId": "stats-101-l1"})
    assert r.status_code == 200


def test_request_still_sends_safety_settings():
    req = service.build_request(service.load_lesson("cs-101-l3"), 3)
    assert {s["category"] for s in req["safetySettings"]} == CATS
