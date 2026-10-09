"""Dry-run simulator for a Fabric Data pipeline definition (pipeline-content.json).

It is NOT Fabric. It walks the activity graph the way the pipeline engine does, evaluates the
pipeline expression language for the subset used by this pipeline, and fakes the data-plane:

- Lookup against etl.load_control reads warehouse/WH_Control/etl/load_control_seed.csv, applies the
  WHERE clause filters for source_system and is_enabled, and returns only the SELECTed columns.
  Output shape follows the documented Lookup contract: firstRowOnly true (the default) returns
  {"firstRow": {...}}, false returns {"count": n, "value": [...]}.
- Copy, Script and Fail activities evaluate their expressions and return canned outputs.

Usage: python tools/simulate_run.py <pipeline-content.json> [--out run.json] [--run-id ID]
Exit code 0 when the simulated pipeline run Succeeded, 1 when it Failed.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEED = os.path.join(ROOT, "warehouse", "WH_Control", "etl", "load_control_seed.csv")
RUNTIME_PROPS = {
    "effectiveIntegrationRuntime": "WorkspaceIR (East US)",
    "billingReference": {"activityType": "PipelineActivity", "billableDuration": []},
    "durationInQueue": {"integrationRuntimeQueue": 0},
}


class ExprError(Exception):
    def __init__(self, message: str, code: str = "InvalidTemplate"):
        super().__init__(message)
        self.code = code


# ------------------------------------------------------------------ expression language
TOKEN = re.compile(r"\s*(?:(?P<str>'(?:[^']|'')*')|(?P<num>-?\d+(?:\.\d+)?)|(?P<name>[A-Za-z_][A-Za-z0-9_]*)|(?P<op>\?\.|[().,\[\]]))")


def _tokenize(text: str) -> list[tuple[str, str]]:
    pos, out = 0, []
    text = text.strip()
    while pos < len(text):
        m = TOKEN.match(text, pos)
        if not m or m.end() == pos:
            raise ExprError(f"The expression '{text}' is not valid: unexpected character at position {pos}.")
        kind = m.lastgroup
        out.append((kind, m.group(kind)))
        pos = m.end()
    return out


class _Parser:
    def __init__(self, text: str, ctx: dict):
        self.text, self.ctx = text.strip(), ctx
        self.toks = _tokenize(text)
        self.i = 0

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else (None, None)

    def take(self, value=None):
        tok = self.peek()
        if value is not None and tok[1] != value:
            raise ExprError(f"The expression '{self.text}' is not valid: expected '{value}'.")
        self.i += 1
        return tok

    def parse(self):
        v = self.expr()
        if self.i != len(self.toks):
            raise ExprError(f"The expression '{self.text}' is not valid: trailing tokens.")
        return v

    def expr(self):
        v = self.primary()
        while True:
            kind, val = self.peek()
            if val in (".", "?."):
                self.take()
                _, prop = self.take()
                v = self.select(v, prop, optional=(val == "?."))
            elif val == "[":
                self.take()
                key = self.expr()
                self.take("]")
                v = self.select(v, key)
            else:
                return v

    def select(self, obj, prop, optional=False):
        if obj is None:
            if optional:
                return None
            raise ExprError(
                f"The expression '{self.text}' cannot be evaluated because property '{prop}' cannot be selected."
            )
        if isinstance(obj, list):
            if isinstance(prop, (int, float)) and 0 <= int(prop) < len(obj):
                return obj[int(prop)]
            raise ExprError(
                f"The expression '{self.text}' cannot be evaluated because property '{prop}' cannot be "
                "selected. Array elements can only be selected using an integer index."
            )
        if isinstance(obj, dict):
            if prop in obj:
                return obj[prop]
            if optional:
                return None
            avail = ", ".join(obj.keys())
            raise ExprError(
                f"The expression '{self.text}' cannot be evaluated because property '{prop}' doesn't "
                f"exist, available properties are '{avail}'."
            )
        raise ExprError(f"The expression '{self.text}' cannot be evaluated because property '{prop}' cannot be selected.")

    def primary(self):
        kind, val = self.take()
        if kind == "str":
            return val[1:-1].replace("''", "'")
        if kind == "num":
            return float(val) if "." in val else int(val)
        if kind == "name":
            if val in ("true", "false"):
                return val == "true"
            if val == "null":
                return None
            self.take("(")
            args = []
            if self.peek()[1] != ")":
                args.append(self.expr())
                while self.peek()[1] == ",":
                    self.take()
                    args.append(self.expr())
            self.take(")")
            return self.call(val, args)
        raise ExprError(f"The expression '{self.text}' is not valid.")

    def call(self, fn, args):
        c = self.ctx
        if fn == "activity":
            name = args[0]
            if name not in c["outputs"]:
                raise ExprError(
                    f"The template validation failed: 'The action '{name}' referenced by 'inputs' in "
                    f"the action '{c['current']}' is not defined in the template or has not run.'"
                )
            return c["outputs"][name]
        if fn == "item":
            if "item" not in c:
                raise ExprError(f"The expression '{self.text}' is not valid: item() used outside a ForEach.")
            return c["item"]
        if fn == "pipeline":
            return c["pipeline"]
        if fn == "variables":
            return c["variables"].get(args[0])
        if fn == "concat":
            if args and all(isinstance(a, list) for a in args):
                return [x for a in args for x in a]
            return "".join(_to_str(a) for a in args)
        if fn == "utcnow":
            return c["pipeline"]["TriggerTime"]
        if fn == "formatDateTime":
            ts = dt.datetime.fromisoformat(str(args[0]).replace("Z", "+00:00"))
            fmt = args[1] if len(args) > 1 else "yyyy-MM-ddTHH:mm:ss.fffffffZ"
            for a, b in (("yyyy", "%Y"), ("MM", "%m"), ("dd", "%d"), ("HH", "%H"), ("mm", "%M"), ("ss", "%S")):
                fmt = fmt.replace(a, b)
            return ts.strftime(fmt.replace("fffffff", "0000000").replace("fff", "000"))
        if fn == "string":
            return _to_str(args[0])
        if fn == "int":
            return int(args[0])
        if fn == "length":
            if not isinstance(args[0], (list, str, dict)):
                raise ExprError(f"The function 'length' expects its parameter to be an array or a string. The provided value is of type '{type(args[0]).__name__}'.")
            return len(args[0])
        if fn == "equals":
            return args[0] == args[1]
        if fn in ("greater", "less"):
            return args[0] > args[1] if fn == "greater" else args[0] < args[1]
        if fn == "not":
            return not args[0]
        if fn == "and":
            return all(args)
        if fn == "or":
            return any(args)
        if fn == "if":
            return args[1] if args[0] else args[2]
        if fn == "coalesce":
            return next((a for a in args if a is not None), None)
        if fn in ("toLower", "toUpper"):
            return str(args[0]).lower() if fn == "toLower" else str(args[0]).upper()
        if fn == "replace":
            return str(args[0]).replace(args[1], args[2])
        if fn == "createArray":
            return list(args)
        raise ExprError(f"The template function '{fn}' is not defined or not valid.")


def _to_str(v) -> str:
    if isinstance(v, bool):
        return "True" if v else "False"
    if isinstance(v, (dict, list)):
        return json.dumps(v)
    return "" if v is None else str(v)


def evaluate(value, ctx):
    """Evaluate a property value: {"value": "...", "type": "Expression"} or a plain value."""
    if isinstance(value, dict) and value.get("type") == "Expression":
        return eval_string(value.get("value", ""), ctx)
    if isinstance(value, dict):
        return {k: evaluate(v, ctx) for k, v in value.items()}
    if isinstance(value, list):
        return [evaluate(v, ctx) for v in value]
    return value


def eval_string(s: str, ctx):
    if s.startswith("@") and not s.startswith("@{") and not s.startswith("@@"):
        return _Parser(s[1:], ctx).parse()
    out, i = [], 0
    while i < len(s):
        if s.startswith("@@", i):
            out.append("@")
            i += 2
        elif s.startswith("@{", i):
            j = s.index("}", i)
            out.append(_to_str(_Parser(s[i + 2 : j], ctx).parse()))
            i = j + 1
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


# ------------------------------------------------------------------ data plane fakes
def _load_seed() -> list[dict]:
    with open(SEED, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["load_id"] = int(r["load_id"])
        r["is_enabled"] = r["is_enabled"] == "1"
    return rows


def fake_lookup(query: str, first_row_only: bool) -> dict:
    q = " ".join(query.split())
    m = re.match(r"(?is)select\s+(.*?)\s+from\s+\[?etl\]?\.\[?load_control\]?(.*)$", q)
    if not m:
        raise ExprError("Failure happened on 'Source' side. ErrorCode=SqlInvalidObjectName, Invalid object name in query.", "2100")
    cols_txt, where = m.group(1), m.group(2)
    rows = _load_seed()
    known = list(rows[0].keys())
    if cols_txt.strip() == "*":
        cols = known
    else:
        cols = [c.strip().strip("[]") for c in cols_txt.split(",")]
        bad = [c for c in cols if c not in known]
        if bad:
            raise ExprError(f"Failure happened on 'Source' side. ErrorCode=SqlOperationFailed, Invalid column name '{bad[0]}'.", "2100")
    sm = re.search(r"source_system\s*=\s*'([^']*)'", where)
    if sm:
        rows = [r for r in rows if r["source_system"] == sm.group(1)]
    if re.search(r"is_enabled\s*=\s*1", where):
        rows = [r for r in rows if r["is_enabled"]]
    out_rows = []
    for r in rows:
        o = {c: r[c] for c in cols}
        if "is_enabled" in o:
            o["is_enabled"] = bool(o["is_enabled"])
        out_rows.append(o)
    if first_row_only:
        return {"firstRow": out_rows[0] if out_rows else {}, **RUNTIME_PROPS}
    return {"count": len(out_rows), "value": out_rows, **RUNTIME_PROPS}


# ------------------------------------------------------------------ engine
CONDITIONS = {"Succeeded", "Failed", "Skipped", "Completed"}


class Engine:
    def __init__(self, pipeline: dict, run_id: str, trigger_time: str):
        self.props = pipeline["properties"]
        params = {}
        for k, v in (self.props.get("parameters") or {}).items():
            params[k] = v.get("defaultValue")
        self.pipeline_ctx = {
            "parameters": params,
            "RunId": run_id,
            "TriggerTime": trigger_time,
            "Pipeline": "PL_Nightly_ERP_Load",
            "DataFactory": "ws-northwind-data-prod",
        }
        self.variables = {k: v.get("defaultValue") for k, v in (self.props.get("variables") or {}).items()}
        self.runs: list[dict] = []
        self.clock = dt.datetime.fromisoformat(trigger_time.replace("Z", "+00:00"))

    def ctx(self, outputs, item=None, current=""):
        c = {"outputs": outputs, "pipeline": self.pipeline_ctx, "variables": self.variables, "current": current}
        if item is not None:
            c["item"] = item
        return c

    def run_graph(self, activities, item=None, scope="") -> dict:
        status: dict[str, str] = {}
        outputs: dict[str, dict] = {}
        names = [a["name"] for a in activities]
        pending = list(activities)
        while pending:
            progressed = False
            for a in list(pending):
                deps = a.get("dependsOn") or []
                if any(d["activity"] not in names for d in deps):
                    missing = [d["activity"] for d in deps if d["activity"] not in names][0]
                    raise ExprError(f"Activity '{a['name']}' depends on '{missing}', which is not in the same scope.", "InvalidPipelineDefinition")
                if any(d["activity"] not in status for d in deps):
                    continue
                pending.remove(a)
                progressed = True
                ok = all(self._dep_ok(status[d["activity"]], d.get("dependencyConditions", [])) for d in deps)
                if not ok:
                    status[a["name"]] = "Skipped"
                    self._record(a, "Skipped", {}, None, None, scope, item)
                    continue
                st, out = self.run_activity(a, outputs, item, scope)
                status[a["name"]] = st
                last = self.runs[-1] if self.runs else {}
                outputs[a["name"]] = {"output": out, "status": st, "error": last.get("error")}
            if not progressed:
                raise ExprError("Circular dependency between activities: " + ", ".join(p["name"] for p in pending), "InvalidPipelineDefinition")
        return status

    @staticmethod
    def _dep_ok(st: str, conds: list[str]) -> bool:
        for c in conds:
            if c == "Completed" and st in ("Succeeded", "Failed"):
                return True
            if c == st:
                return True
        return False

    def _record(self, a, st, inp, out, err, scope, item):
        start = self.clock
        dur = {"Lookup": 9_412, "ForEach": 0, "Copy": 61_000, "Script": 2_310, "Fail": 112}.get(a["type"], 1000)
        if st != "Succeeded":
            dur = min(dur, 1_500)
        self.clock += dt.timedelta(milliseconds=dur)
        rec = {
            "activityName": a["name"],
            "activityType": a["type"],
            "activityRunId": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{a['name']}-{scope}-{json.dumps(item, default=str)}")),
            "status": st,
            "activityRunStart": start.isoformat().replace("+00:00", "Z"),
            "durationInMs": dur,
            "input": inp,
            "output": out,
            "error": err or {"errorCode": "", "message": "", "failureType": "", "target": a["name"], "details": ""},
        }
        if scope:
            rec["iterationScope"] = scope
        self.runs.append(rec)

    def run_activity(self, a, outputs, item, scope):
        c = self.ctx(outputs, item, a["name"])
        tp = a.get("typeProperties") or {}
        try:
            if a["type"] == "Lookup":
                query = evaluate(tp["source"].get("sqlReaderQuery", ""), c)
                first = tp.get("firstRowOnly", True)
                out = fake_lookup(query, first)
                self._record(a, "Succeeded", {"source": {"sqlReaderQuery": query}, "firstRowOnly": first}, out, None, scope, item)
                return "Succeeded", out
            if a["type"] == "ForEach":
                items = evaluate(tp.get("items"), c)
                if not isinstance(items, list):
                    raise ExprError(
                        f"The function 'ForEach' expects its 'items' to evaluate to an array; it evaluated to '{type(items).__name__}'."
                    )
                self._record(a, "InProgress", {"itemsCount": len(items), "isSequential": tp.get("isSequential", False), "batchCount": tp.get("batchCount", 20)}, None, None, scope, item)
                rec = self.runs[-1]
                failed = False
                for idx, it in enumerate(items):
                    st = self.run_graph(tp.get("activities", []), item=it, scope=f"{a['name']}[{idx}]")
                    if any(v == "Failed" for v in st.values()):
                        failed = True
                rec["status"] = "Failed" if failed else "Succeeded"
                rec["output"] = {"iterations": len(items)}
                if failed:
                    rec["error"] = {"errorCode": "ActivityFailed", "message": "Activity failed because an inner activity failed", "failureType": "UserError", "target": a["name"], "details": ""}
                return rec["status"], rec["output"]
            if a["type"] == "Copy":
                src = evaluate(tp.get("source", {}), c)
                sink = evaluate(tp.get("sink", {}), c)
                ds = evaluate(tp.get("datasetSettings", {}), c)
                q = src.get("sqlReaderQuery", "")
                m = re.search(r"from\s+\[([^\]]*)\]\.\[([^\]]*)\]", q, re.I)
                if not m or not m.group(1) or not m.group(2):
                    raise ExprError(f"Failure happened on 'Source' side. ErrorCode=SqlInvalidObjectName, Invalid object name in query: {q}", "2200")
                rows = (len(m.group(2)) * 1371) % 50_000 + 120
                out = {"dataRead": rows * 212, "rowsRead": rows, "rowsCopied": rows, "copyDuration": 58, "usedParallelCopies": 4,
                       "sourceQuery": q, "sinkTable": (ds.get("typeProperties") or {}).get("table"), **RUNTIME_PROPS}
                self._record(a, "Succeeded", {"source": src, "sink": sink, "datasetSettings": ds}, out, None, scope, item)
                return "Succeeded", out
            if a["type"] == "Script":
                scripts = evaluate(tp.get("scripts", []), c)
                out = {"resultSetCount": 0, "recordsAffected": 1, "scripts": [s.get("text") for s in scripts], **RUNTIME_PROPS}
                self._record(a, "Succeeded", {"scripts": scripts}, out, None, scope, item)
                return "Succeeded", out
            if a["type"] == "Fail":
                msg = evaluate(tp.get("message", ""), c)
                code = evaluate(tp.get("errorCode", ""), c)
                err = {"errorCode": code, "message": msg, "failureType": "UserError", "target": a["name"], "details": ""}
                self._record(a, "Failed", {"message": msg, "errorCode": code}, {}, err, scope, item)
                return "Failed", {}
            body = evaluate(tp, c)
            self._record(a, "Succeeded", body, {}, None, scope, item)
            return "Succeeded", {}
        except ExprError as e:
            err = {"errorCode": e.code, "message": str(e), "failureType": "UserError", "target": a["name"], "details": ""}
            self._record(a, "Failed", {}, None, err, scope, item)
            return "Failed", {}

    def run(self) -> dict:
        top = self.props.get("activities", [])
        status = self.run_graph(top)
        handled = set()
        for a in top:
            for d in a.get("dependsOn") or []:
                if set(d.get("dependencyConditions", [])) & {"Failed", "Completed"}:
                    handled.add(d["activity"])
        failed = [n for n, s in status.items() if s == "Failed" and (n not in handled or any(
            a["name"] == n and a["type"] == "Fail" for a in top))]
        fail_runs = [r for r in self.runs if r["activityType"] == "Fail" and r["status"] == "Failed"]
        pstatus = "Failed" if failed or fail_runs else "Succeeded"
        msg = ""
        if fail_runs:
            msg = f"Operation on target {fail_runs[0]['activityName']} failed: {fail_runs[0]['error']['message']}"
        elif failed:
            r = next(r for r in self.runs if r["activityName"] == failed[0])
            msg = f"Operation on target {failed[0]} failed: {r['error']['message']}"
        return {
            "runId": self.pipeline_ctx["RunId"],
            "pipelineName": self.pipeline_ctx["Pipeline"],
            "status": pstatus,
            "message": msg,
            "runStart": self.pipeline_ctx["TriggerTime"],
            "invokedBy": {"name": "Nightly 02:00 UTC", "invokedByType": "ScheduleTrigger"},
            "activityRuns": self.runs,
        }


def simulate(pipeline_path: str, run_id: str | None = None, trigger_time: str = "2026-10-13T02:00:00Z") -> dict:
    with open(pipeline_path) as f:
        pipeline = json.load(f)
    run_id = run_id or str(uuid.uuid5(uuid.NAMESPACE_URL, pipeline_path + trigger_time))
    return Engine(pipeline, run_id, trigger_time).run()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pipeline")
    ap.add_argument("--out")
    ap.add_argument("--run-id")
    ap.add_argument("--trigger-time", default="2026-10-13T02:00:00Z")
    args = ap.parse_args()
    result = simulate(args.pipeline, args.run_id, args.trigger_time)
    if args.out:
        with open(args.out, "w") as f:
            json.dump(result, f, indent=2)
    print(f"pipeline run {result['runId']}: {result['status']}")
    for r in result["activityRuns"]:
        scope = f" ({r['iterationScope']})" if "iterationScope" in r else ""
        line = f"  {r['activityType']:<8} {r['activityName']:<18} {r['status']:<10}{scope}"
        if r["status"] == "Failed":
            line += f"  {r['error']['errorCode']}: {r['error']['message'][:200]}"
        print(line)
    return 0 if result["status"] == "Succeeded" else 1


if __name__ == "__main__":
    sys.exit(main())
