"""Hidden checks for genai/w6-t1."""

from conftest import world  # noqa: F401

Q = "Is the Glacier 45 cooler in stock?"


def test_stock_answer_is_not_served_to_another_store(world):
    a, _, _, clock, _ = world
    a.ask("u-ana", "012", Q)
    clock.t += 5
    r = a.ask("u-cy", "087", "is the glacier 45 cooler in stock")
    assert r.text == "The Glacier 45qt Cooler is sold out at store 087."


def test_stock_answer_for_the_same_store_is_fresh_within_a_minute(world):
    a, _, inv, clock, _ = world
    a.ask("u-ana", "012", Q)
    inv.stock[("KO-COOL-45", "012")] = 0
    clock.t += 120
    assert a.ask("u-ana", "012", Q).text == "The Glacier 45qt Cooler is sold out at store 012."


def test_stock_answers_never_older_than_60s(world):
    a, _, inv, clock, _ = world
    a.ask("u-ana", "012", Q)
    inv.stock[("KO-COOL-45", "012")] = 2
    clock.t += 61
    assert "2 left" in a.ask("u-ana", "012", Q).text


def test_personal_answers_are_never_cached(world):
    a, agent, _, _, cache = world
    ana = a.ask("u-ana", "012", "Where is my order?")
    ben = a.ask("u-ben", "012", "where is my order")
    assert "K-1001" in ana.text and "K-2001" in ben.text
    assert ben.cache_hit is False
    assert all("K-1001" not in e.text for e in cache.entries.values())


def test_faq_still_cached_for_hours(world):
    a, agent, _, clock, _ = world
    a.ask("u-ana", "012", "What is your return policy?")
    clock.t += 12 * 3600
    assert a.ask("u-x", "045", "WHAT is your return policy??").cache_hit is True
    assert agent.calls == 1


def test_faq_expires_after_a_day(world):
    a, agent, _, clock, _ = world
    a.ask("u-ana", "012", "What is your return policy?")
    clock.t += 24 * 3600 + 1
    assert a.ask("u-ana", "012", "What is your return policy?").cache_hit is False


def test_catalog_answers_cached_but_not_beyond_an_hour(world):
    a, agent, _, clock, _ = world
    a.ask("u-ana", "012", "How much is the Ridgeline tent?")
    clock.t += 600
    assert a.ask("u-ben", "087", "how much is the ridgeline tent").cache_hit is True
    clock.t += 2 * 3600
    assert a.ask("u-ben", "087", "how much is the ridgeline tent").cache_hit is False


def test_hit_rate_on_mixed_holiday_traffic(world):
    a, _, _, clock, cache = world
    faq = ["What is your return policy?", "what is your return policy", "Return policy?"]
    for i in range(30):
        a.ask(f"u-{i}", ["012", "045", "087"][i % 3], faq[i % 3] if "?" in faq[i % 3] else faq[i % 3])
        clock.t += 30
    assert cache.hits >= 25
