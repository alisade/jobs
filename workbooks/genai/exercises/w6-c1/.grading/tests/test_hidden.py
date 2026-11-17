"""Hidden checks for genai/w6-c1: validation with retry, grounding checks, review queue,
idempotency and the cost cap."""

import json

from enrich.llm import ScriptedLLM
from enrich.pipeline import run_batch, write_jsonl
from enrich.store import EnrichmentStore
from fixtures import COOLER, JACKET, LANTERN, TENT, ans, cooler_ans, jacket_ans, lantern_ans

LONG_TITLE = "Ridgeline Two Person Freestanding Backpacking Tent With Two Doors And Two Vestibules Sage"


def reasons_for(report, sku):
    for r in report.review:
        if r["supplier_sku"] == sku:
            return r["reasons"]
    return None


def test_invalid_output_is_retried_once_with_the_error_fed_back():
    llm = ScriptedLLM({TENT["supplier_sku"]: [ans(title=LONG_TITLE), ans()]})
    report = run_batch([TENT], llm)
    assert llm.calls == 2
    assert [p["supplier_sku"] for p in report.published] == ["NWT-4471"]
    assert "title" in llm.prompts[1], "the retry prompt must carry the validation error"
    assert "title" not in llm.prompts[0].split("SUPPLIER_TEXT:")[1]


def test_malformed_json_twice_goes_to_review_after_exactly_two_calls():
    llm = ScriptedLLM({TENT["supplier_sku"]: ["Sure! Here is the JSON: {title: tent", "```json\n{\"title\": 1}\n```"]})
    report = run_batch([TENT], llm)
    assert llm.calls == 2
    assert report.published == []
    assert reasons_for(report, "NWT-4471") == ["invalid_output"]


def test_category_outside_taxonomy_and_extra_fields_are_invalid():
    bad_cat = json.dumps({**json.loads(ans()), "category": "camping"})
    extra = json.dumps({**json.loads(ans()), "msrp_usd": 249})
    llm = ScriptedLLM({TENT["supplier_sku"]: [bad_cat, extra]})
    report = run_batch([TENT], llm)
    assert report.published == []
    assert reasons_for(report, "NWT-4471") == ["invalid_output"]


def test_invented_material_and_color_go_to_review():
    llm = ScriptedLLM({TENT["supplier_sku"]: [ans(material="silnylon", color="orange")]})
    report = run_batch([TENT], llm)
    r = reasons_for(report, "NWT-4471")
    assert r is not None and "unsupported:material" in r and "unsupported:color" in r


def test_weights_and_capacity_with_unit_conversion_are_accepted():
    llm = ScriptedLLM({
        COOLER["supplier_sku"]: [cooler_ans()],       # 23.5 lb -> 10.66 kg, 45 qt -> 42.6 L
        JACKET["supplier_sku"]: [jacket_ans()],       # 340 g -> 0.34 kg
        LANTERN["supplier_sku"]: [lantern_ans()],     # 280 g -> 0.28 kg
    })
    report = run_batch([COOLER, JACKET, LANTERN], llm)
    assert [p["supplier_sku"] for p in report.published] == ["GLC-45R", "DPR-RJ2", "BCN-L400"]


def test_numbers_not_in_the_source_are_rejected():
    llm = ScriptedLLM({
        TENT["supplier_sku"]: [ans(weight_kg=2.4)],
        COOLER["supplier_sku"]: [cooler_ans(capacity_l=45.0)],  # 45 qt is 42.6 L, not 45 L
    })
    report = run_batch([TENT, COOLER], llm)
    assert "unsupported:weight_kg" in reasons_for(report, "NWT-4471")
    assert "unsupported:capacity_l" in reasons_for(report, "GLC-45R")


def test_waterproof_only_when_the_supplier_says_so():
    llm = ScriptedLLM({
        TENT["supplier_sku"]: [ans(description="Freestanding waterproof two-person tent.")],
        JACKET["supplier_sku"]: [jacket_ans()],
    })
    report = run_batch([TENT, JACKET], llm)
    assert "unsupported_claim:waterproof" in reasons_for(report, "NWT-4471")
    assert [p["supplier_sku"] for p in report.published] == ["DPR-RJ2"]


def test_banned_claims_always_go_to_review():
    llm = ScriptedLLM({JACKET["supplier_sku"]: [jacket_ans(title="Downpour Eco-Friendly Rain Jacket")]})
    report = run_batch([JACKET], llm)
    assert "banned_claim:eco-friendly" in reasons_for(report, "DPR-RJ2")


def test_low_confidence_goes_to_review():
    llm = ScriptedLLM({LANTERN["supplier_sku"]: [lantern_ans(confidence=0.41)]})
    report = run_batch([LANTERN], llm)
    assert reasons_for(report, "BCN-L400") == ["low_confidence"]


def test_unchanged_items_are_not_sent_to_the_model_again():
    store = EnrichmentStore()
    script = {
        TENT["supplier_sku"]: [ans()],
        LANTERN["supplier_sku"]: [lantern_ans(confidence=0.3)],
    }
    first = run_batch([TENT, LANTERN], ScriptedLLM(script), store=store)
    llm2 = ScriptedLLM(script)
    second = run_batch([TENT, LANTERN], llm2, store=store)
    assert llm2.calls == 0, "unchanged items (published or in review) must not be re-billed"
    assert second.published == first.published
    assert second.review == first.review
    changed = dict(TENT, description=TENT["description"] + " Now with a footprint.")
    llm3 = ScriptedLLM(script)
    run_batch([changed, LANTERN], llm3, store=store)
    assert llm3.calls == 1


def test_cost_cap_stops_the_batch_and_reports_skipped_items():
    items = [dict(TENT, supplier_sku=f"NWT-{i}") for i in range(6)]
    script = {it["supplier_sku"]: [ans()] for it in items}
    llm = ScriptedLLM(script, tokens_per_call=1000)  # 1000 in + 250 out = 0.006750 USD per call
    report = run_batch(items, llm, cost_cap_usd=0.015)
    assert report.budget_exhausted is True
    assert report.llm_calls == 3
    assert report.skipped == ["NWT-3", "NWT-4", "NWT-5"]
    assert len(report.published) == 3
    assert report.cost_usd <= 0.015 + 0.00675 + 1e-9


def test_published_jsonl_in_input_order(tmp_path):
    llm = ScriptedLLM({JACKET["supplier_sku"]: [jacket_ans()], TENT["supplier_sku"]: [ans()]})
    report = run_batch([JACKET, TENT], llm)
    p = tmp_path / "out.jsonl"
    write_jsonl(report, str(p))
    rows = [json.loads(line) for line in p.read_text().splitlines()]
    assert [r["supplier_sku"] for r in rows] == ["DPR-RJ2", "NWT-4471"]
    assert rows[0]["weight_kg"] == 0.34
