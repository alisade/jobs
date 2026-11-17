"""Turn the evidence container into citable chunks with locators."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field

SKIP_ROLES = {"pageHeader", "pageFooter", "pageNumber"}


@dataclass
class Chunk:
    id: str
    blob: str
    kind: str  # "paragraph" | "table_row" | "csv_row"
    locator: dict
    text: str
    cells: list[str] = field(default_factory=list)  # table_row / csv_row: cell values by column


def _page(region_holder: dict) -> int:
    return int(region_holder["boundingRegions"][0]["pageNumber"])


def layout_chunks(blob: str, doc: dict) -> list[Chunk]:
    """Paragraph chunks (skip SKIP_ROLES) and one chunk per table data row with the header row(s) repeated."""
    raise NotImplementedError("TODO: README task 1 (layout_chunks)")


def csv_chunks(blob: str, data: str) -> list[Chunk]:
    """One chunk per data row: text = header line + newline + the raw row; cells = parsed values."""
    raise NotImplementedError("TODO: README task 1 (csv_chunks)")


def build_chunks(container) -> list[Chunk]:
    chunks: list[Chunk] = []
    for props in container.list_blobs():
        name = props.name
        if name.endswith(".layout.json"):
            chunks.extend(layout_chunks(name, json.loads(container.download_blob(name).readall())))
        elif name.endswith(".csv"):
            chunks.extend(csv_chunks(name, container.download_blob(name).readall().decode("utf-8")))
    return chunks
