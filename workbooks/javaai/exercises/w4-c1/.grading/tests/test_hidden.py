import pytest
from fastapi.testclient import TestClient

from conftest import OTHER_PRIV, PUB, id_token
from tutor import tools
from tutor.agent import TutorAgent
from tutor.app import create_app
from tutor.model import FinalText, ScriptedModel, ToolCall


def body(msg="How do pathogens spread?", learner="lrn-ada", course="bio-210"):
    return {"sessionId": "s-1", "learnerId": learner, "courseId": course, "message": msg}


def call(model, headers, payload=None):
    client = TestClient(create_app(model, PUB), raise_server_exceptions=False)
    return client.post("/v1/tutor/turn", json=payload or body(), headers=headers)


def ok_model():
    return ScriptedModel(FinalText("Which routes need direct contact?"))


# ------------------------------------------------------------ auth

def test_missing_token_is_401():
    assert call(ok_model(), {}).status_code == 401


@pytest.mark.parametrize("token", [
    "Basic Zm9vOmJhcg==",
    "Bearer not-a-jwt",
    "Bearer " + id_token(key=OTHER_PRIV),
    "Bearer " + id_token(exp_in=-60),
    "Bearer " + id_token(aud="https://some-other-service.a.run.app"),
    "Bearer " + id_token(iss="https://evil.example"),
], ids=["basic", "garbage", "bad-signature", "expired", "wrong-audience", "wrong-issuer"])
def test_bad_tokens_are_401(token):
    r = call(ok_model(), {"Authorization": token})
    assert r.status_code == 401, r.text


def test_hs256_token_is_rejected():
    # alg confusion: an HMAC token "signed" with the public key text must not pass
    import jwt, time
    t = jwt.encode({"iss": "https://accounts.google.com", "aud": "https://tutor-agent-7f3k2q-uc.a.run.app",
                    "email": "catalog-api@kestrel-prod.iam.gserviceaccount.com", "email_verified": True,
                    "exp": int(time.time()) + 600}, "x" * 64, algorithm="HS256")
    assert call(ok_model(), {"Authorization": "Bearer " + t}).status_code == 401


def test_valid_token_from_other_service_is_403():
    r = call(ok_model(), {"Authorization": "Bearer " + id_token(email="quiz-gen@kestrel-prod.iam.gserviceaccount.com")})
    assert r.status_code == 403


def test_unverified_email_is_rejected():
    r = call(ok_model(), {"Authorization": "Bearer " + id_token(verified=False)})
    assert r.status_code in (401, 403)


def test_model_not_called_when_unauthenticated():
    m = ok_model()
    call(m, {})
    assert m.calls == []


# ------------------------------------------------------------ request validation

def test_oversized_and_empty_messages_are_422(bearer):
    assert call(ok_model(), bearer, body(msg="")).status_code == 422
    assert call(ok_model(), bearer, body(msg="virus " * 500)).status_code == 422


# ------------------------------------------------------------ tool scoping

def test_only_read_tools_are_offered(bearer):
    m = ok_model()
    call(m, bearer)
    assert sorted(m.calls[0][1]) == ["get_learner_progress", "search_course"]


def test_write_tool_is_never_executed(bearer):
    tools.WRITES.clear()
    m = ScriptedModel(ToolCall("record_mastery", {"learner_id": "lrn-ada", "lesson_id": "l5"}), FinalText("Done, what next?"))
    r = call(m, bearer)
    assert r.status_code == 200
    assert tools.WRITES == [], "record_mastery executed: the tutor must not have a write path"
    tool_msgs = [h for h in m.calls[1][0] if h.get("role") == "tool"]
    assert tool_msgs and "error" in str(tool_msgs[-1]).lower(), "feed an error back so the model can recover"


def test_unknown_tool_and_bad_args_are_fed_back(bearer):
    m = ScriptedModel(ToolCall("delete_course", {}), ToolCall("search_course", {"nope": 1}), FinalText("Let us look at section l4-s1."))
    r = call(m, bearer)
    assert r.status_code == 200, r.text
    assert len(m.calls) == 3


def test_progress_is_scoped_to_the_session_learner(bearer):
    m = ScriptedModel(ToolCall("get_learner_progress", {"learner_id": "lrn-bo", "course_id": "bio-210"}), FinalText("You are on vaccines."))
    call(m, bearer, body(msg="What should I study about vaccines next?"))
    result = [h for h in m.calls[1][0] if h.get("role") == "tool"][-1]["result"]
    assert result.get("learner_id") == "lrn-ada", "the model asked for another learner; the session learner wins"


def test_search_is_scoped_to_the_session_course(bearer):
    m = ScriptedModel(ToolCall("search_course", {"course_id": "stats-101", "query": "median"}), FinalText("ok"))
    call(m, bearer, body(msg="Is the virus median incubation relevant?"))
    result = [h for h in m.calls[1][0] if h.get("role") == "tool"][-1]["result"]
    assert all(s["section_id"].startswith("l4") or s["section_id"].startswith("l5") or s["section_id"].startswith("l6") for s in result), result


def test_tool_loop_is_bounded(bearer):
    m = ScriptedModel(ToolCall("search_course", {"course_id": "bio-210", "query": "virus"}))
    r = call(m, bearer)
    assert r.status_code == 200
    assert len(r.json()["toolCalls"]) <= 4
    assert len(m.calls) <= 5
    assert r.json()["reply"], "answer with a fallback message instead of looping or failing"


# ------------------------------------------------------------ guards

def test_off_topic_is_refused_before_the_model(bearer):
    m = ok_model()
    r = call(m, bearer, body(msg="Write my cover letter for a sales job"))
    assert r.status_code == 200
    assert r.json()["refused"] is True
    assert m.calls == [], "the before-model guard must not spend a model call"


def test_reply_that_gives_away_the_quiz_answer_is_withheld(bearer):
    m = ScriptedModel(FinalText("The answer to your quiz is Memory Cells, they remember the antigen."))
    r = call(m, bearer, body(msg="What does the vaccine quiz want?"))
    j = r.json()
    assert j["withheld"] is True
    assert "memory cells" not in j["reply"].lower()


def test_normal_hint_is_not_withheld(bearer):
    m = ScriptedModel(FinalText("Think about what the immune system keeps after a vaccine."))
    j = call(m, bearer, body(msg="What does the vaccine quiz want?")).json()
    assert j["withheld"] is False and j["refused"] is False
