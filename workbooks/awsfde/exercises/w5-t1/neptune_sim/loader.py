"""Bulk load openCypher CSV files into one shared graph, the way the platform loads every tenant.

Node and relationship IDs are global to the graph. The Neptune docs say node IDs should be unique
across all node files in the current and previous loads. This simulator models what happens when they
are not as an upsert: a node ID that already exists is the same vertex (labels merged, properties
from the later file overwrite), and a relationship ID that already exists is replaced. It returns
load statistics in the spirit of a load job's status.
"""

from __future__ import annotations

import csv
import pathlib

import networkx as nx

_CAST = {"String": str, "Int": int, "Long": int, "Double": float}


def _props(row: dict) -> dict:
    out = {}
    for col, val in row.items():
        if col.startswith(":") or val in ("", None):
            continue
        name, _, typ = col.partition(":")
        out[name] = _CAST.get(typ or "String", str)(val)
    return out


def bulk_load(g: nx.MultiDiGraph, nodes_csv: pathlib.Path, edges_csv: pathlib.Path) -> dict:
    stats = {"nodes_created": 0, "nodes_updated": 0, "edges_created": 0, "edges_replaced": 0,
             "updated_node_ids": [], "errors": []}
    with open(nodes_csv, newline="") as fh:
        for row in csv.DictReader(fh):
            nid, labels, props = row[":ID"], set(row[":LABEL"].split(";")), _props(row)
            if nid in g:
                g.nodes[nid]["__labels__"] |= labels
                g.nodes[nid].update(props)
                stats["nodes_updated"] += 1
                stats["updated_node_ids"].append(nid)
            else:
                g.add_node(nid, __labels__=labels, **props)
                stats["nodes_created"] += 1
    with open(edges_csv, newline="") as fh:
        for row in csv.DictReader(fh):
            a, b, rid = row[":START_ID"], row[":END_ID"], row[":ID"]
            if a not in g or b not in g:
                stats["errors"].append(f"{rid}: unknown endpoint")
                continue
            dup = [(u, v, k) for u, v, k, d in g.edges(keys=True, data=True) if d.get("rel_id") == rid]
            for u, v, k in dup:
                g.remove_edge(u, v, k)
            g.add_edge(a, b, __labels__={row[":TYPE"]}, rel_id=rid, **_props(row))
            stats["edges_replaced" if dup else "edges_created"] += 1
    return stats
