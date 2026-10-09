"""Offline dry-run of fabric-cicd parameterization (the subset this repo uses).

Renders the git-synced workspace folder for one target environment, the way
fabric-cicd's FabricWorkspace(..., environment=ENV).publish_all_items() rewrites
item definitions before publishing. Nothing is sent to Fabric.

Supported (mirrors https://microsoft.github.io/fabric-cicd/latest/how_to/parameterization/):
  find_replace:      find_value, replace_value{ENV|_ALL_}, is_regex (capture group 1), ignore_case,
                     item_type / item_name / file_path filters (string or list; all given filters must match)
  key_value_replace: find_key of the form $.properties.activities[?(@.name=="X")].typeProperties.<key>
  replace_value variables: $workspace.$id, $workspace.$name, $items.<type>.<name>.$id
Behaviour that matters here, as documented upstream:
  * "If at least one filter value does not match, the replacement will be skipped for that file."
  * A literal find_value that matches nothing is not an error.
  * If the environment is not a key in replace_value, that replacement is skipped.
  * .platform files are never parameterized.
  * Only item folders are published; parameter.yml itself is not part of the rendered output.

Usage: uv run python deploy/render.py --env PROD [--workspace workspace] [--targets deploy/targets.json] --out DIR
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import shutil
from pathlib import Path

import yaml


def _as_list(v):
    if v is None:
        return None
    return v if isinstance(v, list) else [v]


def load_items(workspace: Path) -> list[dict]:
    """One dict per item folder: type, name, folder, files (relative to workspace, '/'-prefixed)."""
    items = []
    for plat in sorted(workspace.rglob(".platform")):
        meta = json.loads(plat.read_text())["metadata"]
        folder = plat.parent
        files = [p for p in sorted(folder.rglob("*")) if p.is_file() and p.name != ".platform"]
        items.append({"type": meta["type"], "name": meta["displayName"], "folder": folder, "files": files})
    return items


def resolve_value(value: str, env: str, targets: dict) -> str:
    t = targets[env]
    if value in ("$workspace.$id", "$workspace.id"):
        return t["workspace_id"]
    if value == "$workspace.$name":
        return t["workspace_name"]
    m = re.fullmatch(r"\$items\.([^.]+)\.(.+)\.\$id", value)
    if m:
        itype, iname = m.group(1), m.group(2)
        try:
            return t["items"][itype][iname]
        except KeyError:
            raise SystemExit(
                f"[ERROR] parameter.yml: {value} does not resolve: no {itype} named '{iname}' in {env}"
            )
    return value


def env_value(replace_value: dict, env: str):
    for k, v in replace_value.items():
        if k.lower() == "_all_":
            return v
    return replace_value.get(env)


def filters_match(entry: dict, item: dict, rel: str) -> bool:
    types = _as_list(entry.get("item_type"))
    names = _as_list(entry.get("item_name"))
    paths = _as_list(entry.get("file_path"))
    if types is not None and item["type"] not in types:
        return False
    if names is not None and item["name"] not in names:
        return False
    if paths is not None and not any(fnmatch.fnmatch(rel, p) or rel == p for p in paths):
        return False
    return True


def _truthy(v) -> bool:
    return str(v).lower() == "true"


def apply_find_replace(text: str, entry: dict, new: str) -> str:
    find = entry["find_value"]
    flags = re.IGNORECASE if _truthy(entry.get("ignore_case")) else 0
    if _truthy(entry.get("is_regex")):
        rx = re.compile(find, flags)
        m = rx.search(text)
        if not m:
            return text
        return text.replace(m.group(1), new)
    if flags:
        return re.sub(re.escape(find), new, text, flags=flags)
    return text.replace(find, new)


_KV = re.compile(r'\$\.properties\.activities\[\?\(@\.name=="([^"]+)"\)\]\.typeProperties\.(\w+)$')


def apply_key_value(doc: dict, find_key: str, new: str) -> dict:
    m = _KV.match(find_key)
    if not m:
        raise SystemExit(f"[ERROR] render.py only supports activity typeProperties keys, got {find_key}")
    name, key = m.group(1), m.group(2)
    for act in doc.get("properties", {}).get("activities", []):
        if act.get("name") == name and key in act.get("typeProperties", {}):
            act["typeProperties"][key] = new
    return doc


def render(workspace: Path, env: str, targets: dict, out: Path) -> list[str]:
    """Render workspace for env into out. Returns a log of applied replacements."""
    params = yaml.safe_load((workspace / "parameter.yml").read_text()) or {}
    if out.exists():
        shutil.rmtree(out)
    # parameter.yml is configuration for the release, not an item: it is never published.
    shutil.copytree(workspace, out, ignore=shutil.ignore_patterns("parameter.yml"))
    log: list[str] = []
    for item in load_items(out):
        for f in item["files"]:
            rel = "/" + f.relative_to(out).as_posix()
            text = f.read_text()
            orig = text
            for entry in params.get("find_replace", []) or []:
                val = env_value(entry.get("replace_value", {}), env)
                if val is None or not filters_match(entry, item, rel):
                    continue
                new = resolve_value(val, env, targets)
                after = apply_find_replace(text, entry, new)
                if after != text:
                    log.append(f"find_replace {entry['find_value']} -> {new} in {rel}")
                text = after
            kv = params.get("key_value_replace", []) or []
            if kv and f.suffix == ".json":
                doc = json.loads(text)
                for entry in kv:
                    val = env_value(entry.get("replace_value", {}), env)
                    if val is None or not filters_match(entry, item, rel):
                        continue
                    new = resolve_value(val, env, targets)
                    doc = apply_key_value(doc, entry["find_key"], new)
                dumped = json.dumps(doc, indent=2) + "\n"
                if json.loads(dumped) != json.loads(text):
                    log.append(f"key_value_replace in {rel}")
                    text = dumped
            if text != orig:
                f.write_text(text)
    return log


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", required=True)
    ap.add_argument("--workspace", default="workspace")
    ap.add_argument("--targets", default="deploy/targets.json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    targets = json.loads(Path(a.targets).read_text())
    log = render(Path(a.workspace), a.env, targets, Path(a.out))
    for line in log:
        print(line)
    print(f"rendered {a.workspace} for {a.env} into {a.out} ({len(log)} replacements)")


if __name__ == "__main__":
    main()
