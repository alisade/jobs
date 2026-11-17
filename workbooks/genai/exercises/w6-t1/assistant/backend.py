"""Fake inventory/orders backend and a deterministic stand-in for the assistant agent (complete).

The real agent calls the model and tools; this one decides by keywords so the incident is
reproducible offline. What matters for the cache is the AgentResult: the text and which tools the
answer depended on.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Inventory:
    stock: dict = field(default_factory=lambda: {
        ("KO-COOL-45", "012"): 6, ("KO-COOL-45", "087"): 0,
        ("KO-TENT-2P", "012"): 3, ("KO-TENT-2P", "087"): 2,
    })
    calls: int = 0

    def available(self, sku: str, store_id: str) -> int:
        self.calls += 1
        return self.stock.get((sku, store_id), 0)


ORDERS = {
    "u-ana": {"order_id": "K-1001", "status": "out for delivery", "eta": "today 2-5 pm"},
    "u-ben": {"order_id": "K-2001", "status": "delivered", "eta": None},
}

PRODUCTS = {"glacier 45": ("KO-COOL-45", "Glacier 45qt Cooler", 21900), "ridgeline": ("KO-TENT-2P", "Ridgeline 2P Tent", 24900)}


@dataclass
class AgentResult:
    text: str
    tools_used: list[str]


@dataclass
class FakeAgent:
    inventory: Inventory
    calls: int = 0

    def run(self, user_id: str, store_id: str, question: str) -> AgentResult:
        self.calls += 1
        q = question.lower()
        if "return policy" in q or "returns" in q:
            return AgentResult("You can return unused items within 60 days with a receipt.", ["policy_lookup"])
        if "my order" in q:
            o = ORDERS.get(user_id)
            if not o:
                return AgentResult("I could not find a recent order.", ["get_order_status"])
            eta = f", arriving {o['eta']}" if o["eta"] else ""
            return AgentResult(f"Order {o['order_id']} is {o['status']}{eta}.", ["get_order_status"])
        for key, (sku, name, price) in PRODUCTS.items():
            if key in q:
                if "stock" in q:
                    n = self.inventory.available(sku, store_id)
                    status = f"in stock ({n} left)" if n > 0 else "sold out"
                    return AgentResult(f"The {name} is {status} at store {store_id}.", ["search_products", "check_inventory"])
                return AgentResult(f"The {name} is ${price / 100:.2f}.", ["search_products"])
        return AgentResult("I can help with products, stock, orders and returns.", [])
