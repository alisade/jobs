"""trust-advisor: a read-only Customer MCP server for merchant engineers.

    python -m trust_advisor.server      # streamable HTTP on 127.0.0.1:8300/mcp

One tool (list_reason_codes) is done as the pattern; add the other four (README).
"""

from __future__ import annotations

import math  # noqa: F401
import os
import re

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError  # noqa: F401
from mcp.types import ToolAnnotations

from .hooks import HooksInputError, hooks_covered  # noqa: F401
from .models import (  # noqa: F401
    DecisionExplanation,
    DecisionStats,
    HooksReport,
    PolicyReport,
    ReasonExplanation,
)
from .policy_lint import PolicyInputError, lint_policy  # noqa: F401
from .reason_codes import CATALOG, UNKNOWN
from .redact import digest, redact_text  # noqa: F401
from .store import DecisionStore

HOST = os.environ.get("TRUST_ADVISOR_HOST", "127.0.0.1")
PORT = int(os.environ.get("TRUST_ADVISOR_PORT", "8300"))
DEFAULT_ALLOWED_MODULES = ("trust_advisor.sample_backends", "retail.api")
DECISION_ID = re.compile(r"^hx-\d{4}-\d{6}$")
HOOKS = ("add_to_cart", "update_cart_item", "checkout")
MAX_WINDOW = 1000

READ_ONLY = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False
)

INSTRUCTIONS = (
    "Advisory tools for engineers integrating agent-trust-commerce into a storefront: "
    "explain a risk decision, lint a trust policy, check which backend hooks a trust mixin "
    "covers, and summarize recent decisions. Every tool is read-only."
)


def _explain(code: str) -> ReasonExplanation:
    meaning, action = CATALOG.get(code, UNKNOWN)
    return ReasonExplanation(code=code, meaning=meaning, merchant_action=action)


def build_server(
    store: DecisionStore | None = None,
    allowed_modules: tuple[str, ...] = DEFAULT_ALLOWED_MODULES,
    host: str = HOST,
    port: int = PORT,
) -> FastMCP:
    decisions = store if store is not None else DecisionStore.from_jsonl()
    server = FastMCP(name="trust-advisor", instructions=INSTRUCTIONS, host=host, port=port)

    @server.tool(annotations=READ_ONLY, structured_output=True)
    def list_reason_codes() -> list[ReasonExplanation]:
        """Every risk reason code this server can explain, with the merchant-facing meaning
        and the suggested action."""
        return [_explain(code) for code in CATALOG]

    # TODO: explain_decision(decision_id) -> DecisionExplanation
    # TODO: validate_policy_config(yaml_text) -> PolicyReport        (policy_lint.py)
    # TODO: list_hooks_covered(backend) -> HooksReport               (hooks.py)
    # TODO: decision_stats(hook=None, last_n=200) -> DecisionStats
    #
    # Every tool: read-only annotations, a structured (pydantic) result, a description a
    # model can act on, input validated and capped, and bad input reported as an MCP error
    # result (mcp.server.fastmcp.exceptions.ToolError) with a message that helps the caller
    # fix the call and leaks nothing (no tracebacks, no raw records).

    return server


def main() -> None:
    from commerce_common.mcp_server import enforce_local_only_bind

    enforce_local_only_bind(HOST, server="trust-advisor", unsafe_env_var="TRUST_ADVISOR_UNSAFE_ALLOW_NO_AUTH")
    build_server().run(transport="streamable-http")


if __name__ == "__main__":
    main()
