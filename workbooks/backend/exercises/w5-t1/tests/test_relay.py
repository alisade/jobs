import pytest

from outbox.consumer import Consumer
from outbox.relay import Relay, SimulatedCrash
from testkit import effects, statuses


def test_happy_path_every_event_applied_once(env):
    env["add"](150)
    relay = Relay(env["db"], env["broker"], "relay-a", env["clock"], batch_size=100)
    while relay.run_once():
        pass
    c = Consumer(env["consumer_db"], env["broker"])
    c.poll()
    assert effects(env["consumer_db"]) == 150
    assert statuses(env["db"]) == {"sent": 150}


def test_relay_killed_mid_batch_then_restarted(env):
    """The 2026-11-10 rollout: relay-a killed during a batch, a new pod takes over after the lease."""
    env["add"](100)
    a = Relay(env["db"], env["broker"], "relay-a", env["clock"], batch_size=100, lease_seconds=30)
    with pytest.raises(SimulatedCrash):
        a.run_once(crash_after=40)
    env["clock"].t += 31
    b = Relay(env["db"], env["broker"], "relay-b", env["clock"], batch_size=100)
    while b.run_once():
        pass
    c = Consumer(env["consumer_db"], env["broker"])
    c.poll()
    assert effects(env["consumer_db"]) == 100, "each stage change must be applied exactly once downstream"
