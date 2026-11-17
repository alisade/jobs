import pathlib
import re

import pytest

from outbox.consumer import Consumer
from outbox.db import connect
from outbox.relay import Relay, SimulatedCrash
from testkit import effects, statuses


def drain(relay):
    for _ in range(1000):
        if not relay.run_once():
            return


def test_message_ids_are_the_outbox_event_ids(env):
    ids = env["add"](50)
    drain(Relay(env["db"], env["broker"], "relay-a", env["clock"]))
    assert sorted(m.headers["event_id"] for m in env["broker"].all_messages()) == sorted(ids)


@pytest.mark.parametrize("crash_after", [1, 37, 99])
def test_crash_then_restart_applies_exactly_once(env, crash_after):
    env["add"](230)
    a = Relay(env["db"], env["broker"], "relay-a", env["clock"], batch_size=100, lease_seconds=30)
    a.run_once()
    with pytest.raises(SimulatedCrash):
        a.run_once(crash_after=crash_after)
    env["clock"].t += 60
    drain(Relay(env["db"], env["broker"], "relay-b", env["clock"], batch_size=100))
    Consumer(env["consumer_db"], env["broker"]).poll()
    assert effects(env["consumer_db"]) == 230
    assert statuses(env["db"]) == {"sent": 230}


def test_crash_republishes_at_most_the_in_flight_row(env):
    env["add"](100)
    a = Relay(env["db"], env["broker"], "relay-a", env["clock"], batch_size=100, lease_seconds=30)
    with pytest.raises(SimulatedCrash):
        a.run_once(crash_after=60)
    env["clock"].t += 31
    drain(Relay(env["db"], env["broker"], "relay-b", env["clock"], batch_size=100))
    published = len(env["broker"].all_messages())
    assert published <= 101, f"{published - 100} rows were published twice"


def test_relay_that_lost_its_lease_stops_publishing(env):
    """Broker latency spike: relay-a's batch outlives its lease and relay-b takes over."""
    env["add"](80)
    a = Relay(env["db"], env["broker"], "relay-a", env["clock"], batch_size=80, lease_seconds=30)
    b = Relay(env["db"], env["broker"], "relay-b", env["clock"], batch_size=80, lease_seconds=30)
    rows_a = a.claim()
    assert b.claim() == [], "a live claim must not be taken by the other replica"
    env["clock"].t += 31
    drain(b)
    a.publish_claimed(rows_a)
    ids = [m.headers["event_id"] for m in env["broker"].all_messages()]
    assert len(ids) == 80 and len(set(ids)) == 80


def test_per_aggregate_order_is_preserved(env):
    env["add"](120)
    drain(Relay(env["db"], env["broker"], "relay-a", env["clock"], batch_size=25))
    last = {}
    for m in env["broker"].all_messages():
        opp, v = m.value["opportunity_id"], m.value["version"]
        assert v == last.get(opp, 0) + 1
        last[opp] = v


def test_consumer_dedupes_a_redelivered_message(env):
    env["add"](10)
    drain(Relay(env["db"], env["broker"], "relay-a", env["clock"]))
    c = Consumer(env["consumer_db"], env["broker"])
    c.poll()
    env["broker"].committed.clear()  # consumer restarted without its committed offsets
    c.poll()
    assert effects(env["consumer_db"]) == 10


def test_answer_names_the_id_regeneration():
    text = pathlib.Path("ANSWER.md").read_text().lower()
    assert re.search(r"uuid4|new (event )?id|fresh (event )?id|regenerat|event_id .*(publish|relay)", text)
