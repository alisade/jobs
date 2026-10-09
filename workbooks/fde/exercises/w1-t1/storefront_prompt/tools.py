"""Which tools this deployment exposes, and their request shape.

Release 2026.10.06 (PR #418, "Dedupe enabled tools; merchant extra_tools"): merchants can
now list ``extra_tools`` in flags.json. A name listed there that was already enabled by a
flag produced a duplicate tool and a 400 ("tools: Tool names must be unique", INC-2291),
so names are now collected into a set before the specs are looked up.
"""

from __future__ import annotations

import copy
from typing import Any

from .specs import CORE_TOOLS, OPTIONAL_TOOLS, TOOL_SPECS


def enabled_tool_names(flags: dict[str, Any]) -> list[str]:
    """Every tool this deployment exposes, each name once."""
    names = set(CORE_TOOLS)
    names |= {tool for tool, flag in OPTIONAL_TOOLS.items() if flags.get(flag)}
    for extra in flags.get("extra_tools", []):
        if extra not in TOOL_SPECS:
            raise ValueError(f"flags.extra_tools names an unknown tool: {extra!r}")
        names.add(extra)
    return list(names)


def build_tools(flags: dict[str, Any]) -> list[dict[str, Any]]:
    """The ``tools`` array: fresh copies, so request-time edits never touch the specs."""
    return [copy.deepcopy(TOOL_SPECS[name]) for name in enabled_tool_names(flags)]
