from tutor import backend
from tutor.agent import TutorAgent
from tutor.model import FollowsInstructionsModel


def test_ordinary_lesson_question_is_answered():
    backend.WRITES.clear()
    out = TutorAgent(FollowsInstructionsModel()).run("lrn-ada", "Can you help me with lesson l6 on antibiotics?")
    assert out["reply"]
    assert out["tool_calls"] == ["get_lesson"]
