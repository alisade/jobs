from __future__ import annotations

import json
import re
from typing import Any, Callable

import yaml

VAR = re.compile(r"\{\{\s*([\w:.\-]+)\s*\}\}")


class ParameterError(ValueError):
    pass


class StepFailed(Exception):
    pass


class FakeAws:
    """Registry of fake API handlers keyed by (Service, Api). Records every call in ``calls``."""

    def __init__(self):
        self.handlers: dict[tuple[str, str], Callable[[dict], dict]] = {}
        self.calls: list[tuple[str, str, dict]] = []

    def register(self, service: str, api: str, fn: Callable[[dict], dict]) -> None:
        self.handlers[(service, api)] = fn

    def call(self, service: str, api: str, params: dict) -> dict:
        self.calls.append((service, api, params))
        key = (service, api)
        if key not in self.handlers:
            raise StepFailed(f"no fake for {service}.{api}")
        return self.handlers[key](params)


def select(doc: Any, selector: str) -> Any:
    if not selector.startswith("$"):
        raise StepFailed(f"selector must start with $: {selector}")
    cur = doc
    for part in re.findall(r"\.([\w\-]+)|\[(\d+)\]", selector[1:]):
        key, idx = part
        try:
            cur = cur[int(idx)] if idx else cur[key]
        except (KeyError, IndexError, TypeError) as e:
            raise StepFailed(f"selector {selector} found nothing") from e
    return cur


def _cast(value: Any, typ: str) -> Any:
    if typ == "Integer":
        return int(value)
    if typ == "Boolean":
        return str(value).lower() == "true"
    if typ in ("StringList", "MapList"):
        return value
    return str(value) if not isinstance(value, (dict, list)) else json.dumps(value)


def _substitute(value: Any, scope: dict) -> Any:
    if isinstance(value, str):
        whole = VAR.fullmatch(value.strip())
        if whole:
            key = whole.group(1)
            if key not in scope:
                raise StepFailed(f"unknown variable {key}")
            return scope[key]

        def repl(m):
            if m.group(1) not in scope:
                raise StepFailed(f"unknown variable {m.group(1)}")
            v = scope[m.group(1)]
            return v if isinstance(v, str) else json.dumps(v)
        return VAR.sub(repl, value)
    if isinstance(value, list):
        return [_substitute(v, scope) for v in value]
    if isinstance(value, dict):
        return {k: _substitute(v, scope) for k, v in value.items()}
    return value


def _params(doc: dict, given: dict) -> dict:
    out = {}
    for name, spec in (doc.get("parameters") or {}).items():
        if name in given:
            v = given[name]
        elif "default" in spec:
            v = spec["default"]
        else:
            raise ParameterError(f"missing required parameter {name}")
        typ = spec.get("type", "String")
        try:
            v = _cast(v, typ)
        except (TypeError, ValueError) as e:
            raise ParameterError(f"{name}: expected {typ}") from e
        if "allowedPattern" in spec and not re.fullmatch(spec["allowedPattern"], str(v)):
            raise ParameterError(f"{name}={v!r} does not match {spec['allowedPattern']}")
        if "allowedValues" in spec and v not in spec["allowedValues"]:
            raise ParameterError(f"{name}={v!r} not in {spec['allowedValues']}")
        out[name] = v
    unknown = set(given) - set(out)
    if unknown:
        raise ParameterError(f"unknown parameters {sorted(unknown)}")
    return out


def _branch(inputs: dict, scope: dict) -> str | None:
    for ch in inputs.get("Choices", []):
        var = _substitute(ch["Variable"], scope)
        for op, want in ch.items():
            if op in ("NextStep", "Variable"):
                continue
            want = _substitute(want, scope)
            ok = {
                "StringEquals": lambda: str(var) == str(want),
                "NumericEquals": lambda: float(var) == float(want),
                "NumericGreater": lambda: float(var) > float(want),
                "NumericGreaterOrEquals": lambda: float(var) >= float(want),
                "NumericLesser": lambda: float(var) < float(want),
                "BooleanEquals": lambda: bool(var) == bool(want),
            }.get(op)
            if ok is None:
                raise StepFailed(f"unsupported branch operator {op}")
            if ok():
                return ch["NextStep"]
    return inputs.get("Default")


def run(doc_text: str, params: dict, aws: FakeAws, approve: Callable[[dict], bool] = lambda i: True,
        execution_id: str = "exec-0001", clock_step: int = 10) -> dict:
    """Execute a runbook. Returns {status, executed, failed_step, error, outputs, assume_role}."""
    doc = yaml.safe_load(doc_text)
    if str(doc.get("schemaVersion")) != "0.3":
        raise ParameterError("Automation runbooks use schemaVersion '0.3'")
    p = _params(doc, params)
    scope: dict[str, Any] = {**p, "automation:EXECUTION_ID": execution_id}
    steps = doc["mainSteps"]
    index = {s["name"]: i for i, s in enumerate(steps)}
    executed: list[str] = []
    i = 0
    result = {"status": "Success", "executed": executed, "failed_step": None, "error": None,
              "assume_role": _substitute(doc.get("assumeRole"), scope) if doc.get("assumeRole") else None}
    guard = 0
    while i < len(steps):
        guard += 1
        if guard > 200:
            raise StepFailed("runbook loops")
        step = steps[i]
        name, action = step["name"], step["action"]
        executed.append(name)
        nxt: str | None = step.get("nextStep")
        try:
            inputs = _substitute(step.get("inputs") or {}, scope)
            resp: Any = None
            if action == "aws:executeAwsApi":
                svc, api = inputs.pop("Service"), inputs.pop("Api")
                resp = aws.call(svc, api, inputs)
            elif action == "aws:approve":
                if not inputs.get("Approvers"):
                    raise StepFailed("aws:approve needs Approvers")
                if not approve(inputs):
                    raise StepFailed("approval rejected")
                resp = {"ApprovalStatus": "Approved"}
            elif action == "aws:branch":
                nxt = _branch(inputs, scope)
                if nxt is None:
                    raise StepFailed("no branch matched and no Default")
            elif action == "aws:waitForAwsResourceProperty":
                svc, api = inputs.pop("Service"), inputs.pop("Api")
                sel, desired = inputs.pop("PropertySelector"), [str(x) for x in inputs.pop("DesiredValues")]
                timeout = int(step.get("timeoutSeconds", 3600))
                waited = 0
                while True:
                    resp = aws.call(svc, api, dict(inputs))
                    if str(select(resp, sel)) in desired:
                        break
                    waited += clock_step
                    if waited > timeout:
                        raise StepFailed(f"timed out after {timeout}s waiting for {sel} in {desired}")
            elif action == "aws:executeScript":
                ns: dict[str, Any] = {}
                exec(compile(inputs["Script"], f"<{name}>", "exec"), ns)  # noqa: S102
                handler = ns[inputs["Handler"]]
                resp = {"Payload": handler(inputs.get("InputPayload", {}), None)}
            elif action == "aws:sleep":
                resp = {}
            else:
                raise StepFailed(f"unsupported action {action}")
            for o in step.get("outputs") or []:
                scope[f"{name}.{o['Name']}"] = _cast(select(resp, o["Selector"]), o.get("Type", "String"))
        except Exception as e:  # noqa: BLE001
            on_fail = step.get("onFailure", "Abort")
            if on_fail.startswith("step:"):
                result["error"] = f"{name}: {e}"
                i = index[on_fail[5:]]
                continue
            result.update(status="Failed", failed_step=name, error=f"{name}: {e}")
            break
        if step.get("isEnd"):
            break
        if nxt:
            if nxt not in index:
                raise StepFailed(f"{name}: nextStep {nxt} does not exist")
            i = index[nxt]
        else:
            i += 1
    result["outputs"] = {k: scope.get(k) for k in doc.get("outputs") or []}
    return result
