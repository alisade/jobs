import asyncio

from assistant_tools.catalog_client import FakeCatalog
from assistant_tools.inventory_tool import check_inventory


def run(coro, timeout=10.0):
    return asyncio.run(asyncio.wait_for(coro, timeout))


def test_two_products_one_store():
    cat = FakeCatalog(latency_s=0.01)
    out = run(check_inventory(cat, ["KO-TENT-2P", "KO-LAMP-1"], ["087"]))
    assert [i["sku"] for i in out["items"]] == ["KO-TENT-2P", "KO-LAMP-1"]
    assert out["items"][0]["available"] == FakeCatalog.truth("KO-TENT-2P", "087")
    assert out["partial"] is False


def test_every_pair_is_reported():
    cat = FakeCatalog(latency_s=0.0)
    out = run(check_inventory(cat, ["A", "B"], ["012", "087"]))
    assert [(i["sku"], i["store_id"]) for i in out["items"]] == [
        ("A", "012"), ("A", "087"), ("B", "012"), ("B", "087"),
    ]
