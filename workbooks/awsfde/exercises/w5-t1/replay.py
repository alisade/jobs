"""Replay the graph's load history and the reported questions; write run/ (done).

Usage: python replay.py [outdir]
Load history: acme-foods on 2026-08-02, brightline-health on 2026-11-11 (onboarding), into one graph.
"""

from __future__ import annotations

import json
import pathlib
import sys

import networkx as nx

from export_job.export import export_tenant
from export_job.validate import validate_load
from graph_tool.run import suppliers_of_product
from neptune_sim.loader import bulk_load

ROOT = pathlib.Path(__file__).resolve().parent
LOADS = [("2026-08-02T03:10:00Z", "acme-foods"), ("2026-11-11T03:10:00Z", "brightline-health")]


def build_graph(outdir: pathlib.Path) -> tuple[nx.MultiDiGraph, list[dict]]:
    g = nx.MultiDiGraph()
    jobs = []
    for ts, tenant in LOADS:
        nodes, edges = export_tenant(tenant, outdir / "load")
        problems = validate_load(tenant, nodes, edges, g)
        job = {"ts": ts, "tenant_id": tenant, "files": [nodes.name, edges.name]}
        if problems:
            job.update(status="LOAD_REJECTED_BY_VALIDATOR", problems=problems)
        else:
            job.update(status="LOAD_COMPLETED", **bulk_load(g, nodes, edges))
        jobs.append(job)
    return g, jobs


def main(out: str = "run") -> int:
    outdir = ROOT / out
    outdir.mkdir(exist_ok=True)
    g, jobs = build_graph(outdir)
    (outdir / "load-jobs.log").write_text("".join(json.dumps(j) + "\n" for j in jobs))
    lines, qlog = [], []
    for line in (ROOT / "evidence" / "questions.jsonl").read_text().splitlines():
        q = json.loads(line)
        rows = suppliers_of_product(g, q["tenant_id"], q["product"])
        qlog.append({**q, "tool": "suppliers_of_product", "rows": rows})
        lines.append(f"{q['tenant_id']:18} {q['product']:15} -> {[r[0] for r in rows]}")
    (outdir / "query.log").write_text("".join(json.dumps(x) + "\n" for x in qlog))
    (outdir / "summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
