"""Run an openCypher query with $parameters against the local graph (done).

The local engine is grand-cypher (openCypher on networkx). It supports a subset of openCypher;
see the README's "Local engine notes". Parameters are substituted as literals before execution
(Neptune binds them server-side; the query text you write is the same).
"""

from __future__ import annotations

import json
import pathlib
import re

import networkx as nx
from grandcypher import GrandCypher

QUERY_DIR = pathlib.Path(__file__).resolve().parent.parent / "queries"
_PARAM = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")


def read_query(name: str) -> str:
    """Query text of queries/<name>.cypher without // comment lines."""
    text = (QUERY_DIR / f"{name}.cypher").read_text()
    return "\n".join(line for line in text.splitlines() if not line.strip().startswith("//")).strip()


def bind(query: str, params: dict) -> str:
    def sub(m: re.Match) -> str:
        key = m.group(1)
        if key not in params:
            raise KeyError(f"query uses ${key} but no value was given")
        v = params[key]
        if isinstance(v, bool) or not isinstance(v, (int, float, str)):
            raise TypeError(f"unsupported parameter type for ${key}")
        return json.dumps(v) if isinstance(v, str) else str(v)
    return _PARAM.sub(sub, query)


def run(g: nx.MultiDiGraph, query: str, params: dict | None = None) -> list[tuple]:
    """Execute and return rows as tuples in RETURN column order."""
    if not query.strip():
        raise ValueError("empty query")
    res = GrandCypher(g).run(bind(query, params or {}))
    cols = list(res)
    n = len(res[cols[0]]) if cols else 0
    return [tuple(res[c][i] for c in cols) for i in range(n)]
