"""Loaders for the exercise data. Do not change."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "data"


def jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]


def authored() -> list[dict]:
    return jsonl(ROOT / "authored.jsonl")


def heldout() -> list[dict]:
    return jsonl(ROOT / "heldout.jsonl")


def candidate(name: str) -> list[dict]:
    return jsonl(ROOT / "candidates" / f"{name}.jsonl")


def candidate_models() -> dict:
    return json.loads((ROOT / "candidates" / "models.json").read_text())


def prices() -> dict:
    return json.loads((ROOT / "prices.json").read_text())


CANDIDATES = ["prompt-flash", "fewshot-flash", "tuned-flashlite"]
