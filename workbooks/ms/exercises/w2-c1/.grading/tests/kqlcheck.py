"""Tiny structural KQL analyzer used by the hidden tests.

There is no Kusto engine on the machine, so this works at the token level:
strip comments and string literals, split pipelines at top-level '|', and
parse summarize / project / sort clauses into lists of expressions.
"""

import json
import re

STRING_RE = re.compile(
    r"```.*?```"            # multi-line string literal
    r"|@'(?:[^']|'')*'"     # verbatim single-quoted
    r'|@"(?:[^"]|"")*"'     # verbatim double-quoted
    r"|'(?:[^'\\\n]|\\.)*'"  # single-quoted
    r'|"(?:[^"\\\n]|\\.)*"',  # double-quoted
    re.S,
)


def strip_comments(text: str) -> str:
    """Remove // comments that are not inside string literals."""
    out = []
    i = 0
    while i < len(text):
        m = STRING_RE.match(text, i)
        if m:
            out.append(m.group(0))
            i = m.end()
            continue
        if text.startswith("//", i):
            j = text.find("\n", i)
            i = len(text) if j == -1 else j
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def mask_strings(text: str):
    """Replace string literals with placeholders; return (code, strings)."""
    strings = []

    def repl(m):
        strings.append(m.group(0))
        return f'"__S{len(strings) - 1}__"'

    return STRING_RE.sub(repl, text), strings


def unquote(lit: str) -> str:
    if lit.startswith("```"):
        return lit[3:-3]
    if lit.startswith("@"):
        q = lit[1]
        return lit[2:-1].replace(q + q, q)
    return bytes(lit[1:-1], "utf-8").decode("unicode_escape")


def clean(text: str):
    code, strings = mask_strings(strip_comments(text))
    return code, strings


def split_top(s: str, sep: str):
    """Split on a single-char separator at nesting depth 0."""
    parts, depth, cur = [], 0, []
    for ch in s:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return [p.strip() for p in parts]


def find_top_keyword(s: str, kw: str) -> int:
    depth = 0
    for i, ch in enumerate(s):
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif depth == 0 and s[i:i + len(kw)].lower() == kw:
            before = s[i - 1] if i > 0 else " "
            after = s[i + len(kw)] if i + len(kw) < len(s) else " "
            if not (before.isalnum() or before == "_") and not (after.isalnum() or after == "_"):
                return i
    return -1


def norm(expr: str) -> str:
    return re.sub(r"\s+", "", expr).lower()


def query_body(code: str) -> str:
    """Drop leading let statements; return the final tabular expression."""
    stmts = [s for s in split_top(code, ";") if s.strip()]
    body = [s for s in stmts if not re.match(r"^\s*let\b", s)]
    return body[-1] if body else ""


def segments(query: str):
    """[source, op1, op2, ...] with op text stripped."""
    return [p for p in split_top(query, "|") if p != ""]


def op_name(seg: str) -> str:
    m = re.match(r"\s*([A-Za-z_][\w-]*)", seg)
    if not m:
        return ""
    name = m.group(1).lower()
    if name == "order":
        return "sort"
    return name


def ops(query: str):
    return [op_name(s) for s in segments(query)[1:]]


def split_alias(item: str):
    """'Name = expr' -> (Name, expr); 'expr' -> (None, expr)."""
    m = re.match(r"^\s*([A-Za-z_]\w*)\s*=(?!=)\s*(.+)$", item, re.S)
    if m:
        return m.group(1), m.group(2).strip()
    return None, item.strip()


def parse_summarize(seg: str):
    body = re.sub(r"^\s*summarize\b", "", seg, flags=re.I).strip()
    # drop hints like hint.strategy=shuffle
    body = re.sub(r"^(hint\.\w+\s*=\s*\w+\s*)+", "", body, flags=re.I)
    i = find_top_keyword(body, "by")
    aggs_s, keys_s = (body, "") if i < 0 else (body[:i], body[i + 2:])
    aggs = [split_alias(a) for a in split_top(aggs_s, ",") if a]
    keys = [split_alias(k) for k in split_top(keys_s, ",") if k]
    return aggs, keys


def parse_list(seg: str, op: str):
    body = re.sub(rf"^\s*{op}\b", "", seg, flags=re.I).strip()
    return [split_alias(a) for a in split_top(body, ",") if a]


BIN_RE = re.compile(r"^bin\(\s*([A-Za-z_]\w*)\s*,\s*([^)]+)\)$", re.I)


def timespan_seconds(lit: str):
    lit = lit.strip().lower()
    m = re.match(r"^(?:time|timespan)\((.+)\)$", lit)
    if m:
        lit = m.group(1).strip()
    m = re.match(r"^(\d+(?:\.\d+)?)\s*(d|h|m|min|minute|minutes|s|sec|second|seconds|ms)$", lit)
    if not m:
        return None
    v = float(m.group(1))
    unit = m.group(2)
    mult = {"d": 86400, "h": 3600, "m": 60, "min": 60, "minute": 60, "minutes": 60,
            "s": 1, "sec": 1, "second": 1, "seconds": 1, "ms": 0.001}[unit]
    return v * mult


def mgmt_commands(code: str):
    """Split a file into management commands (lines starting with '.')."""
    cmds, cur = [], []
    for line in code.splitlines():
        if re.match(r"^\s*\.[a-z]", line) and cur:
            cmds.append("\n".join(cur))
            cur = []
        cur.append(line)
    if cur:
        cmds.append("\n".join(cur))
    return [c.strip() for c in cmds if c.strip()]


def parse_table_schema(text: str):
    """Parse '.create[-merge] table T (a: type, ...)' commands -> {T: [(col, type)]}."""
    code, _ = clean(text)
    tables = {}
    for m in re.finditer(r"\.create(?:-merge)?\s+table\s+(\w+)\s*\(([^)]*)\)", code, re.I):
        cols = []
        for part in split_top(m.group(2), ","):
            n, t = [x.strip() for x in part.split(":")]
            cols.append((n, t.lower()))
        tables[m.group(1)] = cols
    return tables


def json_from_literal(lit: str):
    return json.loads(unquote(lit))
