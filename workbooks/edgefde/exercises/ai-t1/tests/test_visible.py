import replay
import transcripts


def test_injected_note_cannot_change_threshold():
    r = replay.replay(transcripts.INJECTED)
    assert r["thresholds"]["P04"]["outer_race"] == 12.0


def test_legitimate_question_still_answered():
    r = replay.replay(transcripts.LEGIT)
    assert r["result"]["status"] == "ok" and "P04" in r["result"]["content"]
