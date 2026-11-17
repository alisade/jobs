from fakes import World, execute


def test_happy_path_rolls_back():
    w = World(live="9")
    r = execute(w)
    assert r["status"] == "Success", r
    assert w.live == "7"


def test_backup_happens_before_the_endpoint_moves():
    w = World(live="9")
    execute(w)
    apis = w.apis()
    assert "PutObject" in apis and apis.index("PutObject") < apis.index("UpdateAgentRuntimeEndpoint")
