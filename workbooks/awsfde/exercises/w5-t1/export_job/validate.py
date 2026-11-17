"""Pre-load checks for a tenant's load files, run before the files are handed to the loader."""

from __future__ import annotations

import pathlib

import networkx as nx


def validate_load(tenant_id: str, nodes_csv: pathlib.Path, edges_csv: pathlib.Path,
                  existing: nx.MultiDiGraph) -> list[str]:
    """Return a list of problems; an empty list means the load may proceed.

    Not implemented yet (planned in ASK-377): the load always proceeds.
    """
    return []
