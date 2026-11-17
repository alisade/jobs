from enrich.llm import ScriptedLLM
from enrich.pipeline import run_batch
from fixtures import COOLER, TENT, ans, cooler_ans


def test_two_good_items_are_published():
    llm = ScriptedLLM({TENT["supplier_sku"]: [ans()], COOLER["supplier_sku"]: [cooler_ans()]})
    report = run_batch([TENT, COOLER], llm)
    assert [p["supplier_sku"] for p in report.published] == ["NWT-4471", "GLC-45R"]
    assert report.review == []
    assert report.published[0]["category"] == "tents"
    assert report.llm_calls == 2


def test_cost_is_reported():
    llm = ScriptedLLM({TENT["supplier_sku"]: [ans()]})
    report = run_batch([TENT], llm)
    assert report.cost_usd > 0
