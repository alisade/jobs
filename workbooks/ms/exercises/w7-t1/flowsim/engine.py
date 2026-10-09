"""A deliberately small simulator of the Logic Apps / Power Automate run engine.

Provided tooling (you do not need to edit it). It is NOT the real engine: it models just enough
to replay a day of purchase orders through a cloud flow definition:

- actions inside `actions` / Scope `actions`, ordered by `runAfter`; an action runs when every
  predecessor finished with one of its allowed statuses, otherwise it is Skipped;
- statuses Succeeded, Failed, Skipped, TimedOut;
- a scope (and the run) is Failed when any branch ends in Failed (a Skipped tail takes the status
  of its predecessor), matching the documented status evaluation;
- `Terminate` ends the run with its `runStatus`;
- `retryPolicy` on connector actions: default (exponential, 4 retries, 7.5 s steps capped 5-45 s),
  none, fixed (count, interval), exponential (count, interval, minimumInterval, maximumInterval).
  Retries happen on 408, 429 and 5xx. The simulator uses the upper bound of each exponential range
  so results are deterministic;
- expressions are not evaluated. Connector calls are answered by a pluggable `backend`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

STATUSES = {"Succeeded", "Failed", "Skipped", "TimedOut"}
RETRYABLE = {408, 429} | set(range(500, 600))


def iso_seconds(value: str) -> float:
    """Parse the ISO 8601 durations used in retry policies (PnDTnHnMnS)."""
    m = re.fullmatch(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?", value or "")
    if not m or value in ("P", "PT"):
        raise ValueError(f"not an ISO 8601 duration: {value!r}")
    d, h, mi, s = m.groups()
    return int(d or 0) * 86400 + int(h or 0) * 3600 + int(mi or 0) * 60 + float(s or 0)


def retry_delays(policy: dict | None) -> list[float]:
    """Delays (seconds) before each retry for a retryPolicy object."""
    if not policy or policy.get("type", "default").lower() == "default":
        return [min(max(7.5 * 2 ** i, 5.0), 45.0) for i in range(4)]
    kind = policy["type"].lower()
    if kind == "none":
        return []
    count = int(policy.get("count", 0))
    if not 1 <= count <= 90:
        raise ValueError(f"retry count must be 1-90, got {count}")
    interval = iso_seconds(policy["interval"])
    if not 5 <= interval <= 86400:
        raise ValueError("retry interval must be between PT5S and P1D")
    if kind == "fixed":
        return [interval] * count
    if kind == "exponential":
        lo = iso_seconds(policy.get("minimumInterval", "PT5S"))
        hi = iso_seconds(policy.get("maximumInterval", "P1D"))
        return [max(min(interval * 2 ** i, hi), lo) for i in range(count)]
    raise ValueError(f"unknown retry policy type {policy['type']!r}")


@dataclass
class ActionRecord:
    name: str
    scope: str
    status: str
    start: float
    end: float
    attempts: list = field(default_factory=list)  # (time, statusCode, headers, body)
    error: dict | None = None


class Terminated(Exception):
    def __init__(self, status: str, error: dict | None):
        self.status, self.error = status, error


class Run:
    def __init__(self, definition: dict, backend, start_time: float, trigger_body: dict):
        self.d = definition
        self.backend = backend
        self.clock = start_time
        self.trigger_body = trigger_body
        self.records: list[ActionRecord] = []
        self.status = "Running"
        self.error = None

    # -- public --------------------------------------------------------------
    def execute(self) -> "Run":
        try:
            st = self._run_block(self.d.get("actions", {}), "")
            self.status = "Failed" if st == "Failed" else "Succeeded"
        except Terminated as t:
            self.status, self.error = t.status, t.error
        return self

    # -- internals -----------------------------------------------------------
    def _run_block(self, actions: dict, scope: str) -> str:
        done: dict[str, str] = {}
        pending = dict(actions)
        while pending:
            progressed = False
            for name, act in list(pending.items()):
                ra = act.get("runAfter") or {}
                if any(dep not in done for dep in ra):
                    continue
                ok = all(done[dep] in allowed for dep, allowed in ra.items())
                if ok:
                    done[name] = self._run_action(name, act, scope)
                else:
                    done[name] = "Skipped"
                    self.records.append(ActionRecord(name, scope, "Skipped", self.clock, self.clock))
                del pending[name]
                progressed = True
            if not progressed:
                raise ValueError(f"runAfter cycle or dangling reference in scope '{scope or 'root'}': {sorted(pending)}")
        return self._block_status(actions, done)

    @staticmethod
    def _block_status(actions: dict, done: dict) -> str:
        succ = {n: [] for n in actions}
        for n, a in actions.items():
            for dep in (a.get("runAfter") or {}):
                succ[dep].append(n)

        def effective(n, seen=()):
            if done[n] != "Skipped":
                return done[n]
            preds = list((actions[n].get("runAfter") or {}).keys())
            if not preds:
                return "Succeeded"
            sts = [effective(p, seen + (n,)) for p in preds if p not in seen]
            return "Failed" if "Failed" in sts or "TimedOut" in sts else "Succeeded"

        # a tail is an action none of whose successors actually ran
        tails = [n for n in actions if all(done[s] == "Skipped" for s in succ[n])]
        return "Failed" if any(effective(n) in ("Failed", "TimedOut") for n in tails) else "Succeeded"

    def _run_action(self, name: str, act: dict, scope: str) -> str:
        t = act.get("type", "")
        start = self.clock
        if t == "Scope":
            st = self._run_block(act.get("actions", {}), name)
            self.records.append(ActionRecord(name, scope, st, start, self.clock))
            return st
        if t == "Terminate":
            inputs = act.get("inputs", {})
            self.records.append(ActionRecord(name, scope, "Succeeded", start, self.clock))
            raise Terminated(inputs.get("runStatus", "Failed"), inputs.get("runError"))
        if t in ("OpenApiConnection", "ApiConnection", "Http"):
            inputs = act.get("inputs", {})
            delays = retry_delays(inputs.get("retryPolicy"))
            rec = ActionRecord(name, scope, "Running", start, start)
            attempt = 0
            while True:
                self.clock += 0.4
                code, headers, body = self.backend(name, inputs, self.clock, self.trigger_body)
                rec.attempts.append((round(self.clock, 1), code, headers, body))
                if code < 400:
                    rec.status = "Succeeded"
                    break
                if code in RETRYABLE and attempt < len(delays):
                    self.clock += delays[attempt]
                    attempt += 1
                    continue
                rec.status = "Failed"
                rec.error = {"code": headers.get("x-ms-error-code", str(code)), "statusCode": code, "body": body}
                break
            rec.end = self.clock
            self.records.append(rec)
            return rec.status
        # Compose, Query, SetVariable, Condition-free data actions: instant success
        self.clock += 0.05
        self.records.append(ActionRecord(name, scope, "Succeeded", start, self.clock))
        return "Succeeded"


def run_flow(definition: dict, backend, start_time: float, trigger_body: dict) -> Run:
    return Run(definition, backend, start_time, trigger_body).execute()


def validate_graph(actions: dict, scope: str = "") -> list[str]:
    """Static checks: runAfter references, allowed statuses, cycles. Returns problems."""
    problems = []
    for name, act in actions.items():
        for dep, sts in (act.get("runAfter") or {}).items():
            if dep not in actions:
                problems.append(f"{scope or 'root'}/{name}: runAfter '{dep}' is not a sibling action")
            if not sts or not set(sts) <= STATUSES:
                problems.append(f"{scope or 'root'}/{name}: bad runAfter statuses {sts}")
        if act.get("type") == "Scope":
            problems += validate_graph(act.get("actions", {}), name)
    # cycle check
    state = {}

    def visit(n):
        if state.get(n) == 1:
            return True
        if state.get(n) == 2:
            return False
        state[n] = 1
        for dep in (actions.get(n, {}).get("runAfter") or {}):
            if dep in actions and visit(dep):
                return True
        state[n] = 2
        return False

    if any(visit(n) for n in actions):
        problems.append(f"{scope or 'root'}: runAfter cycle")
    return problems
