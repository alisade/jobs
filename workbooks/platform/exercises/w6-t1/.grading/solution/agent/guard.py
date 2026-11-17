"""PreToolUse guard for the unmanaged-resource import agent (tsl-import-agent).

The agent's Bash tool calls check_command() before every command, the same way a PreToolUse hook in a
coding-agent harness can deny a tool call. The agent may read and draft; it must never change
infrastructure. Applies go through the reviewed pipeline, never through the agent.

Design: parse the command line (not regex the raw string), split compound commands, unwrap wrappers
(env, sudo, nohup, time, command, bash -c / sh -c), resolve the binary's basename, skip global options,
and ALLOW only an explicit list of read-only subcommands. Everything else is denied. Command
substitution is denied outright because the guard cannot see what it will run.
"""

from __future__ import annotations

import os
import re
import shlex
from dataclasses import dataclass


@dataclass(frozen=True)
class Decision:
    allow: bool
    reason: str


WRAPPERS = {"env", "sudo", "nohup", "time", "command", "nice", "timeout", "exec"}
SHELLS = {"bash", "sh", "zsh", "dash"}
TF_READ = {"init", "plan", "show", "validate", "fmt", "version", "providers", "output", "graph"}
TF_STATE_READ = {"list", "show", "pull"}
GCLOUD_READ_VERBS = {"list", "describe", "get-iam-policy", "search-all-resources", "search-all-iam-policies",
                     "analyze-iam-policy", "config", "info", "version"}
SIMPLE_READ = {"ls", "cat", "head", "tail", "jq", "grep", "wc", "diff", "echo", "pwd", "find", "sort", "uniq"}
GIT_OK = {"status", "diff", "log", "show", "add", "commit", "checkout", "switch", "branch", "push", "fetch", "rev-parse"}
GH_OK = {("pr", "create"), ("pr", "view"), ("pr", "list")}


def _segments(cmd: str) -> list[list[str]]:
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=";&|")
    lex.whitespace_split = True
    segs, cur = [], []
    for tok in lex:
        if tok and set(tok) <= set(";&|"):
            if cur:
                segs.append(cur)
            cur = []
        else:
            cur.append(tok)
    if cur:
        segs.append(cur)
    return segs


def _unwrap(argv: list[str]) -> list[str]:
    while argv:
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", argv[0]):
            argv = argv[1:]
            continue
        base = os.path.basename(argv[0])
        if base in WRAPPERS:
            argv = argv[1:]
            while argv and (argv[0].startswith("-") or (base == "timeout" and re.match(r"^\d+[smh]?$", argv[0]))):
                argv = argv[1:]
            continue
        break
    return argv


def _first_positional(args: list[str]) -> tuple[str | None, list[str]]:
    for i, a in enumerate(args):
        if not a.startswith("-"):
            return a, args[i + 1:]
    return None, []


def _check_argv(argv: list[str], depth: int) -> Decision:
    argv = _unwrap(argv)
    if not argv:
        return Decision(True, "empty")
    base = os.path.basename(argv[0])
    rest = argv[1:]
    if base in SHELLS:
        if len(rest) >= 2 and rest[0] in ("-c", "-lc", "-ec"):
            if depth > 3:
                return Decision(False, "nested shells too deep")
            return check_command(rest[1], depth + 1)
        return Decision(False, f"interactive or script shell invocation denied: {' '.join(argv)}")
    if base in ("terraform", "tofu"):
        sub, after = _first_positional(rest)
        if sub in TF_READ:
            if sub == "plan" and any(a in ("-destroy",) for a in after):
                return Decision(True, "plan -destroy is read-only")
            return Decision(True, f"{base} {sub} is read-only")
        if sub == "state":
            s2, _ = _first_positional(after)
            if s2 in TF_STATE_READ:
                return Decision(True, f"{base} state {s2} is read-only")
        return Decision(False, f"{base} {sub or ''} changes infrastructure or state; only the reviewed pipeline may run it")
    if base == "gcloud":
        positional = [a for a in rest if not a.startswith("-")]
        verb = next((p for p in reversed(positional) if p in GCLOUD_READ_VERBS), None)
        if verb and not any(p in ("delete", "create", "update", "set-iam-policy", "add-iam-policy-binding",
                                  "remove-iam-policy-binding", "patch", "deploy") for p in positional):
            return Decision(True, f"gcloud {verb} is read-only")
        return Decision(False, "gcloud command is not on the read-only list")
    if base in SIMPLE_READ:
        return Decision(True, f"{base} is read-only")
    if base == "git":
        sub, after = _first_positional(rest)
        if sub == "push" and any(a in ("--force", "-f", "--force-with-lease") for a in after):
            return Decision(False, "force push denied")
        if sub in GIT_OK:
            return Decision(True, f"git {sub}")
        return Decision(False, f"git {sub} not allowed")
    if base == "gh":
        pos = [a for a in rest if not a.startswith("-")]
        if tuple(pos[:2]) in GH_OK:
            return Decision(True, "gh " + " ".join(pos[:2]))
        return Decision(False, "gh command not allowed")
    return Decision(False, f"{base} is not on the agent's allow list")


def check_command(cmd: str, depth: int = 0) -> Decision:
    if "`" in cmd or "$(" in cmd or "<(" in cmd or ">(" in cmd:
        return Decision(False, "command substitution denied: the guard cannot see what it runs")
    try:
        segs = _segments(cmd)
    except ValueError as e:
        return Decision(False, f"cannot parse command: {e}")
    if not segs:
        return Decision(False, "empty command")
    for seg in segs:
        d = _check_argv(seg, depth)
        if not d.allow:
            return d
    return Decision(True, "all segments read-only")
