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
    out: list[Chunk] = []
    for i, p in enumerate(doc.get("paragraphs", [])):
        if p.get("role") in SKIP_ROLES:
            continue
        page = _page(p)
        out.append(Chunk(f"{blob}#p{page}.para{i}", blob, "paragraph", {"blob": blob, "page": page, "paragraph": i}, p["content"]))
    for t, tab in enumerate(doc.get("tables", [])):
        page = _page(tab)
        rows: dict[int, dict[int, str]] = {}
        header_rows = set()
        for c in tab["cells"]:
            rows.setdefault(c["rowIndex"], {})[c["columnIndex"]] = c["content"]
            if c.get("kind") == "columnHeader":
                header_rows.add(c["rowIndex"])
        ncol = tab["columnCount"]
        header = " | ".join(" | ".join(rows[h].get(k, "") for k in range(ncol)) for h in sorted(header_rows))
        for r in sorted(rows):
            if r in header_rows:
                continue
            cells = [rows[r].get(k, "") for k in range(ncol)]
            line = " | ".join(cells)
            text = f"{header}\n{line}" if header else line
            out.append(Chunk(f"{blob}#p{page}.t{t}.r{r}", blob, "table_row", {"blob": blob, "page": page, "table": t, "row": r}, text, cells))
    return out


def csv_chunks(blob: str, data: str) -> list[Chunk]:
    lines = [ln for ln in data.splitlines() if ln.strip()]
    if not lines:
        return []
    header = lines[0]
    out = []
    for n, line in enumerate(lines[1:], start=1):
        cells = next(csv.reader(io.StringIO(line)))
        out.append(Chunk(f"{blob}#row{n}", blob, "csv_row", {"blob": blob, "row": n}, f"{header}\n{line}", cells))
    return out


def build_chunks(container) -> list[Chunk]:
    chunks: list[Chunk] = []
    for props in container.list_blobs():
        name = props.name
        if name.endswith(".layout.json"):
            chunks.extend(layout_chunks(name, json.loads(container.download_blob(name).readall())))
        elif name.endswith(".csv"):
            chunks.extend(csv_chunks(name, container.download_blob(name).readall().decode("utf-8")))
    return chunks
