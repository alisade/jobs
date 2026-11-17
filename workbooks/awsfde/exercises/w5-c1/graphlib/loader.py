"""Load Neptune openCypher CSV files (nodes and relationships) into a networkx MultiDiGraph (done).

Format (Neptune "Load format for openCypher data"): node files have :ID and :LABEL system columns
(several labels separated by ";"), relationship files have :ID, :START_ID, :END_ID and :TYPE, and
property columns are name:Type (String, Int, Long, Double, Bool, ...). Empty cells mean "no
property". Labels and types go into the __labels__ attribute that grand-cypher matches on.
"""

from __future__ import annotations

import csv
import pathlib

import networkx as nx

GRAPH_DIR = pathlib.Path(__file__).resolve().parent.parent / "graph"
_CAST = {"String": str, "Int": int, "Long": int, "Double": float, "Float": float,
         "Bool": lambda v: v.lower() == "true", "Boolean": lambda v: v.lower() == "true"}


def _props(row: dict) -> dict:
    out = {}
    for col, val in row.items():
        if col.startswith(":") or val in ("", None):
            continue
        name, _, typ = col.partition(":")
        out[name] = _CAST.get(typ or "String", str)(val)
    return out


def load_graph(nodes_csv: pathlib.Path | None = None, edges_csv: pathlib.Path | None = None) -> nx.MultiDiGraph:
    g = nx.MultiDiGraph()
    with open(nodes_csv or GRAPH_DIR / "nodes.csv", newline="") as fh:
        for row in csv.DictReader(fh):
            g.add_node(row[":ID"], __labels__=set(row[":LABEL"].split(";")), **_props(row))
    with open(edges_csv or GRAPH_DIR / "edges.csv", newline="") as fh:
        for row in csv.DictReader(fh):
            for end in (":START_ID", ":END_ID"):
                if row[end] not in g:
                    raise ValueError(f"relationship {row[':ID']} references unknown node {row[end]}")
            # grand-cypher matches incorrectly on MultiDiGraph edges with explicit string keys, so the
            # relationship id is stored as the edge attribute "rel_id" instead of the networkx key.
            g.add_edge(row[":START_ID"], row[":END_ID"], __labels__={row[":TYPE"]}, rel_id=row[":ID"], **_props(row))
    return g
