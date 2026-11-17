"""Remembers the outcome per supplier item so unchanged items are never sent to the model twice
(complete; you may use it as is). Backed by a dict; pass a path to persist as JSON between runs."""

from __future__ import annotations

import json
import os


class EnrichmentStore:
    def __init__(self, path: str | None = None) -> None:
        self.path = path
        self._data: dict[str, dict] = {}
        if path and os.path.exists(path):
            with open(path, encoding="utf8") as f:
                self._data = json.load(f)

    def get(self, supplier_sku: str) -> dict | None:
        return self._data.get(supplier_sku)

    def put(self, supplier_sku: str, record: dict) -> None:
        """record: {"source_hash": str, "status": "published" | "review", "attributes": dict | None,
        "reasons": list[str]}"""
        self._data[supplier_sku] = record
        if self.path:
            with open(self.path, "w", encoding="utf8") as f:
                json.dump(self._data, f, indent=1, sort_keys=True)
