"""Write a tenant's supply chain as Neptune openCypher load files (nodes and relationships).

Source rows come from the tenant's ERP extract (data/source/<tenant>.json). Each ERP numbers its
own rows (seq), starting wherever that ERP starts.
"""

from __future__ import annotations

import csv
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent


def node_id(tenant_id: str, kind: str, seq: int) -> str:
    """The :ID of a vertex. kind is sup, part or prod."""
    return f"{kind}-{seq:03d}"


def export_tenant(tenant_id: str, outdir: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    src = json.loads((ROOT / "data" / "source" / f"{tenant_id}.json").read_text())
    outdir.mkdir(parents=True, exist_ok=True)
    nodes = outdir / f"{tenant_id}-nodes.csv"
    edges = outdir / f"{tenant_id}-edges.csv"
    with nodes.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([":ID", ":LABEL", "name:String", "tenant_id:String"])
        for kind, label, rows in (("sup", "Supplier", src["suppliers"]), ("part", "Part", src["parts"]),
                                  ("prod", "Product", src["products"])):
            for r in rows:
                w.writerow([node_id(tenant_id, kind, r["seq"]), label, r["name"], tenant_id])
    with edges.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([":ID", ":START_ID", ":END_ID", ":TYPE"])
        for s, p in src["supplies"]:
            a, b = node_id(tenant_id, "sup", s), node_id(tenant_id, "part", p)
            w.writerow([f"{a}-SUPPLIES-{b}", a, b, "SUPPLIES"])
        for p, x in src["bom"]:
            a, b = node_id(tenant_id, "part", p), node_id(tenant_id, "prod", x)
            w.writerow([f"{a}-USED_IN-{b}", a, b, "USED_IN"])
    return nodes, edges
