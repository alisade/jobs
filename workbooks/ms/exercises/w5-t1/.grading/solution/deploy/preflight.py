"""Release preflight: fail before `pac solution import` if the manifest cannot succeed.

Usage:
  uv run python deploy/preflight.py --manifest deploy/manifest.yaml \
      --inventory deploy/environments/uat.json --artifacts deploy/artifacts.json [--solutions solutions]
Exit 1 and one line per problem; exit 0 when the manifest is safe to run.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

_SOL = re.compile(r"^\s*(?P<name>[^()]+?)\s*\((?P<version>[\d.]+)\)\s*$")


def parse_version(v: str) -> tuple[int, ...]:
    """'2.1.0.0' -> (2, 1, 0, 0). Dataverse versions compare numerically per part."""
    parts = str(v).strip().split(".")
    if not 2 <= len(parts) <= 4 or not all(p.isdigit() for p in parts):
        raise ValueError(f"invalid solution version {v!r}")
    nums = [int(p) for p in parts]
    return tuple(nums + [0] * (4 - len(nums)))


def missing_dependencies(solution_xml: str) -> list[dict]:
    """Parse <MissingDependencies> from an unpacked Solution.xml."""
    root = ET.fromstring(solution_xml)
    out = []
    for md in root.iter("MissingDependency"):
        req = md.find("Required")
        dep = md.find("Dependent")
        if req is None:
            continue
        sol = req.get("solution", "")
        m = _SOL.match(sol)
        out.append({
            "required_type": int(req.get("type", "0")),
            "required": req.get("schemaName") or req.get("id") or "",
            "required_display": req.get("displayName", ""),
            "parent": req.get("parentSchemaName"),
            "solution_name": m.group("name") if m else sol.strip(),
            "solution_version": parse_version(m.group("version")) if m else None,
            "dependent_display": dep.get("displayName", "") if dep is not None else "",
            "dependent_type": int(dep.get("type", "0")) if dep is not None else None,
        })
    return out


def _fmt(v: tuple[int, ...]) -> str:
    return ".".join(str(x) for x in v)


def preflight(manifest: dict, inventory: dict, artifacts: dict, solution_xml_by_name: dict[str, str]) -> list[str]:
    errors: list[str] = []
    installed = {
        s["name"]: {"version": parse_version(s["version"]), "managed": bool(s["managed"])}
        for s in inventory.get("solutions", [])
    }
    arts = {a["file"]: a for a in artifacts.get("artifacts", [])}
    for step in manifest.get("solutions", []):
        name = step["name"]
        version = parse_version(step["version"])
        managed = bool(step.get("managed", False))
        label = f"{name} {_fmt(version)}"

        art = arts.get(step.get("artifact", ""))
        if art is None:
            errors.append(f"{label}: artifact {step.get('artifact')!r} not found in build artifacts")
        else:
            if art["solution"] != name or parse_version(art["version"]) != version:
                errors.append(f"{label}: artifact {art['file']} is {art['solution']} {art['version']}")
            if bool(art["managed"]) != managed:
                errors.append(f"{label}: artifact {art['file']} managed={art['managed']} but manifest managed={managed}")

        current = installed.get(name)
        if current is not None:
            if version < current["version"]:
                errors.append(f"{label}: downgrade, target has {name} {_fmt(current['version'])}")
            if managed and not current["managed"]:
                errors.append(f"{label}: cannot import managed over the unmanaged {name} already in the target")
            if not managed and current["managed"]:
                errors.append(f"{label}: cannot import unmanaged over the managed {name} already in the target")

        xml = solution_xml_by_name.get(name)
        if xml is not None:
            for dep in missing_dependencies(xml):
                need = dep["solution_name"]
                what = f"{dep['required']}" + (f" on {dep['parent']}" if dep["parent"] else "")
                if dep["solution_version"] is None:
                    errors.append(
                        f"{label}: depends on unmanaged component {what} (solution {need!r}); "
                        "add it to a solution in source and re-export"
                    )
                    continue
                have = installed.get(need)
                if have is None or have["version"] < dep["solution_version"]:
                    have_s = _fmt(have["version"]) if have else "nothing"
                    errors.append(
                        f"{label}: requires {need} >= {_fmt(dep['solution_version'])} for {what} "
                        f"(needed by {dep['dependent_display']}); target has {have_s} at this step"
                    )

        installed[name] = {"version": version, "managed": managed}
    return sorted(set(errors), key=errors.index)


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
