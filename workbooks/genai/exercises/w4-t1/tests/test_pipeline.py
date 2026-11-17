from conftest import replay


def test_plain_price_answer_is_shown():
    out = replay("How much is the lantern?")
    assert out["blocked"] is False
    assert "$34.50" in out["answer"]


def test_expired_promotion_is_blocked():
    out = replay("Can I use FALL20 on the Ridgeline 2P?")
    assert out["blocked"] is True
