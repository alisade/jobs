"""Fake Kestrel store systems for the associate MCP server (complete; do not change)."""

from __future__ import annotations

from dataclasses import dataclass, field

_NAMES = [
    ("KO-TENT-1P", "Solo Trek 1P Tent", 18900, "A12"), ("KO-TENT-2P", "Ridgeline 2P Tent", 24900, "A12"),
    ("KO-TENT-3P", "Basecamp 3P Tent", 32900, "A12"), ("KO-TENT-6P", "Lodge 6P Cabin Tent", 44900, "A13"),
    ("KO-TENT-FP", "Footprint for Ridgeline Tent", 3900, "A12"), ("KO-TENT-STK", "Aluminum Tent Stakes 8pk", 1900, "A14"),
    ("KO-TENT-RPR", "Tent Repair Kit", 1400, "A14"), ("KO-BAG-20F", "Alpine 20F Sleeping Bag", 15900, "B03"),
    ("KO-BAG-40F", "Summer 40F Sleeping Bag", 8900, "B03"), ("KO-PAD-INF", "Cloudrest Inflatable Pad", 7900, "B04"),
    ("KO-LAMP-1", "Trail Lantern", 3450, "C07"), ("KO-HEAD-300", "Beacon 300 Headlamp", 2900, "C07"),
    ("KO-STOVE-1", "Ember Canister Stove", 5900, "D02"), ("KO-COOL-45", "Glacier 45qt Cooler", 21900, "D09"),
    ("KO-PACK-45", "Switchback 45L Pack", 16900, "E01"), ("KO-JKT-RAIN", "Downpour Rain Jacket", 12900, "F05"),
]


@dataclass
class Backend:
    products: dict = field(default_factory=lambda: {
        sku: {"sku": sku, "name": name, "price_cents": price, "aisle": aisle,
              "description": f"{name}. Full marketing copy, care instructions and specs (about 2 KB in production).",
              "supplier_cost_cents": price // 2}
        for sku, name, price, aisle in _NAMES
    })
    stock: dict = field(default_factory=lambda: {("KO-TENT-2P", "012"): 3, ("KO-TENT-2P", "087"): 0,
                                                 ("KO-LAMP-1", "012"): 9, ("KO-COOL-45", "012"): 1})
    orders: dict = field(default_factory=lambda: {
        "K-5501": {"order_id": "K-5501", "store_id": "012", "status": "ready_for_pickup", "items": ["KO-LAMP-1"],
                   "customer": {"name": "Maya Okafor", "email": "maya.o@example.com", "phone": "+1-555-0100"}},
        "K-5502": {"order_id": "K-5502", "store_id": "087", "status": "picking", "items": ["KO-TENT-2P"],
                   "customer": {"name": "Lee Park", "email": "lee.p@example.com", "phone": "+1-555-0101"}},
    })
    hours: dict = field(default_factory=lambda: {"012": "Mon-Sat 9:00-21:00, Sun 10:00-18:00",
                                                 "087": "Mon-Sun 8:00-22:00"})
    holds: list = field(default_factory=list)

    def search(self, query: str) -> list[dict]:
        words = query.lower().split()
        return [dict(p) for p in self.products.values() if all(w in p["name"].lower() for w in words)]

    def available(self, sku: str, store_id: str) -> int:
        return self.stock.get((sku, store_id), 0)

    def place_hold(self, sku: str, store_id: str, customer_name: str, quantity: int) -> dict:
        self.stock[(sku, store_id)] = self.available(sku, store_id) - quantity
        h = {"hold_id": f"H-{len(self.holds) + 1:04d}", "sku": sku, "store_id": store_id,
             "customer_name": customer_name, "quantity": quantity}
        self.holds.append(h)
        return h
