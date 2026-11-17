"""Hidden checks for genai/w5-t1: batch lookups, bounded concurrency, deadline, partial results."""

import asyncio
import time

from assistant_tools.catalog_client import BATCH_MAX, FakeCatalog
from assistant_tools.inventory_tool import check_inventory

SKUS20 = [f"KO-SKU-{i:02d}" for i in range(20)]


def run(coro, timeout=10.0):
    return asyncio.run(asyncio.wait_for(coro, timeout))


def timed(coro):
    t0 = time.perf_counter()
    out = run(coro)
    return out, time.perf_counter() - t0


def test_twenty_products_two_stores_is_fast():
    cat = FakeCatalog(latency_s=0.05)
    out, dt = timed(check_inventory(cat, SKUS20, ["012", "087"], deadline_s=3.0))
    assert len(out["items"]) == 40
    assert out["partial"] is False
    assert dt < 0.4, f"40 lookups took {dt:.2f}s; sequential per-pair calls do not fit the budget"


def test_uses_the_batch_endpoint():
    cat = FakeCatalog(latency_s=0.01)
    run(check_inventory(cat, SKUS20, ["012", "087"], deadline_s=3.0))
    assert cat.single_calls == 0, "use POST /inventory/lookup (batch_stock), not one GET per pair"
    assert cat.batch_calls == 1
    assert max(cat.batch_sizes) <= BATCH_MAX


def test_large_requests_split_and_cap_concurrency():
    cat = FakeCatalog(latency_s=0.03)
    skus = [f"S{i:03d}" for i in range(100)]
    out = run(check_inventory(cat, skus, ["012", "045", "087"], deadline_s=3.0))
    assert len(out["items"]) == 300
    assert all(n <= BATCH_MAX for n in cat.batch_sizes)
    assert sum(cat.batch_sizes) == 300
    assert cat.max_in_flight <= 4, f"{cat.max_in_flight} catalog calls in flight; cap it"
    assert out["partial"] is False


def test_values_are_correct_and_in_input_order():
    cat = FakeCatalog(latency_s=0.0)
    out = run(check_inventory(cat, ["B", "A", "C"], ["087", "012"], deadline_s=3.0))
    assert [(i["sku"], i["store_id"]) for i in out["items"]] == [
        ("B", "087"), ("B", "012"), ("A", "087"), ("A", "012"), ("C", "087"), ("C", "012"),
    ]
    for i in out["items"]:
        assert i["available"] == FakeCatalog.truth(i["sku"], i["store_id"])
        assert i["stock_unknown"] is False


def test_deadline_returns_partial_instead_of_failing():
    cat = FakeCatalog(latency_s=1.5)
    out, dt = timed(check_inventory(cat, SKUS20, ["087"], deadline_s=0.2))
    assert dt < 0.45, f"tool took {dt:.2f}s with a 0.2s budget"
    assert out["partial"] is True
    assert len(out["items"]) == 20
    assert all(i["stock_unknown"] and i["available"] is None for i in out["items"])


def test_call_timeout_never_exceeds_remaining_budget():
    cat = FakeCatalog(latency_s=0.01)
    run(check_inventory(cat, SKUS20, ["087"], deadline_s=0.3))
    assert cat.timeouts_seen and max(cat.timeouts_seen) <= 0.3 + 1e-6


def test_a_failed_batch_marks_only_its_items_unknown():
    skus = [f"S{i:03d}" for i in range(60)]  # 60 pairs -> two batches
    cat = FakeCatalog(latency_s=0.01, fail_batch=lambda items: ("S000", "087") in items)
    out = run(check_inventory(cat, skus, ["087"], deadline_s=2.0))
    unknown = [i for i in out["items"] if i["stock_unknown"]]
    known = [i for i in out["items"] if not i["stock_unknown"]]
    assert out["partial"] is True
    assert unknown and known, "one failing batch must not hide the other batch's results"
    assert all(i["available"] == FakeCatalog.truth(i["sku"], "087") for i in known)


def test_empty_and_duplicate_input():
    cat = FakeCatalog(latency_s=0.01)
    assert run(check_inventory(cat, [], ["087"])) == {"items": [], "partial": False}
    assert cat.batch_calls == 0 and cat.single_calls == 0
    out = run(check_inventory(cat, ["A", "A", "B"], ["087"], deadline_s=1.0))
    assert [i["sku"] for i in out["items"]] == ["A", "B"]


def test_small_happy_path_guard():
    cat = FakeCatalog(latency_s=0.01)
    out = run(check_inventory(cat, ["KO-TENT-2P"], ["012"], deadline_s=1.0))
    assert out["items"][0]["available"] == FakeCatalog.truth("KO-TENT-2P", "012")
