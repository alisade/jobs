def test_faq_is_answered_and_cached(world):
    a, agent, _, _, _ = world
    first = a.ask("u-ana", "012", "What is your return policy?")
    second = a.ask("u-ben", "087", "what is your return policy")
    assert "60 days" in first.text
    assert second.cache_hit is True
    assert agent.calls == 1


def test_stock_answer_on_a_miss_is_correct(world):
    a, _, _, _, _ = world
    r = a.ask("u-ana", "012", "Is the Glacier 45 cooler in stock?")
    assert r.text == "The Glacier 45qt Cooler is in stock (6 left) at store 012."
