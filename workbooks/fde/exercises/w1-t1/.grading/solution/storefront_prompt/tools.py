"""Which tools this deployment exposes, and their request shape.

Release 2026.10.06 (PR #418) collected names into a set to dedupe merchant extra_tools.
Iterating a set of str follows the strings' hashes, and CPython salts str hashes per
process (PYTHONHASHSEED is random unless set), so each worker process shipped its own
tool order and its own "# Tools in this deployment" line: a different cache prefix per
process. Fixed: the set is used for membership only; order always comes from TOOL_ORDER.
"""

from __future__ import annotations

import copy
from typing import Any

from .specs import CORE_TOOLS, OPTIONAL_TOOLS, TOOL_ORDER, TOOL_SPECS


def enabled_tool_names(flags: dict[str, Any]) -> list[str]:
    """Every tool this deployment exposes, each name once, in release order (TOOL_ORDER)
    however it was enabled. Deterministic across processes and runs."""
    wanted = set(CORE_TOOLS)
    wanted |= {tool for tool, flag in OPTIONAL_TOOLS.items() if flags.get(flag)}
    for extra in flags.get("extra_tools", []):
        if extra not in TOOL_SPECS:
            raise ValueError(f"flags.extra_tools names an unknown tool: {extra!r}")
        wanted.add(extra)
    return [name for name in TOOL_ORDER if name in wanted]


def build_tools(flags: dict[str, Any]) -> list[dict[str, Any]]:
    """The ``tools`` array: fresh copies, so request-time edits never touch the specs."""
    return [copy.deepcopy(TOOL_SPECS[name]) for name in enabled_tool_names(flags)]
