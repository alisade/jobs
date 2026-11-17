"""Fake Kestrel backend: catalog, inventory and orders (complete).

In production these are the catalog and orders services. The assistant must call them with the
customer's identity, never as a superuser.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class NotFound(Exception):
    pass


class BackendError(Exception):
    pass


PRODUCTS = {
    "KO-TENT-2P": {"sku": "KO-TENT-2P", "name": "Ridgeline 2P Tent", "price_cents": 24900,
                   "review_snippet": "Great tent, easy pitch."},
    "KO-BAG-20F": {"sku": "KO-BAG-20F", "name": "Alpine 20F Sleeping Bag", "price_cents": 15900,
                   "review_snippet": "Warm down bag."},
    "KO-LAMP-1": {"sku": "KO-LAMP-1", "name": "Trail Lantern", "price_cents": 3450,
                  "review_snippet": "Bright and lasts all weekend."},
}

ORDERS = {
    "K-1001": {"order_id": "K-1001", "user_id": "u-ana", "status": "delivered", "items": ["KO-TENT-2P"],
               "delivered_on": "2026-11-02"},
    "K-1002": {"order_id": "K-1002", "user_id": "u-ana", "status": "shipped", "items": ["KO-LAMP-1"],
               "delivered_on": None},
    "K-2001": {"order_id": "K-2001", "user_id": "u-ben", "status": "delivered", "items": ["KO-BAG-20F"],
               "delivered_on": "2026-10-28"},
}


@dataclass
class Store:
    products: dict = field(default_factory=lambda: {k: dict(v) for k, v in PRODUCTS.items()})
    orders: dict = field(default_factory=lambda: {k: dict(v) for k, v in ORDERS.items()})
    stock: dict = field(default_factory=lambda: {("KO-TENT-2P", "012"): 4, ("KO-BAG-20F", "012"): 0,
                                                 ("KO-LAMP-1", "012"): 11})
    returns: list = field(default_factory=list)
    fail_search: bool = False

    def search(self, query: str) -> list[dict]:
        if self.fail_search:
            raise BackendError("catalog-search returned HTTP 503")
        q = query.lower()
        return [dict(p) for p in self.products.values() if any(w in p["name"].lower() for w in q.split())]

    def check_inventory(self, sku: str, store_id: str) -> int:
        if sku not in self.products:
            raise NotFound(f"unknown sku {sku}")
        return self.stock.get((sku, store_id), 0)

    def get_order(self, order_id: str) -> dict:
        """Raw lookup with no permission check (the orders service checks the caller's token)."""
        if order_id not in self.orders:
            raise NotFound(order_id)
        return dict(self.orders[order_id])

    def start_return(self, order_id: str, reason: str) -> dict:
        o = self.get_order(order_id)
        if o["status"] != "delivered":
            raise BackendError(f"order {order_id} is {o['status']}; only delivered orders can be returned")
        rma = f"RMA-{len(self.returns) + 1:04d}"
        self.returns.append({"rma": rma, "order_id": order_id, "reason": reason})
        return {"rma": rma, "order_id": order_id, "label_url": f"https://kestrel.example/returns/{rma}.pdf"}
