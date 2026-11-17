"""Product rows for local runs. In production these come from Postgres (catalog-db)."""

PRODUCTS = [
    {"sku": "KO-TENT-2P", "name": "Ridgeline 2P Tent", "category": "tents", "price_cents": 24900},
    {"sku": "KO-TENT-3P", "name": "Basecamp 3P Tent", "category": "tents", "price_cents": 32900},
    {"sku": "KO-TENT-1P", "name": "Solo Trek 1P Tent", "category": "tents", "price_cents": 18900},
    {"sku": "KO-BAG-20F", "name": "Alpine 20F Sleeping Bag", "category": "sleeping", "price_cents": 15900},
    {"sku": "KO-BAG-40F", "name": "Summer 40F Sleeping Bag", "category": "sleeping", "price_cents": 8900},
    {"sku": "KO-PAD-INF", "name": "Cloudrest Inflatable Pad", "category": "sleeping", "price_cents": 7900},
    {"sku": "KO-LAMP-1", "name": "Trail Lantern", "category": "lighting", "price_cents": 3450},
    {"sku": "KO-HEAD-300", "name": "Beacon 300 Headlamp", "category": "lighting", "price_cents": 2900},
    {"sku": "KO-STOVE-1", "name": "Ember Canister Stove", "category": "cooking", "price_cents": 5900},
    {"sku": "KO-POT-SET", "name": "Nesting Cook Set", "category": "cooking", "price_cents": 4500},
    {"sku": "KO-PACK-45", "name": "Switchback 45L Pack", "category": "packs", "price_cents": 16900},
    {"sku": "KO-PACK-28", "name": "Daytripper 28L Pack", "category": "packs", "price_cents": 8900},
    {"sku": "KO-JKT-RAIN", "name": "Downpour Rain Jacket", "category": "apparel", "price_cents": 12900},
    {"sku": "KO-JKT-FLC", "name": "Hearth Fleece Jacket", "category": "apparel", "price_cents": 7900},
    {"sku": "KO-CHAIR-1", "name": "Fireside Camp Chair", "category": "furniture", "price_cents": 5400},
    {"sku": "KO-TABLE-1", "name": "Fold-flat Camp Table", "category": "furniture", "price_cents": 6900},
    {"sku": "KO-COOL-45", "name": "Glacier 45qt Cooler", "category": "cooking", "price_cents": 21900},
    {"sku": "KO-BOTL-1L", "name": "Insulated 1L Bottle", "category": "cooking", "price_cents": 3200},
    {"sku": "KO-HAMK-1", "name": "Canopy Hammock", "category": "furniture", "price_cents": 6400},
    {"sku": "KO-TARP-10", "name": "Shelter Tarp 10x10", "category": "tents", "price_cents": 7400},
]


def search_rows(q: str, category: str | None, limit: int) -> list[dict]:
    terms = [t for t in q.lower().split() if t]
    out = []
    for row in PRODUCTS:
        hay = (row["name"] + " " + row["category"]).lower()
        if category and row["category"] != category:
            continue
        if all(t in hay for t in terms):
            out.append(dict(row))
    out.sort(key=lambda r: (r["price_cents"], r["sku"]))
    return out[:limit]
