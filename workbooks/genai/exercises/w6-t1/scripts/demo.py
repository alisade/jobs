"""Replay Black Friday at stores 012 and 087 through the assistant and its answer cache."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from assistant.backend import FakeAgent, Inventory  # noqa: E402
from assistant.cache import AnswerCache  # noqa: E402
from assistant.pipeline import Assistant  # noqa: E402

T0 = 1_764_316_800.0  # 2026-11-28 08:00 PT
now = [T0]
inv = Inventory()
a = Assistant(FakeAgent(inv), AnswerCache(clock=lambda: now[0]))

script = [
    (0, "u-assoc-0141", "012", "Is the Glacier 45 cooler in stock?", None),
    (5, "u-guest-8812", "045", "What is your return policy?", None),
    (90, "u-guest-1290", "012", "what is your return policy", None),
    (240, None, None, None, ("KO-COOL-45", "012", 0)),
    (300, "u-assoc-0141", "012", "is the glacier 45 cooler in stock?", None),
    (600, "u-assoc-0877", "087", "Is the Glacier 45 cooler in stock", None),
    (601, "u-ana", "012", "Where is my order?", None),
    (602, "u-ben", "012", "where is my order", None),
]
for minutes, user, store, q, change in script:
    now[0] = T0 + minutes * 60
    hh, mm = divmod(8 * 60 + minutes, 60)
    if change:
        sku, st, n = change
        inv.stock[(sku, st)] = n
        print(f"{hh:02d}:{mm:02d}  [inventory] {sku} at store {st} -> {n} (true stock)")
        continue
    r = a.ask(user, store, q)
    print(f"{hh:02d}:{mm:02d}  store={store} user={user:<13} hit={str(r.cache_hit):<5} Q: {q}")
    print(f"        A: {r.text}")
print(f"\ncache hits={a.cache.hits} misses={a.cache.misses}")
