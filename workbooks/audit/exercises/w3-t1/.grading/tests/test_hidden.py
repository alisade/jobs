"""Hidden tests for audit/w3-t1."""

from conftest import counts, night


def test_two_nights_cover_the_whole_sample_once(tmp_path):
    night(tmp_path)
    night(tmp_path)
    c = counts(tmp_path)
    assert len(c["tested"]) == 10 and set(c["tested"].values()) == {1}


def test_one_work_item_per_exception(tmp_path):
    night(tmp_path)
    night(tmp_path)
    assert counts(tmp_path)["work_items"] == {"CHG-105103": 1, "CHG-105107": 1, "CHG-105109": 1}


def test_third_night_tests_nothing(tmp_path):
    for _ in range(3):
        out = night(tmp_path)
    assert "Nothing left" in out
    assert sum(counts(tmp_path)["tested"].values()) == 10


def test_first_night_tests_one_batch(tmp_path):
    night(tmp_path)
    assert sorted(counts(tmp_path)["tested"]) == [f"CHG-10{n}" for n in range(5101, 5106)]


def test_progress_key_is_persisted_scope():
    from nightly import tools
    assert not tools.COMPLETED_KEY.startswith("temp:")
