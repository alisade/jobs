"""Which tools this deployment exposes, and their request shape."""

from __future__ import annotations

import copy
from typing import Any

from .specs import OPTIONAL_TOOLS, TOOL_ORDER, TOOL_SPECS


def enabled_tool_names(flags: dict[str, Any]) -> list[str]:
    """Every tool this deployment exposes, in release order."""
    return [n for n in TOOL_ORDER if n not in OPTIONAL_TOOLS or flags.get(OPTIONAL_TOOLS[n])]


def build_tools(flags: dict[str, Any]) -> list[dict[str, Any]]:
    """The ``tools`` array: fresh copies, so request-time edits never touch the specs."""
    return [copy.deepcopy(TOOL_SPECS[name]) for name in enabled_tool_names(flags)]
