import threading

import service.app as app
from util import Factory, texts


def fresh():
    if hasattr(app, "_SPECIALIST"):
        app._SPECIALIST = None


def test_history_size_stays_flat_across_sessions():
    fresh()
    f = Factory(turns_per_session=1)
    svc = app.HelpdeskService(f)
    sizes = []
    for i in range(6):
        sid = f"s{i}"
        svc.handle(sid, f"user{i}", "payments", "pending?")
        sizes.append(len(f.model(sid).seen[-1]))
    assert len(set(sizes)) == 1, f"messages sent to the model grow per session: {sizes}"


def test_each_session_gets_its_own_model_and_team_tools():
    fresh()
    f = Factory(turns_per_session=1)
    svc = app.HelpdeskService(f)
    svc.handle("p", "lwong", "payments", "pending?")
    svc.handle("c", "mchen", "claims", "pending?")
    assert "AR-903" in texts(f.model("c")) and "AR-901" not in texts(f.model("c"))
    assert "AR-901" in texts(f.model("p"))


def test_new_service_instance_starts_clean():
    fresh()
    f1 = Factory(turns_per_session=1)
    app.HelpdeskService(f1).handle("x", "lwong", "payments", "pending?")
    f2 = Factory(turns_per_session=1)
    app.HelpdeskService(f2).handle("y", "mchen", "claims", "pending?")
    assert "lwong" not in texts(f2.model("y"))


def test_lru_bound():
    fresh()
    f = Factory(turns_per_session=1)
    svc = app.HelpdeskService(f, max_sessions=3)
    for i in range(5):
        svc.handle(f"s{i}", "u", "payments", "pending?")
    assert svc.active_sessions() == 3


def test_idle_sessions_expire():
    fresh()
    now = [1000.0]
    f = Factory(turns_per_session=2)
    svc = app.HelpdeskService(f, idle_seconds=60, clock=lambda: now[0])
    svc.handle("a", "lwong", "payments", "first")
    now[0] += 120
    svc.handle("b", "mchen", "claims", "hello")
    assert svc.active_sessions() == 1
    svc.handle("a", "lwong", "payments", "again")
    assert "first" not in texts(f.model("a")), "an expired session must start a new conversation"


def test_concurrent_sessions_isolated():
    fresh()
    f = Factory(turns_per_session=1)
    svc = app.HelpdeskService(f)
    errs = []

    def run(i):
        try:
            svc.handle(f"t{i}", f"user{i}", "payments", f"question from user{i}")
        except Exception as e:  # noqa: BLE001
            errs.append(repr(e))

    th = [threading.Thread(target=run, args=(i,)) for i in range(8)]
    [t.start() for t in th]
    [t.join(timeout=20) for t in th]
    assert not errs, errs[:2]
    for i in range(8):
        seen = texts(f.model(f"t{i}"))
        others = [j for j in range(8) if j != i and f"user{j}" in seen]
        assert not others, f"session t{i} saw users {others}"


def test_answer_has_root_cause():
    from pathlib import Path
    t = Path("ANSWER.md").read_text().lower()
    assert "singleton" in t or "module-level" in t or "global" in t or "shared agent" in t
