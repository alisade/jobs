import json

from tuneval import data
from tuneval.evaluate import parse_item
from tuneval.tuning import to_example


def test_example_has_user_and_model_turns():
    ex = to_example(data.authored()[0])
    assert [c["role"] for c in ex["contents"]] == ["user", "model"]
    assert json.loads(ex["contents"][1]["parts"][0]["text"])["answerIndex"] == 0


def test_parse_item_accepts_a_good_item():
    good = {"stem": "s", "options": ["a", "b", "c", "d"], "answerIndex": 2, "explanation": "e", "sectionId": "l1-s1"}
    assert parse_item(json.dumps(good)) == good
