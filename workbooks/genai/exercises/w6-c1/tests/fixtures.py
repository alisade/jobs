"""Supplier items and model answers used by the tests."""

import json

TENT = {
    "supplier_sku": "NWT-4471",
    "supplier": "Northwind Trail Co",
    "description": (
        "NWT Ridgeline two person backpacking tent. Freestanding, 2 doors, 2 vestibules. "
        "Fly: 20D ripstop nylon, 3000mm coating. Trail weight 1.9 kg. Color: sage green. "
        "Packed size 46 x 15 cm. Spot clean only, dry before storing."
    ),
}
COOLER = {
    "supplier_sku": "GLC-45R",
    "supplier": "Glacier Coolers",
    "description": (
        "Glacier 45 qt rotomolded cooler with 2 in. insulation and freezer-grade gasket. "
        "Holds ice up to 5 days. Weight 23.5 lb empty. Color: slate. Wash with mild soap."
    ),
}
JACKET = {
    "supplier_sku": "DPR-RJ2",
    "supplier": "Downpour Outdoor",
    "description": (
        "Downpour 2.5-layer rain jacket, fully seam taped, waterproof and breathable shell. "
        "Recycled polyester face fabric. Weighs 340 g. Color: tide blue. Machine wash cold."
    ),
}
LANTERN = {
    "supplier_sku": "BCN-L400",
    "supplier": "Beacon Lighting",
    "description": "Rechargeable camp lantern, 400 lumens, 3 modes, USB-C. 280 g. Color: black.",
}


def ans(**over) -> str:
    base = {
        "title": "Ridgeline 2-Person Backpacking Tent",
        "category": "tents",
        "material": "ripstop nylon",
        "weight_kg": 1.9,
        "capacity_l": None,
        "color": "sage green",
        "care": "Spot clean only; dry before storing.",
        "description": "Freestanding two-person tent with two doors and two vestibules.",
        "confidence": 0.92,
    }
    base.update(over)
    return json.dumps(base)


def cooler_ans(**over) -> str:
    base = {
        "title": "Glacier 45 qt Rotomolded Cooler",
        "category": "coolers",
        "material": None,
        "weight_kg": 10.66,
        "capacity_l": 42.6,
        "color": "slate",
        "care": "Wash with mild soap.",
        "description": "Rotomolded cooler with thick insulation that holds ice for up to five days.",
        "confidence": 0.88,
    }
    base.update(over)
    return json.dumps(base)


def jacket_ans(**over) -> str:
    base = {
        "title": "Downpour 2.5-Layer Rain Jacket",
        "category": "jackets",
        "material": "recycled polyester",
        "weight_kg": 0.34,
        "capacity_l": None,
        "color": "tide blue",
        "care": "Machine wash cold.",
        "description": "Fully seam-taped waterproof, breathable rain shell.",
        "confidence": 0.9,
    }
    base.update(over)
    return json.dumps(base)


def lantern_ans(**over) -> str:
    base = {
        "title": "Beacon 400 Lumen Rechargeable Lantern",
        "category": "lighting",
        "material": None,
        "weight_kg": 0.28,
        "capacity_l": None,
        "color": "black",
        "care": None,
        "description": "Rechargeable 400 lumen lantern with three modes and USB-C charging.",
        "confidence": 0.9,
    }
    base.update(over)
    return json.dumps(base)
