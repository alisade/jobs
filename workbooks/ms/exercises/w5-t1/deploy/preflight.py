"""Release preflight: fail before `pac solution import` if the manifest cannot succeed.

Usage:
  uv run python deploy/preflight.py --manifest deploy/manifest.yaml \
      --inventory deploy/environments/uat.json --artifacts deploy/artifacts.json [--solutions solutions]
Exit 1 and one line per problem; exit 0 when the manifest is safe to run.

TODO (part of the fix): implement parse_version, missing_dependencies and preflight.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

def parse_version(v: str) -> tuple[int, ...]:
    """'2.1.0.0' -> (2, 1, 0, 0). Dataverse versions compare numerically per part (2.10 > 2.9).
    Accept 2 to 4 numeric parts (pad with zeros); raise ValueError otherwise."""
    # TODO
    raise NotImplementedError


def missing_dependencies(solution_xml: str) -> list[dict]:
    """Parse <MissingDependencies> from an unpacked Solution.xml.

    One dict per <MissingDependency> with keys: required_type (int), required (schemaName or id),
    required_display, parent (parentSchemaName or None), solution_name, solution_version
    (tuple from "Name (1.2.3.4)", or None when the solution attribute has no version, e.g. "Active"),
    dependent_display, dependent_type (int or None).
    """
    # TODO
    raise NotImplementedError


def preflight(manifest: dict, inventory: dict, artifacts: dict, solution_xml_by_name: dict[str, str]) -> list[str]:
    """Simulate the manifest in order against the target inventory. Return one message per problem.

    See README section "Preflight" for the rules. An empty list means the release can run.
    """
    # TODO
    raise NotImplementedError


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="deploy/manifest.yaml")
    ap.add_argument("--inventory", default="deploy/environments/uat.json")
    ap.add_argument("--artifacts", default="deploy/artifacts.json")
    ap.add_argument("--solutions", default="solutions")
    a = ap.parse_args()
    manifest = yaml.safe_load(Path(a.manifest).read_text())
    xmls = {}
    for p in Path(a.solutions).glob("*/src/Other/Solution.xml"):
        xmls[p.parent.parent.parent.name] = p.read_text()
    errors = preflight(
        manifest,
        json.loads(Path(a.inventory).read_text()),
        json.loads(Path(a.artifacts).read_text()),
        xmls,
    )
    for e in errors:
        print(f"PREFLIGHT FAIL {e}")
    print(f"preflight: {len(errors)} problem(s) for {manifest.get('environment')}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
