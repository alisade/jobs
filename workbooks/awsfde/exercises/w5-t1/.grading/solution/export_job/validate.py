"""Pre-load checks for a tenant's load files, run before the files are handed to the loader."""

from __future__ import annotations

import csv
import pathlib

import networkx as nx


def validate_load(tenant_id: str, nodes_csv: pathlib.Path, edges_csv: pathlib.Path,
                  existing: nx.MultiDiGraph) -> list[str]:
    """Return a list of problems; an empty list means the load may proceed."""
    problems: list[str] = []
    prefix = f"{tenant_id}:"
    batch: dict[str, str] = {}
    with open(nodes_csv, newline="") as fh:
        for row in csv.DictReader(fh):
            nid, t = row.get(":ID", ""), row.get("tenant_id:String", "")
            if t != tenant_id:
                problems.append(f"node {nid}: tenant_id {t!r} is not {tenant_id}")
            if not nid.startswith(prefix):
                problems.append(f"node {nid}: id is not prefixed with {prefix}")
            if nid in batch:
                problems.append(f"node {nid}: duplicate id in this load")
            if nid in existing and existing.nodes[nid].get("tenant_id") != tenant_id:
                problems.append(f"node {nid}: id collides with a {existing.nodes[nid].get('tenant_id')} vertex")
            batch[nid] = t

    def tenant_of(nid: str) -> str | None:
        if nid in batch:
            return batch[nid]
        if nid in existing:
            return existing.nodes[nid].get("tenant_id")
        return None

    with open(edges_csv, newline="") as fh:
        for row in csv.DictReader(fh):
            rid = row.get(":ID", "")
            if not rid.startswith(prefix):
                problems.append(f"relationship {rid}: id is not prefixed with {prefix}")
            for end in (":START_ID", ":END_ID"):
                t = tenant_of(row[end])
                if t is None:
                    problems.append(f"relationship {rid}: unknown endpoint {row[end]}")
                elif t != tenant_id:
                    problems.append(f"relationship {rid}: endpoint {row[end]} belongs to {t}")
    return problems
