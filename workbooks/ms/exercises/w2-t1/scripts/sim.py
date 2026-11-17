"""Local stand-in for Eventhouse JSON ingestion with an ingestion mapping.

Applies a Kusto JSON ingestion mapping (Column / DataType / Properties.Path /
Properties.Transform / Properties.ConstValue) to JSON events the way queued
or streaming ingestion would: a path that does not exist yields null (it is
NOT an ingestion failure), and values are converted to the column type.

Supported JSONPath subset: $, $.a.b, $['a b'], $.a[0].

Usage:
  python scripts/sim.py replay <events.jsonl> [mapping.json]
"""

import datetime as dt
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SCHEMA = HERE / "eventhouse" / "schema.kql"
MAPPING = HERE / "eventhouse" / "mappings" / "TelemetryLanding_mapping.json"

TRANSFORMS = {
    "DateTimeFromUnixSeconds": 1,
    "DateTimeFromUnixMilliseconds": 1_000,
    "DateTimeFromUnixMicroseconds": 1_000_000,
    "DateTimeFromUnixNanoseconds": 1_000_000_000,
}
OTHER_TRANSFORMS = {"PropertyBagArrayToDictionary", "SourceLocation", "SourceLineNumber",
                    "DropMappedFields", "BytesAsBase64"}
EPOCH = dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)


def load_schema(path=SCHEMA):
    text = re.sub(r"//[^\n]*", "", Path(path).read_text())
    tables = {}
    for m in re.finditer(r"\.create(?:-merge)?\s+table\s+(\w+)\s*\(([^)]*)\)", text):
        cols = []
        for part in m.group(2).split(","):
            name, typ = (x.strip() for x in part.split(":"))
            cols.append((name, typ.lower()))
        tables[m.group(1)] = cols
    return tables


def parse_path(path):
    if path == "$":
        return []
    if not path.startswith("$"):
        raise ValueError(f"path must start with $: {path!r}")
    rest, parts = path[1:], []
    tok = re.compile(r"\.([A-Za-z_][\w]*)|\[\s*'((?:[^'\\]|\\.)*)'\s*\]|\[\s*(\d+)\s*\]")
    pos = 0
    while pos < len(rest):
        m = tok.match(rest, pos)
        if not m:
            raise ValueError(f"unsupported JSONPath syntax at {rest[pos:]!r} in {path!r}")
        if m.group(1) is not None:
            parts.append(m.group(1))
        elif m.group(2) is not None:
            parts.append(m.group(2).replace("\\'", "'"))
        else:
            parts.append(int(m.group(3)))
        pos = m.end()
    return parts


def resolve(doc, parts):
    cur = doc
    for p in parts:
        if isinstance(p, int):
            if not isinstance(cur, list) or p >= len(cur):
                return None
            cur = cur[p]
        else:
            if not isinstance(cur, dict) or p not in cur:
                return None
            cur = cur[p]
    return cur


def parse_datetime(v):
    if not isinstance(v, str):
        return None
    s = v.strip().replace("Z", "+00:00")
    try:
        d = dt.datetime.fromisoformat(s)
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc)


def convert(value, typ):
    if value is None:
        return None
    if typ == "string":
        return value if isinstance(value, str) else json.dumps(value)
    if typ in ("real", "double", "decimal"):
        if isinstance(value, bool):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    if typ in ("int", "long"):
        if isinstance(value, bool):
            return None
        try:
            f = float(value)
        except (TypeError, ValueError):
            return None
        return int(f) if f == int(f) else None
    if typ == "bool":
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.lower() in ("true", "false"):
            return value.lower() == "true"
        return None
    if typ == "datetime":
        if isinstance(value, dt.datetime):
            return value
        return parse_datetime(value)
    if typ == "dynamic":
        return value
    return None


def apply_transform(value, transform):
    if transform in TRANSFORMS:
        if isinstance(value, bool) or not isinstance(value, (int, float, str)):
            return None
        try:
            n = float(value)
        except ValueError:
            return None
        div = TRANSFORMS[transform]
        whole, frac = divmod(int(n), div)
        return EPOCH + dt.timedelta(seconds=whole, microseconds=frac * 1_000_000 // div)
    if transform in OTHER_TRANSFORMS:
        return value
    raise ValueError(f"unknown transform {transform!r}")


def validate_mapping(mapping, columns):
    """Return a list of problems with the mapping itself (shape, names, types)."""
    problems = []
    if not isinstance(mapping, list) or not mapping:
        return ["mapping must be a non-empty JSON array"]
    types = dict(columns)
    seen = []
    for i, el in enumerate(mapping):
        if not isinstance(el, dict) or "Column" not in el:
            problems.append(f"element {i}: needs a Column")
            continue
        col = el["Column"]
        seen.append(col)
        if col not in types:
            problems.append(f"{col}: not a column of the table")
        if "DataType" in el and types.get(col) and el["DataType"].lower() != types[col]:
            problems.append(f"{col}: DataType {el['DataType']} does not match table type {types[col]}")
        props = el.get("Properties")
        if not isinstance(props, dict):
            problems.append(f"{col}: needs a Properties object")
            continue
        unknown = set(props) - {"Path", "ConstValue", "Transform"}
        if unknown:
            problems.append(f"{col}: unknown properties {sorted(unknown)}")
        if "Path" not in props and "ConstValue" not in props and "Transform" not in props:
            problems.append(f"{col}: needs Path, ConstValue or Transform")
        if "Path" in props:
            try:
                parse_path(props["Path"])
            except ValueError as exc:
                problems.append(f"{col}: {exc}")
        t = props.get("Transform")
        if t is not None and t not in TRANSFORMS and t not in OTHER_TRANSFORMS:
            problems.append(f"{col}: unknown transform {t!r}")
    dups = sorted({c for c in seen if seen.count(c) > 1})
    if dups:
        problems.append(f"columns mapped more than once: {dups}")
    return problems


def apply_mapping(event, mapping, columns):
    types = dict(columns)
    row = {c: None for c, _ in columns}
    for el in mapping:
        col = el["Column"]
        props = el.get("Properties", {})
        if "ConstValue" in props:
            raw = props["ConstValue"]
        elif "Path" in props:
            raw = resolve(event, parse_path(props["Path"]))
        else:
            raw = None
        if props.get("Transform"):
            raw = apply_transform(raw, props["Transform"])
        row[col] = convert(raw, types.get(col, "string"))
    return row


def fmt(v):
    if v is None:
        return "null"
    if isinstance(v, dt.datetime):
        return v.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    return str(v)


def table(rows, columns):
    names = [c for c, _ in columns]
    cells = [[fmt(r[n]) for n in names] for r in rows]
    widths = [max([len(n)] + [len(c[i]) for c in cells]) for i, n in enumerate(names)]
    lines = [" | ".join(n.ljust(w) for n, w in zip(names, widths)),
             "-+-".join("-" * w for w in widths)]
    lines += [" | ".join(c.ljust(w) for c, w in zip(cell, widths)) for cell in cells]
    return "\n".join(lines)


def main(argv):
    if len(argv) < 3 or argv[1] != "replay":
        print(__doc__)
        return 2
    events = [json.loads(line) for line in Path(argv[2]).read_text().splitlines() if line.strip()]
    mapping = json.loads(Path(argv[3] if len(argv) > 3 else MAPPING).read_text())
    cols = load_schema()["TelemetryLanding"]
    problems = validate_mapping(mapping, cols)
    for p in problems:
        print("MAPPING PROBLEM:", p)
    rows = [apply_mapping(e, mapping, cols) for e in events]
    print(table(rows, cols))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
