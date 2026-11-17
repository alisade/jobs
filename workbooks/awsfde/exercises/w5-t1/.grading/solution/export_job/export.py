"""Write a tenant's supply chain as Neptune openCypher load files (nodes and relationships).

Source rows come from the tenant's ERP extract (data/source/<tenant>.json). Each ERP numbers its
own rows (seq), starting wherever that ERP starts, so seq values collide across tenants. Node and
relationship IDs are global to the graph, so every ID is prefixed with the tenant.
"""

from __future__ import annotations

import csv
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
_TENANT = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")


def node_id(tenant_id: str, kind: str, seq: int) -> str:
    """The :ID of a vertex. kind is sup, part or prod."""
    if not _TENANT.match(tenant_id):
        raise ValueError(f"invalid tenant id {tenant_id!r}")
    if kind not in ("sup", "part", "prod"):
        raise ValueError(f"invalid kind {kind!r}")
    return f"{tenant_id}:{kind}-{seq:03d}"


def export_tenant(tenant_id: str, outdir: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    src = json.loads((ROOT / "data" / "source" / f"{tenant_id}.json").read_text())
    if src["tenant_id"] != tenant_id:
        raise ValueError("source extract belongs to another tenant")
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
            w.writerow([f"{a}-SUPPLIES-{b.split(':', 1)[1]}", a, b, "SUPPLIES"])
        for p, x in src["bom"]:
            a, b = node_id(tenant_id, "part", p), node_id(tenant_id, "prod", x)
            w.writerow([f"{a}-USED_IN-{b.split(':', 1)[1]}", a, b, "USED_IN"])
    return nodes, edges
