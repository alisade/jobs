from criteria.stubs import pb2


def req(case_id, criteria):
    return pb2.CheckRequest(case_id=case_id, criteria=list(criteria))


async def test_results_in_request_order(stub):
    crit = ["KHP-MP-0417/2.a", "KHP-MP-0417/2.b", "KHP-MP-0417/2.cx"]
    resp = await stub.CheckCriteria(req("PA-2026-0001", crit), timeout=5)
    assert [r.criterion_id for r in resp.results] == crit
    assert [r.status for r in resp.results] == ["met", "met", "not_met"]


async def test_health_reports_serving(stub):
    resp = await stub.Health(pb2.HealthRequest(), timeout=5)
    assert resp.status == "SERVING"
