"""python -m pipeline.run data/requests.json out/  -> out/routes.json, prints a summary and warnings."""

from __future__ import annotations

import collections
import json
import logging
import sys
from pathlib import Path

from .criteria_engine import route
from .mapper import to_bundle
from .validator import validate

log = logging.getLogger("pipeline.run")


def run(src: str | Path) -> list[dict]:
    out = []
    for rec in json.loads(Path(src).read_text()):
        b = to_bundle(rec)
        errors, warnings = validate(b)
        for w in warnings:
            log.warning("%s: %s", rec["case_id"], w)
        if errors:
            out.append({"case_id": rec["case_id"], "route": "rejected", "reason": "; ".join(errors)})
            continue
        out.append(route(b))
    return out


def main(argv):
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    routes = run(argv[1])
    Path(argv[2]).mkdir(parents=True, exist_ok=True)
    (Path(argv[2]) / "routes.json").write_text(json.dumps(routes, indent=2) + "\n")
    c = collections.Counter((r["route"], r.get("reason")) for r in routes)
    for k, v in sorted(c.items()):
        log.info("route=%s reason=%s count=%d", k[0], k[1], v)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
