#!/usr/bin/env python3
"""cli_lint.py: a static dry run of a jboss-cli script against what exists on the EAP 8 target.

Not a real management model: it parses `/subsystem=<s>/<type>=<name>:add(...)` operations, checks that
the subsystem exists on EAP 8, and that every reference to another Elytron or Undertow resource points at
something the script creates or config/eap8-existing.txt lists. Use it as `make check`; it is the local
stand-in for running the script against a test server.

Usage: cli_lint.py [script]   (default config/migrate-security.cli)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EAP8_SUBSYSTEMS = {"elytron", "undertow", "ejb3", "datasources", "naming", "mail", "messaging-activemq", "logging", "transactions"}
OP = re.compile(r"^/subsystem=([\w-]+)/([\w-]+)=([^/:]+)(?:/([\w-]+)=([^:]+))?:(\w[\w-]*)\((.*)\)\s*$")

REFS = {  # attribute -> resource types it may point at
    "dir-context": {"dir-context"},
    "role-decoder": {"simple-role-decoder"},
    "role-mapper": {"mapped-role-mapper", "simple-role-mapper", "constant-role-mapper"},
    "permission-mapper": {"simple-permission-mapper", "constant-permission-mapper"},
    "security-domain": {"security-domain"},
    "http-authentication-factory": {"http-authentication-factory"},
    "http-server-mechanism-factory": {"provider-http-server-mechanism-factory", "global"},
    "default-realm": {"ldap-realm", "properties-realm", "filesystem-realm", "jdbc-realm"},
    "realm": {"ldap-realm", "properties-realm", "filesystem-realm", "jdbc-realm"},
    "store": {"credential-store"},
}


def split_top(s: str) -> list[str]:
    out, depth, cur, q = [], 0, "", False
    for ch in s:
        if ch == '"':
            q = not q
        if not q and ch in "{[(":
            depth += 1
        if not q and ch in "}])":
            depth -= 1
        if ch == "," and depth == 0 and not q:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def attrs(raw: str) -> dict[str, str]:
    d = {}
    for part in split_top(raw):
        if "=" in part:
            k, v = part.split("=", 1)
            d[k.strip()] = v.strip().strip('"')
    return d


def parse(script: str) -> list[dict]:
    ops = []
    for n, line in enumerate(script.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#") or line in ("batch", "run-batch", "reload"):
            continue
        m = OP.match(line)
        if not m:
            ops.append({"line": n, "raw": line, "unparsed": True})
            continue
        sub, typ, name, ctyp, cname, op, raw = m.groups()
        ops.append({"line": n, "raw": line, "subsystem": sub, "type": typ, "name": name.strip('"'),
                    "child": (ctyp, cname) if ctyp else None, "op": op, "args": raw, "attrs": attrs(raw)})
    return ops


def existing() -> set[tuple[str, str, str]]:
    have = set()
    for line in (ROOT / "config/eap8-existing.txt").read_text().splitlines():
        m = re.match(r"^/subsystem=([\w-]+)/([\w-]+)=([^\s]+)", line.strip())
        if m:
            have.add(m.groups())
    return have


def refs_in(raw: str) -> list[tuple[str, str]]:
    return [(k, v) for k, v in re.findall(r"([\w-]+)=\"?([\w.-]+)\"?", raw) if k in REFS]


def lint(script: str) -> list[str]:
    ops = parse(script)
    errors = []
    defined = existing()
    for o in ops:
        if o.get("unparsed"):
            errors.append(f"line {o['line']}: cannot parse: {o['raw'][:80]}")
            continue
        if o["subsystem"] not in EAP8_SUBSYSTEMS:
            errors.append(f"line {o['line']}: WFLYCTL0030: No resource definition is registered for address subsystem={o['subsystem']}")
            continue
        if o["op"] == "add" and not o["child"]:
            defined.add((o["subsystem"], o["type"], o["name"]))
        if "${VAULT::" in o["args"]:
            errors.append(f"line {o['line']}: vault expressions are not supported on EAP 8 (use a credential-store credential-reference)")
    names = {(t, n) for _, t, n in defined}
    for o in ops:
        if o.get("unparsed") or o["subsystem"] not in EAP8_SUBSYSTEMS:
            continue
        for k, v in refs_in(o["args"]):
            if k == "security-domain" and o["type"] == "security-domain":
                continue
            if k == "http-server-mechanism-factory" and v == "global":
                continue
            if not any((t, v) in names for t in REFS[k]):
                errors.append(f"line {o['line']}: {k}={v} does not exist on the target or in this script")
    return errors


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else ROOT / "config/migrate-security.cli"
    errs = lint(path.read_text())
    print("\n".join(errs) if errs else f"{path.name}: dry run OK ({len(parse(path.read_text()))} operations)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
