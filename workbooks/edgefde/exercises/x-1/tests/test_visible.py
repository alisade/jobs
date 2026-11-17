def test_happy_path(env):
    clock, server, t, c = env
    wo = c.raise_work_order("pump-04", "2026-11-04T14:05:00Z", "Outer race BPFO", "P2")
    assert wo.status == "draft" and wo.asset_id == "pump-04"
    assert len(server.orders) == 1


def test_lost_response_does_not_duplicate(env):
    clock, server, t, c = env
    t.script([None, "commit-timeout"])  # token ok; the POST is processed but the response is lost
    c.raise_work_order("pump-04", "2026-11-04T14:05:00Z", "Outer race BPFO", "P2")
    assert len(server.orders) == 1
