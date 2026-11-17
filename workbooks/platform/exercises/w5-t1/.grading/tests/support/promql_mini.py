"""A small PromQL subset evaluator for offline rule testing (platform/w5-t1).

Supported:
  selectors        metric{label="v", label!="v", label=~"re", label!~"re"} (metric name optional
                   when matchers are given); instant lookback 5m; a missing label equals ""
  range functions  rate(sel[5m]), increase(sel[1h])  (per-second rate from the first and last
                   sample in the window, counter resets handled, no extrapolation)
  functions        absent(expr), vector(scalar)
  aggregations     sum, max, min, avg, count with by (...) or without (...), before or after the
                   argument
  arithmetic       + - * / between scalars, vector/scalar and vector/vector (one-to-one matching on
                   the full label set without __name__; on(...) and ignoring(...) are supported)
  comparisons      > < >= <= == != as filters (no bool modifier)
  set operators    and, or, unless (matching on the full label set, or on(...)/ignoring(...))

Not supported: subqueries, offset, @, histogram functions, group_left/group_right, bool.
"""

from __future__ import annotations

import bisect
import re
from dataclasses import dataclass, field

LOOKBACK = 300.0
DUR = {"s": 1, "m": 60, "h": 3600, "d": 86400}


class PromQLError(Exception):
    pass


# ----------------------------------------------------------------------------- storage
@dataclass
class Series:
    labels: dict
    ts: list = field(default_factory=list)
    vs: list = field(default_factory=list)

    def add(self, t: float, v: float) -> None:
        self.ts.append(t)
        self.vs.append(v)


class TSDB:
    def __init__(self) -> None:
        self.series: dict[tuple, Series] = {}

    @staticmethod
    def key(labels: dict) -> tuple:
        return tuple(sorted(labels.items()))

    def add(self, labels: dict, t: float, v: float) -> None:
        k = self.key(labels)
        s = self.series.get(k)
        if s is None:
            s = self.series[k] = Series(dict(labels))
        s.add(t, v)

    @classmethod
    def from_json(cls, data: dict) -> "TSDB":
        db = cls()
        for s in data["series"]:
            ser = Series(dict(s["labels"]), [float(t) for t, _ in s["samples"]], [float(v) for _, v in s["samples"]])
            db.series[cls.key(ser.labels)] = ser
        return db

    def select(self, matchers: list) -> list[Series]:
        return [s for s in self.series.values() if all(m(s.labels) for m in matchers)]


# ----------------------------------------------------------------------------- lexer
TOKEN = re.compile(r"""
    (?P<ws>\s+)
  | (?P<dur>\d+[smhd])(?![a-zA-Z0-9_])
  | (?P<num>\d+\.\d*|\.\d+|\d+(?:[eE][+-]?\d+)?)(?![a-zA-Z0-9_])
  | (?P<str>"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')
  | (?P<op>=~|!~|!=|==|>=|<=|[-+*/(){}\[\],=<>])
  | (?P<ident>[a-zA-Z_:][a-zA-Z0-9_:]*)
""", re.X)


def lex(src: str) -> list[tuple[str, str]]:
    out, pos = [], 0
    while pos < len(src):
        m = TOKEN.match(src, pos)
        if not m:
            raise PromQLError(f"unexpected character at {pos}: {src[pos:pos + 10]!r}")
        pos = m.end()
        kind = m.lastgroup
        if kind != "ws":
            out.append((kind, m.group()))
    out.append(("eof", ""))
    return out


# ----------------------------------------------------------------------------- AST
AGGS = {"sum", "max", "min", "avg", "count"}
CMP = {">", "<", ">=", "<=", "==", "!="}


def matcher(label: str, op: str, value: str):
    if op == "=":
        return lambda ls: ls.get(label, "") == value
    if op == "!=":
        return lambda ls: ls.get(label, "") != value
    rx = re.compile(f"^(?:{value})$")
    if op == "=~":
        return lambda ls: bool(rx.match(ls.get(label, "")))
    return lambda ls: not rx.match(ls.get(label, ""))


class Parser:
    def __init__(self, src: str) -> None:
        self.toks = lex(src)
        self.i = 0

    def peek(self, k: int = 0):
        return self.toks[self.i + k]

    def take(self, value: str | None = None, kind: str | None = None):
        t = self.toks[self.i]
        if (value is not None and t[1] != value) or (kind is not None and t[0] != kind):
            raise PromQLError(f"expected {value or kind}, got {t[1]!r}")
        self.i += 1
        return t

    def parse(self):
        node = self.expr()
        if self.peek()[0] != "eof":
            raise PromQLError(f"trailing input at {self.peek()[1]!r}")
        return node

    def expr(self):
        return self.binary(0)

    LEVELS = [({"or"},), ({"and", "unless"},), (CMP,), ({"+", "-"},), ({"*", "/"},)]

    def binary(self, level: int):
        if level == len(self.LEVELS):
            return self.unary()
        ops = self.LEVELS[level][0]
        left = self.binary(level + 1)
        while self.peek()[1] in ops and self.peek()[0] in ("op", "ident"):
            op = self.take()[1]
            match = self.matching()
            right = self.binary(level + 1)
            left = ("bin", op, left, right, match)
        return left

    def matching(self):
        t = self.peek()
        if t[0] == "ident" and t[1] in ("on", "ignoring"):
            self.take()
            return (t[1], self.label_list())
        return None

    def label_list(self) -> list[str]:
        self.take("(")
        labels = []
        while self.peek()[1] != ")":
            labels.append(self.take(kind="ident")[1])
            if self.peek()[1] == ",":
                self.take(",")
        self.take(")")
        return labels

    def unary(self):
        t = self.peek()
        if t[1] == "-" and t[0] == "op":
            self.take()
            return ("bin", "*", ("num", -1.0), self.unary(), None)
        if t[0] == "num":
            self.take()
            return ("num", float(t[1]))
        if t[1] == "(":
            self.take("(")
            n = self.expr()
            self.take(")")
            return n
        if t[1] == "{":
            return self.selector(None)
        if t[0] == "ident":
            name = t[1]
            if name in AGGS:
                return self.aggregation()
            if name in ("rate", "increase") and self.peek(1)[1] == "(":
                self.take()
                self.take("(")
                sel = self.selector(self.take(kind="ident")[1] if self.peek()[0] == "ident" else None)
                self.take("[")
                d = self.take()[1]
                self.take("]")
                self.take(")")
                return ("range", name, sel, parse_duration(d))
            if name in ("absent", "vector") and self.peek(1)[1] == "(":
                self.take()
                self.take("(")
                arg = self.expr()
                self.take(")")
                return ("func", name, arg)
            self.take()
            return self.selector(name)
        raise PromQLError(f"unexpected token {t[1]!r}")

    def aggregation(self):
        op = self.take()[1]
        grouping = None
        if self.peek()[1] in ("by", "without"):
            g = self.take()[1]
            grouping = (g, self.label_list())
        self.take("(")
        arg = self.expr()
        self.take(")")
        if grouping is None and self.peek()[1] in ("by", "without"):
            g = self.take()[1]
            grouping = (g, self.label_list())
        return ("agg", op, grouping, arg)

    def selector(self, name):
        ms, eqs = [], {}
        if name:
            ms.append(matcher("__name__", "=", name))
            eqs["__name__"] = name
        if self.peek()[1] == "{":
            self.take("{")
            while self.peek()[1] != "}":
                label = self.take(kind="ident")[1]
                op = self.take()[1]
                if op not in ("=", "!=", "=~", "!~"):
                    raise PromQLError(f"bad matcher op {op}")
                raw = self.take(kind="str")[1]
                val = bytes(raw[1:-1], "utf8").decode("unicode_escape")
                ms.append(matcher(label, op, val))
                if op == "=":
                    eqs[label] = val
                if self.peek()[1] == ",":
                    self.take(",")
            self.take("}")
        if not ms:
            raise PromQLError("empty selector")
        return ("sel", ms, eqs)


def parse_duration(d: str) -> float:
    m = re.fullmatch(r"(\d+)([smhd])", d)
    if not m:
        raise PromQLError(f"bad duration {d!r}")
    return float(m.group(1)) * DUR[m.group(2)]


def parse(src: str):
    return Parser(src).parse()


# ----------------------------------------------------------------------------- evaluation
def strip_name(ls: dict) -> dict:
    return {k: v for k, v in ls.items() if k != "__name__"}


def sig(ls: dict, match) -> tuple:
    ls = strip_name(ls)
    if match is None:
        return tuple(sorted(ls.items()))
    kind, names = match
    if kind == "on":
        return tuple(sorted((k, ls.get(k, "")) for k in names))
    return tuple(sorted((k, v) for k, v in ls.items() if k not in names))


def instant(series: Series, t: float):
    i = bisect.bisect_right(series.ts, t) - 1
    if i < 0 or t - series.ts[i] > LOOKBACK:
        return None
    return series.vs[i]


def window_rate(series: Series, t: float, rng: float):
    lo = bisect.bisect_right(series.ts, t - rng)
    hi = bisect.bisect_right(series.ts, t)
    if hi - lo < 2:
        return None
    total, prev = 0.0, series.vs[lo]
    for v in series.vs[lo + 1:hi]:
        total += v - prev if v >= prev else v
        prev = v
    span = series.ts[hi - 1] - series.ts[lo]
    return total / span if span > 0 else None


def evaluate(node, db: TSDB, t: float):
    """Return a float (scalar) or a list of (labels, value) (instant vector)."""
    kind = node[0]
    if kind == "num":
        return node[1]
    if kind == "sel":
        out = []
        for s in db.select(node[1]):
            v = instant(s, t)
            if v is not None:
                out.append((dict(s.labels), v))
        return out
    if kind == "range":
        _, fn, sel, rng = node
        out = []
        for s in db.select(sel[1]):
            r = window_rate(s, t, rng)
            if r is not None:
                out.append((strip_name(s.labels), r * rng if fn == "increase" else r))
        return out
    if kind == "func":
        _, fn, arg = node
        if fn == "vector":
            v = evaluate(arg, db, t)
            if isinstance(v, list):
                raise PromQLError("vector() takes a scalar")
            return [({}, v)]
        v = evaluate(arg, db, t)
        if isinstance(v, list) and v:
            return []
        labels = {k: val for k, val in arg[2].items() if k != "__name__"} if arg[0] in ("sel",) else (
            {k: val for k, val in arg[2][2].items() if k != "__name__"} if arg[0] == "range" else {})
        return [(labels, 1.0)]
    if kind == "agg":
        _, op, grouping, arg = node
        v = evaluate(arg, db, t)
        if not isinstance(v, list):
            raise PromQLError(f"{op} needs a vector")
        groups: dict[tuple, list] = {}
        glabels: dict[tuple, dict] = {}
        for ls, val in v:
            ls = strip_name(ls)
            if grouping is None:
                g = {}
            elif grouping[0] == "by":
                g = {k: ls[k] for k in grouping[1] if ls.get(k, "") != ""}
            else:
                g = {k: x for k, x in ls.items() if k not in grouping[1]}
            k = tuple(sorted(g.items()))
            groups.setdefault(k, []).append(val)
            glabels[k] = g
        fns = {"sum": sum, "max": max, "min": min, "count": len, "avg": lambda xs: sum(xs) / len(xs)}
        return [(glabels[k], float(fns[op](vals))) for k, vals in groups.items()]
    if kind == "bin":
        _, op, ln, rn, match = node
        lv, rv = evaluate(ln, db, t), evaluate(rn, db, t)
        return binop(op, lv, rv, match)
    raise PromQLError(f"unknown node {kind}")


def arith(op: str, a: float, b: float):
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "/":
        return a / b if b != 0 else (float("nan") if a == 0 else float("inf") * (1 if a > 0 else -1))
    return {">": a > b, "<": a < b, ">=": a >= b, "<=": a <= b, "==": a == b, "!=": a != b}[op]


def binop(op, lv, rv, match):
    ls, rs = isinstance(lv, list), isinstance(rv, list)
    if op in ("and", "or", "unless"):
        if not (ls and rs):
            raise PromQLError(f"{op} needs two vectors")
        rsig = {sig(l, match) for l, _ in rv}
        if op == "and":
            return [(l, v) for l, v in lv if sig(l, match) in rsig]
        if op == "unless":
            return [(l, v) for l, v in lv if sig(l, match) not in rsig]
        lsig = {sig(l, match) for l, _ in lv}
        return list(lv) + [(l, v) for l, v in rv if sig(l, match) not in lsig]
    if not ls and not rs:
        r = arith(op, lv, rv)
        return float(r) if op not in CMP else (1.0 if r else 0.0)
    if ls and not rs:
        if op in CMP:
            return [(l, v) for l, v in lv if arith(op, v, rv)]
        return [(strip_name(l), arith(op, v, rv)) for l, v in lv]
    if rs and not ls:
        if op in CMP:
            return [(l, v) for l, v in rv if arith(op, lv, v)]
        return [(strip_name(l), arith(op, lv, v)) for l, v in rv]
    right = {}
    for l, v in rv:
        k = sig(l, match)
        if k in right:
            raise PromQLError("many-to-many matching on the right-hand side")
        right[k] = v
    out = []
    for l, v in lv:
        k = sig(l, match)
        if k not in right:
            continue
        if op in CMP:
            if arith(op, v, right[k]):
                out.append((l, v))
        else:
            res = strip_name(l) if match is None or match[0] == "ignoring" else dict(k)
            out.append((res, arith(op, v, right[k])))
    return out


def query(src: str, db: TSDB, t: float):
    return evaluate(parse(src), db, t)
