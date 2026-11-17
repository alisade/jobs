"""Run the tool query on the local graph (done). Neptune binds $parameters server-side; locally they are
substituted as literals and the query runs on grand-cypher."""

from __future__ import annotations

import json
import re

import networkx as nx
from grandcypher import GrandCypher

from .query import SUPPLIERS_OF_PRODUCT


def bind(query: str, params: dict) -> str:
    return re.sub(r"\$([A-Za-z_]\w*)", lambda m: json.dumps(params[m.group(1)]), query)


def run(g: nx.MultiDiGraph, query: str, params: dict) -> list[tuple]:
    res = GrandCypher(g).run(bind(query, params))
    cols = list(res)
    n = len(res[cols[0]]) if cols else 0
    return [tuple(res[c][i] for c in cols) for i in range(n)]


def suppliers_of_product(g: nx.MultiDiGraph, tenant_id: str, product: str) -> list[tuple]:
    return run(g, SUPPLIERS_OF_PRODUCT, {"tenant_id": tenant_id, "product": product})
