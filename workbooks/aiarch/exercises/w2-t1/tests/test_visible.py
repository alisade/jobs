import service.app as app
from util import Factory, texts


def fresh():
    if hasattr(app, "_SPECIALIST"):
        app._SPECIALIST = None


def test_two_managers_do_not_share_history():
    fresh()
    f = Factory()
    svc = app.HelpdeskService(f)
    svc.handle("sess-a", "lwong", "payments", "what is pending?")
    svc.handle("sess-b", "mchen", "claims", "what is pending?")
    seen_b = texts(f.model("sess-b"))
    assert "lwong" not in seen_b and "ledger-admin" not in seen_b, "session B saw session A's conversation"


def test_same_session_keeps_its_own_history():
    fresh()
    f = Factory()
    svc = app.HelpdeskService(f)
    svc.handle("sess-a", "lwong", "payments", "what is pending?")
    svc.handle("sess-a", "lwong", "payments", "and the second one?")
    assert "what is pending?" in texts(f.model("sess-a"))
