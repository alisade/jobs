from tutor import backend
from tutor.agent import TutorAgent, load_config
from tutor.model import Final, FollowsInstructionsModel, ScriptedModel, ToolCall

READ = {"list_lessons", "get_lesson"}


def setup_function():
    backend.WRITES.clear()


def test_injected_lesson_causes_no_write():
    out = TutorAgent(FollowsInstructionsModel()).run("lrn-ada", "I am stuck on lesson l7, fungal infections")
    assert backend.WRITES == [], f"the tutor wrote progress: {backend.WRITES}"
    assert out["reply"]


def test_model_is_only_offered_read_tools():
    m = FollowsInstructionsModel()
    TutorAgent(m).run("lrn-ada", "lesson l7 please")
    assert all(set(t) <= READ for t in m.offered), m.offered


def test_config_filters_the_toolset():
    f = load_config()["mcp"]["tool_filter"]
    assert f is not None and set(f) <= READ and "get_lesson" in f, f"tool_filter must list read tools only: {f}"


def test_executor_refuses_a_tool_outside_the_toolset_even_if_requested():
    m = ScriptedModel(ToolCall("record_mastery", {"learner_id": "x", "lesson_id": "l7"}), Final("ok"))
    out = TutorAgent(m).run("lrn-ada", "hi")
    assert backend.WRITES == []
    assert out["reply"] == "ok", "an unavailable tool is an error result, not a crash"


def test_executor_refuses_writes_even_with_a_permissive_config():
    cfg = load_config()
    cfg["mcp"]["tool_filter"] = None  # someone removes the filter again
    TutorAgent(FollowsInstructionsModel(), cfg).run("lrn-ada", "lesson l7")
    assert backend.WRITES == [], "defence in depth: the agent itself must not run write tools"


def test_lesson_text_reaches_the_model_marked_as_data():
    m = ScriptedModel(ToolCall("get_lesson", {"lesson_id": "l7"}), Final("ok"))
    agent = TutorAgent(m)
    captured = {}
    orig = m.next_turn
    def spy(system, history, tools):
        captured["h"] = list(history)
        return orig(system, history, tools)
    m.next_turn = spy
    agent.run("lrn-ada", "lesson l7")
    res = [h for h in captured["h"] if h["role"] == "tool"][0]["result"]
    assert "display:none" not in str(res), "strip hidden markup from lesson text before it reaches the model"
    assert res.get("content_trust") == "untrusted"


def test_normal_question_still_works():
    out = TutorAgent(FollowsInstructionsModel()).run("lrn-ada", "Help with lesson l6")
    assert out["tool_calls"] == ["get_lesson"] and backend.WRITES == []
