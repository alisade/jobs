import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def load_json(rel: str):
    return json.loads((ROOT / rel).read_text())


@pytest.fixture
def config():
    return load_json("config.json")


@pytest.fixture
def lexicon():
    return load_json("data/tone_lexicon.json")


def sample(pid, prices, text="Here are options.", s=0):
    return {"probe_id": pid, "sample": s, "text": text,
            "recommendations": [{"sku": f"KO-{i}", "price_cents": p} for i, p in enumerate(prices)]}
