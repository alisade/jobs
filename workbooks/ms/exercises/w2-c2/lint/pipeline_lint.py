"""Generic structural linter for Fabric Data pipeline JSON (pipeline-content.json).

Checks what the Fabric designer would reject or what fails at run time:
activity types, unique names, dependsOn targets and conditions, cycles,
policy formats, expression references (parameters, variables, activity
outputs, item()), and Set variable inside a parallel ForEach.

Usage: python lint/pipeline_lint.py pl_nightly_orchestrator.DataPipeline/pipeline-content.json
"""

import json
import re
import sys

KNOWN_TYPES = {
    "TridentNotebook", "WebActivity", "SetVariable", "AppendVariable", "Wait", "Until",
    "IfCondition", "ForEach", "Switch", "Fail", "InvokePipeline", "ExecutePipeline",
    "Copy", "Lookup", "GetMetadata", "Script", "SqlServerStoredProcedure", "Filter",
    "RefreshDataflow", "Office365Outlook", "Teams",
}
CONTAINERS = {"Until": ["activities"], "ForEach": ["activities"],
              "IfCondition": ["ifTrueActivities", "ifFalseActivities"]}
NO_RETRY_TYPES = {"SetVariable", "AppendVariable", "Wait", "Until", "IfCondition", "ForEach", "Fail", "Switch", "Filter"}
CONDITIONS = {"Succeeded", "Failed", "Skipped", "Completed"}
TIMEOUT_RE = re.compile(r"^(\d+)\.(\d{2}):(\d{2}):(\d{2})$")


def timeout_seconds(value):
    if not isinstance(value, str):
        return None
    m = TIMEOUT_RE.match(value)
    if not m:
        return None
    d, h, mi, s = (int(x) for x in m.groups())
    if h > 23 or mi > 59 or s > 59:
        return None
    return ((d * 24 + h) * 60 + mi) * 60 + s


def load(path):
    with open(path) as f:
        return json.load(f)


def expr_text(v):
    """Return the expression string if v is an expression, else None."""
    if isinstance(v, dict) and v.get("type") == "Expression" and isinstance(v.get("value"), str):
        return v["value"]
    if isinstance(v, str) and v.startswith("@") and not v.startswith("@@"):
        return v
    return None


def walk_values(obj):
    if isinstance(obj, dict):
        e = expr_text(obj)
        if e is not None:
            yield e
            return
        for v in obj.values():
            yield from walk_values(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_values(v)
    else:
        e = expr_text(obj)
        if e is not None:
            yield e


def own_props(act):
    """typeProperties without nested activity lists (those are their own scopes)."""
    tp = dict(act.get("typeProperties") or {})
    for key in CONTAINERS.get(act.get("type"), []):
        tp.pop(key, None)
    return tp


def all_activities(acts, path=()):
    """Yield (activity, path of enclosing container activities)."""
    for a in acts:
        yield a, path
        for key in CONTAINERS.get(a.get("type"), []):
            inner = (a.get("typeProperties") or {}).get(key) or []
            yield from all_activities(inner, path + (a,))


def upstream(acts, name):
    deps = {a["name"]: [d.get("activity") for d in a.get("dependsOn", [])] for a in acts if "name" in a}
    seen, stack = set(), list(deps.get(name, []))
    while stack:
        n = stack.pop()
        if n in seen or n not in deps:
            continue
        seen.add(n)
        stack.extend(deps[n])
    return seen


def find_cycle(acts):
    deps = {a["name"]: [d.get("activity") for d in a.get("dependsOn", [])] for a in acts if "name" in a}
    state = {}

    def visit(n):
        state[n] = 1
        for m in deps.get(n, []):
            if m not in deps:
                continue
            if state.get(m) == 1:
                return True
            if m not in state and visit(m):
                return True
        state[n] = 2
        return False

    return any(visit(n) for n in deps if n not in state)


def lint(doc):
    errors = []
    props = doc.get("properties")
    if not isinstance(props, dict):
        return ["top-level 'properties' object missing"]
    acts = props.get("activities")
    if not isinstance(acts, list) or not acts:
        return ["properties.activities must be a non-empty list"]
    params = props.get("parameters") or {}
    variables = props.get("variables") or {}
    for pname, p in params.items():
        if not isinstance(p, dict) or p.get("type") not in ("String", "Int", "Float", "Bool", "Array", "Object", "SecureString"):
            errors.append(f"parameter {pname}: type must be String/Int/Float/Bool/Array/Object/SecureString")
    for vname, v in variables.items():
        if not isinstance(v, dict) or v.get("type") not in ("String", "Boolean", "Array", "Integer"):
            errors.append(f"variable {vname}: type must be String/Boolean/Array/Integer")

    names = []
    scopes = [(acts, ())]
    for a, path in all_activities(acts):
        if not a.get("name"):
            errors.append("activity without a name")
            continue
        names.append(a["name"])
        if a.get("type") not in KNOWN_TYPES:
            errors.append(f"{a['name']}: unknown activity type {a.get('type')!r}")
        for key in CONTAINERS.get(a.get("type"), []):
            inner = (a.get("typeProperties") or {}).get(key)
            if inner:
                scopes.append((inner, path + (a,)))
    dup = sorted({n for n in names if names.count(n) > 1})
    if dup:
        errors.append(f"activity names must be unique across the pipeline: {dup}")

    for scope, _ in scopes:
        local = {a.get("name") for a in scope}
        for a in scope:
            for d in a.get("dependsOn", []):
                tgt = d.get("activity")
                if tgt not in local:
                    errors.append(f"{a.get('name')}: dependsOn {tgt!r} is not in the same scope")
                if tgt == a.get("name"):
                    errors.append(f"{a.get('name')}: depends on itself")
                conds = d.get("dependencyConditions") or []
                if not conds or not set(conds) <= CONDITIONS:
                    errors.append(f"{a.get('name')}: dependencyConditions must be a non-empty subset of {sorted(CONDITIONS)}")
        if find_cycle(scope):
            errors.append("dependency cycle in scope " + ", ".join(sorted(x for x in local if x)))

    for a, path in all_activities(acts):
        name, typ = a.get("name"), a.get("type")
        pol = a.get("policy") or {}
        if "timeout" in pol and timeout_seconds(pol["timeout"]) is None:
            errors.append(f"{name}: policy.timeout must be D.HH:MM:SS, got {pol['timeout']!r}")
        if "retry" in pol and (not isinstance(pol["retry"], int) or pol["retry"] < 0):
            errors.append(f"{name}: policy.retry must be a non-negative integer")
        if "retryIntervalInSeconds" in pol:
            r = pol["retryIntervalInSeconds"]
            if not isinstance(r, int) or not 30 <= r <= 86400:
                errors.append(f"{name}: retryIntervalInSeconds must be an integer 30-86400")
        if typ in NO_RETRY_TYPES and pol.get("retry", 0):
            errors.append(f"{name}: {typ} is a control activity; retry policy makes no sense there")

        tp = a.get("typeProperties") or {}
        if typ == "Until":
            if timeout_seconds(tp.get("timeout")) is None:
                errors.append(f"{name}: Until needs typeProperties.timeout (D.HH:MM:SS)")
            if expr_text(tp.get("expression")) is None:
                errors.append(f"{name}: Until needs an expression {{value, type: Expression}}")
            if not tp.get("activities"):
                errors.append(f"{name}: Until has no inner activities")
        if typ == "ForEach":
            if expr_text(tp.get("items")) is None:
                errors.append(f"{name}: ForEach items must be an expression")
            if not tp.get("isSequential", False):
                bc = tp.get("batchCount", 20)
                if not isinstance(bc, int) or not 1 <= bc <= 50:
                    errors.append(f"{name}: batchCount must be 1-50")
            for inner, _ in all_activities(tp.get("activities") or []):
                if inner.get("type") == "SetVariable" and not tp.get("isSequential", False):
                    errors.append(f"{inner.get('name')}: Set variable inside a parallel ForEach races (variables are pipeline-scoped)")
        if typ == "IfCondition" and expr_text(tp.get("expression")) is None:
            errors.append(f"{name}: IfCondition needs an expression")
        if typ in ("SetVariable", "AppendVariable"):
            if tp.get("variableName") not in variables:
                errors.append(f"{name}: variable {tp.get('variableName')!r} is not declared")
        if typ == "Fail":
            if not tp.get("message") or not tp.get("errorCode"):
                errors.append(f"{name}: Fail needs message and errorCode")
        if typ == "Wait" and not isinstance(tp.get("waitTimeInSeconds"), (int, dict)):
            errors.append(f"{name}: Wait needs waitTimeInSeconds")

        # expression references
        in_foreach = any(p.get("type") == "ForEach" for p in path)
        scope = (path[-1].get("typeProperties") or {}) if path else props
        scope_acts = None
        if path:
            for key in CONTAINERS[path[-1]["type"]]:
                lst = scope.get(key) or []
                if a in lst:
                    scope_acts = lst
        else:
            scope_acts = acts
        allowed = upstream(scope_acts or [], name)
        for i, cont in enumerate(path):
            parent_scope = acts if i == 0 else None
            if i > 0:
                ptp = path[i - 1].get("typeProperties") or {}
                for key in CONTAINERS[path[i - 1]["type"]]:
                    if cont in (ptp.get(key) or []):
                        parent_scope = ptp.get(key)
            allowed |= upstream(parent_scope or [], cont["name"])
        exprs = list(walk_values(own_props(a)))
        own_inner = set()
        if typ == "Until":
            own_inner = {x.get("name") for x in tp.get("activities") or []}
        for e in exprs:
            for p in re.findall(r"pipeline\(\)\.parameters\.(\w+)", e):
                if p not in params:
                    errors.append(f"{name}: parameter {p!r} not declared")
            for v in re.findall(r"variables\(\s*'([^']+)'\s*\)", e):
                if v not in variables:
                    errors.append(f"{name}: variable {v!r} not declared")
            for r in re.findall(r"activity\(\s*'([^']+)'\s*\)", e):
                if r not in allowed and r not in own_inner:
                    errors.append(f"{name}: references activity('{r}') which is not upstream of it")
            if re.search(r"\bitem\(\)", e) and not in_foreach:
                errors.append(f"{name}: item() used outside a ForEach")
    return errors


def main(argv):
    path = argv[1] if len(argv) > 1 else "pl_nightly_orchestrator.DataPipeline/pipeline-content.json"
    try:
        doc = load(path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read {path}: {exc}")
        return 1
    errs = lint(doc)
    for e in errs:
        print("ERROR", e)
    print(f"{len(errs)} error(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
