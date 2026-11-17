"""Helpers for the connector tests: load the two files and resolve local $refs."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SWAGGER = ROOT / "connector" / "apiDefinition.swagger.json"
PROPS = ROOT / "connector" / "apiProperties.json"
METHODS = ("get", "put", "post", "patch", "delete", "head", "options")


def load_swagger() -> dict:
    return json.loads(SWAGGER.read_text())


def load_props() -> dict:
    return json.loads(PROPS.read_text())


def resolve(spec: dict, node):
    """Follow a local '#/a/b' $ref (repeatedly)."""
    while isinstance(node, dict) and "$ref" in node:
        parts = node["$ref"].lstrip("#/").split("/")
        cur = spec
        for p in parts:
            cur = cur[p]
        node = cur
    return node


def operations(spec: dict):
    """Yield (path, method, operation) for every operation."""
    for path, item in spec.get("paths", {}).items():
        for m in METHODS:
            if m in item:
                yield path, m, item[m]


def op_by_id(spec: dict, op_id: str):
    for path, m, op in operations(spec):
        if op.get("operationId") == op_id:
            return path, m, op
    return None


def params(spec: dict, op: dict, path_item: dict | None = None) -> list[dict]:
    out = [resolve(spec, p) for p in (path_item or {}).get("parameters", [])]
    out += [resolve(spec, p) for p in op.get("parameters", [])]
    return out


def walk_properties(spec: dict, schema, seen=None):
    """Yield (name, property_schema) for every property reachable from schema."""
    seen = seen or set()
    schema = resolve(spec, schema) if isinstance(schema, dict) else schema
    if not isinstance(schema, dict) or id(schema) in seen:
        return
    seen.add(id(schema))
    for name, prop in (schema.get("properties") or {}).items():
        rp = resolve(spec, prop)
        yield name, rp
        yield from walk_properties(spec, rp, seen)
    if "items" in schema:
        yield from walk_properties(spec, schema["items"], seen)


def get_path(schema_props_root: dict, spec: dict, path_string: str):
    """Follow a connector 'path string' (a/b/c) through a schema's properties."""
    node = resolve(spec, schema_props_root)
    for part in path_string.split("/"):
        node = resolve(spec, node)
        if node.get("type") == "array":
            node = resolve(spec, node.get("items", {}))
        node = (node.get("properties") or {}).get(part)
        if node is None:
            return None
    return resolve(spec, node)
