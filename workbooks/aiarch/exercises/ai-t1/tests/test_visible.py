from lighthouse.bedrock_stub import FakeConverse
from util import Clock, conversation


def test_second_turn_reads_the_cache():
    clock = Clock()
    client = FakeConverse(clock)
    u = conversation(client, clock, "lwong", n_turns=2)
    assert u[0]["cacheWriteInputTokens"] > 0
    assert u[1]["cacheReadInputTokens"] > 0, "turn 2 should read the cached prefix"


def test_other_users_share_the_prefix():
    clock = Clock()
    client = FakeConverse(clock)
    conversation(client, clock, "lwong", n_turns=1)
    u = conversation(client, clock, "mchen", n_turns=1, start_id=50)
    assert u[0]["cacheReadInputTokens"] > 0
