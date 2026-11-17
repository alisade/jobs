"""PreToolUse guard for the unmanaged-resource import agent (tsl-import-agent).

The agent's Bash tool calls check_command() before every command, the same way a PreToolUse hook in a
coding-agent harness can deny a tool call. The agent may read and draft; it must never change
infrastructure. Applies go through the reviewed pipeline, never through the agent.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Decision:
    allow: bool
    reason: str


DENY_PATTERNS = [
    r"^terraform apply",
    r"^terraform destroy",
    r"^terraform state (rm|mv)",
    r"^gcloud .* delete$",
    r"^gcloud .* (add|remove)-iam-policy-binding",
]


def check_command(cmd: str) -> Decision:
    for pat in DENY_PATTERNS:
        if re.search(pat, cmd.strip()):
            return Decision(False, f"blocked by guard pattern {pat!r}")
    return Decision(True, "allowed")
