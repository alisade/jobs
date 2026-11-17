"""A small, deterministic simulator for Copilot Studio topic YAML (code-editor format).

It is NOT Copilot Studio. It executes the subset of node kinds and Power Fx that this exercise
uses, so tests can drive scripted conversations:

  node kinds: SendActivity, Question, ConditionGroup, SetVariable, BeginDialog,
              InvokeFlowAction, EndDialog, EndConversation, CancelAllDialogs
  Power Fx:   literals ("text", numbers, true, false), Topic./Global./System. variables,
              = <> < <= > >=, &&, ||, !, And/Or/Not (infix or function), & (concat),
              IsBlank(x), Blank(), parentheses
  values:     a value starting with "=" is a formula; anything else is a literal

Topic selection is done by the test (the real orchestrator is an LLM); the simulator tracks
System.FallbackCount like the platform: +1 per unrecognized message, reset to 0 when a topic
is recognized.
"""
from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass, field
from typing import Any, Callable

import yaml

SCHEMA = "litware_itdesk"
RESET_FLOW = "0f3c2a10-6c1e-4b8e-9a52-5d0c1f7e2a11"
TICKET_FLOW = "7b9d4e22-1a3f-4c6d-8e05-2f6a9b3c4d55"
ENTITIES = {
    "BooleanPrebuiltEntity": bool,
    "StringPrebuiltEntity": str,
    "NumberPrebuiltEntity": (int, float),
    "PersonNamePrebuiltEntity": str,
    "DateTimePrebuiltEntity": str,
    "EmailPrebuiltEntity": str,
}


class SimError(Exception):
    pass


class UndefinedVariable(SimError):
    pass


def load_topics(agent_dir: pathlib.Path) -> dict[str, dict]:
    topics = {}
    for p in sorted((agent_dir / "topics").glob("*.topic.yaml")):
        name = p.name[: -len(".topic.yaml")]
        topics[name] = yaml.safe_load(p.read_text())
    return topics


# ---------------------------------------------------------------- Power Fx subset

_TOKEN = re.compile(
    r'\s*(?:(?P<str>"(?:[^"]|"")*")|(?P<num>\d+(?:\.\d+)?)|(?P<op><>|<=|>=|&&|\|\||[=<>!&(),])'
    r"|(?P<id>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*))"
)


def _tokenize(src: str) -> list[tuple[str, str]]:
    out, pos = [], 0
    src = src.strip()
    while pos < len(src):
        m = _TOKEN.match(src, pos)
        if not m or m.end() == pos:
            raise SimError(f"cannot parse formula near: {src[pos:pos + 20]!r}")
        pos = m.end()
        kind = m.lastgroup
        out.append((kind, m.group(kind)))
    return out


class _Parser:
    def __init__(self, tokens, lookup):
        self.t, self.i, self.lookup = tokens, 0, lookup

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def take(self, val=None):
        tok = self.peek()
        if val is not None and tok[1] != val:
            raise SimError(f"expected {val!r}, got {tok[1]!r}")
        self.i += 1
        return tok

    def parse(self):
        v = self.or_()
        if self.i != len(self.t):
            raise SimError(f"unexpected token {self.peek()[1]!r}")
        return v

    def or_(self):
        v = self.and_()
        while self.peek()[1] in ("||", "Or"):
            self.take()
            r = self.and_()
            v = bool(v) or bool(r)
        return v

    def and_(self):
        v = self.not_()
        while self.peek()[1] in ("&&", "And"):
            self.take()
            r = self.not_()
            v = bool(v) and bool(r)
        return v

    def not_(self):
        if self.peek()[1] == "!" or (self.peek()[1] == "Not" and self.t[self.i + 1:self.i + 2] != [("op", "(")]):
            self.take()
            return not bool(self.not_())
        return self.cmp()

    def cmp(self):
        left = self.concat()
        op = self.peek()[1]
        if op in ("=", "<>", "<", "<=", ">", ">="):
            self.take()
            right = self.concat()
            if op == "=":
                return _eq(left, right)
            if op == "<>":
                return not _eq(left, right)
            if left is None or right is None:
                return False
            return {"<": left < right, "<=": left <= right, ">": left > right, ">=": left >= right}[op]
        return left

    def concat(self):
        v = self.primary()
        while self.peek()[1] == "&":
            self.take()
            r = self.primary()
            v = ("" if v is None else str(v)) + ("" if r is None else str(r))
        return v

    def primary(self):
        kind, val = self.take()
        if kind == "str":
            return val[1:-1].replace('""', '"')
        if kind == "num":
            return float(val) if "." in val else int(val)
        if kind == "op" and val == "(":
            v = self.or_()
            self.take(")")
            return v
        if kind == "id":
            if val == "true":
                return True
            if val == "false":
                return False
            if self.peek()[1] == "(":
                self.take("(")
                args = []
                if self.peek()[1] != ")":
                    args.append(self.or_())
                    while self.peek()[1] == ",":
                        self.take()
                        args.append(self.or_())
                self.take(")")
                return _call(val, args)
            return self.lookup(val)
        raise SimError(f"unexpected token {val!r}")


def _eq(a, b):
    if a is None or b is None:
        return (a in (None, "")) and (b in (None, ""))
    return a == b


def _call(name, args):
    if name == "IsBlank":
        return args[0] is None or args[0] == ""
    if name == "Blank":
        return None
    if name == "Not":
        return not bool(args[0])
    if name == "And":
        return all(bool(a) for a in args)
    if name == "Or":
        return any(bool(a) for a in args)
    if name == "Text":
        return "" if args[0] is None else str(args[0])
    raise SimError(f"function {name}() is not supported by the simulator")


# ---------------------------------------------------------------- runtime

class _Stop(Exception):
    def __init__(self, scope):
        self.scope = scope  # "dialog" or "conversation"


@dataclass
class Session:
    topics: dict[str, dict]
    flows: dict[str, Callable[[dict], dict]]
    upn: str = "dana.kim@litware.com"
    transcript: list[str] = field(default_factory=list)
    flow_calls: list[tuple[str, dict]] = field(default_factory=list)
    questions_asked: list[str] = field(default_factory=list)
    globals: dict[str, Any] = field(default_factory=dict)
    fallback_count: int = 0
    activity_text: str = ""
    topics_run: list[str] = field(default_factory=list)

    # --- public driver API
    def start(self):
        self._run_named(self._find_trigger("OnConversationStart"), [], top=True)

    def recognized(self, topic: str, text: str, answers: list | None = None):
        """The orchestrator picked `topic` for the user's message `text`."""
        self.fallback_count = 0
        self.activity_text = text
        self._run_named(topic, list(answers or []), top=True)

    def unrecognized(self, text: str, answers: list | None = None):
        self.fallback_count += 1
        self.activity_text = text
        self._run_named(self._find_trigger("OnUnknownIntent"), list(answers or []), top=True)

    def escalate(self, text: str):
        self.fallback_count = 0
        self.activity_text = text
        self._run_named(self._find_trigger("OnEscalate"), [], top=True)

    # --- internals
    def _find_trigger(self, kind):
        for name, t in self.topics.items():
            if (t.get("beginDialog") or {}).get("kind") == kind:
                return name
        raise SimError(f"no topic with trigger {kind}")

    def _run_named(self, name, answers, top=False):
        if name not in self.topics:
            raise SimError(f"unknown topic {name}")
        self.topics_run.append(name)
        scope: dict[str, Any] = {}
        try:
            self._run(self.topics[name]["beginDialog"].get("actions") or [], scope, answers)
        except _Stop as s:
            if s.scope == "conversation":
                raise
        if top and answers:
            raise SimError(f"topic {name} ended with unused scripted answers {answers!r}")

    def _lookup(self, scope):
        def get(name):
            if name.startswith("Topic."):
                key = name[6:]
                if key not in scope:
                    raise UndefinedVariable(f"{name} read before it was set")
                return scope[key]
            if name.startswith("Global."):
                key = name[7:]
                if key not in self.globals:
                    raise UndefinedVariable(f"{name} read before it was set")
                return self.globals[key]
            if name == "System.FallbackCount":
                return self.fallback_count
            if name == "System.Activity.Text":
                return self.activity_text
            if name == "System.User.PrincipalName":
                return self.upn
            raise SimError(f"variable {name} not supported by the simulator")
        return get

    def _eval(self, value, scope):
        if isinstance(value, str) and value.startswith("="):
            return _Parser(_tokenize(value[1:]), self._lookup(scope)).parse()
        return value

    def _set(self, var, value, scope):
        var = var[5:] if var.startswith("init:") else var
        if var.startswith("Topic."):
            scope[var[6:]] = value
        elif var.startswith("Global."):
            self.globals[var[7:]] = value
        else:
            raise SimError(f"cannot assign to {var}")

    def _interp(self, text, scope):
        get = self._lookup(scope)

        def rep(m):
            v = get(m.group(1))
            return "" if v is None else str(v)
        return re.sub(r"\{((?:Topic|Global|System)\.[A-Za-z0-9_.]+)\}", rep, text)

    def _run(self, actions, scope, answers):
        for node in actions:
            kind = node.get("kind")
            if kind == "SendActivity":
                act = node.get("activity")
                if isinstance(act, dict):
                    act = (act.get("text") or [""])[0]
                self.transcript.append(self._interp(str(act), scope))
            elif kind == "Question":
                ent = node.get("entity")
                if ent not in ENTITIES:
                    raise SimError(f"Question {node.get('id')} has unsupported or missing entity {ent!r}")
                if not answers:
                    raise SimError(f"Question {node.get('id')} asked but the script has no more answers")
                ans = answers.pop(0)
                if not isinstance(ans, ENTITIES[ent]):
                    raise SimError(f"answer {ans!r} does not fit entity {ent}")
                self.questions_asked.append(node.get("id"))
                self._set(node["variable"], ans, scope)
            elif kind == "SetVariable":
                self._set(node["variable"], self._eval(node.get("value"), scope), scope)
            elif kind == "ConditionGroup":
                for cond in node.get("conditions") or []:
                    if self._eval(cond["condition"], scope):
                        self._run(cond.get("actions") or [], scope, answers)
                        break
                else:
                    self._run(node.get("elseActions") or [], scope, answers)
            elif kind == "BeginDialog":
                target = str(node.get("dialog", ""))
                prefix = f"{SCHEMA}.topic."
                if not target.startswith(prefix):
                    raise SimError(f"BeginDialog target {target!r} is not a {prefix}<Name> topic")
                self._run_named(target[len(prefix):], answers)
            elif kind == "InvokeFlowAction":
                fid = node.get("flowId")
                if fid not in self.flows:
                    raise SimError(f"unknown flowId {fid}")
                binding = ((node.get("input") or {}).get("binding")) or {}
                inputs = {k: self._eval(v, scope) for k, v in binding.items()}
                self.flow_calls.append((fid, inputs))
                outputs = self.flows[fid](inputs)
                for out_name, var in (((node.get("output") or {}).get("binding")) or {}).items():
                    if out_name not in outputs:
                        raise SimError(f"flow {fid} has no output {out_name}")
                    self._set(var, outputs[out_name], scope)
            elif kind == "EndDialog":
                raise _Stop("dialog")
            elif kind in ("EndConversation", "CancelAllDialogs"):
                raise _Stop("conversation")
            else:
                raise SimError(f"node kind {kind!r} is not supported by the simulator")


def make_flows(reset_status="Success", ticket_ids=("INC0042117", "INC0042118", "INC0042119")):
    tickets = list(ticket_ids)

    def reset(inputs):
        return {"resetStatus": reset_status}

    def ticket(inputs):
        return {"ticketId": tickets.pop(0)}
    return {RESET_FLOW: reset, TICKET_FLOW: ticket}


def new_session(agent_dir, **flow_kw) -> Session:
    s = Session(topics=load_topics(pathlib.Path(agent_dir)), flows=make_flows(**flow_kw))
    s.start()
    return s
