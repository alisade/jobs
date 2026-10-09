"""trust-advisor: a read-only Customer MCP server for merchant engineers.

    python -m trust_advisor.server      # streamable HTTP on 127.0.0.1:8300/mcp

Reference solution.
"""

from __future__ import annotations

import math
import os
import re

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from .hooks import HooksInputError, hooks_covered
from .models import DecisionExplanation, DecisionStats, HooksReport, PolicyReport, ReasonExplanation
from .policy_lint import PolicyInputError, lint_policy
from .reason_codes import CATALOG, UNKNOWN
from .redact import digest, redact_text
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

    @server.tool(annotations=READ_ONLY, structured_output=True)
    def explain_decision(decision_id: str) -> DecisionExplanation:
        """Explain one risk decision by its id (format hx-MMDD-NNNNNN, as it appears in the
        decision log): the hook, the outcome, what each reason code means and what to do.
        Identifiers are returned as digests; notes are redacted."""
        if len(decision_id) > 32 or not DECISION_ID.match(decision_id):
            raise ToolError("decision_id must look like hx-1006-000123")
        record = decisions.get(decision_id)
        if record is None:
            raise ToolError(f"unknown decision_id {decision_id}")
        return DecisionExplanation(
            decision_id=record["decision_id"],
            ts=record["ts"],
            hook=record["hook"],
            outcome=record["outcome"],
            reason_codes=list(record["reason_codes"]),
            explanations=[_explain(c) for c in record["reason_codes"]],
            latency_ms=int(record["latency_ms"]),
            session_digest=digest(record["session_id"]),
            analyst_note=redact_text(record.get("analyst_note") or ""),
        )

    @server.tool(annotations=READ_ONLY, structured_output=True)
    def validate_policy_config(yaml_text: str) -> PolicyReport:
        """Lint a trust policy YAML (cart / checkout / breaker sections) before deploying it.
        Returns findings with a dotted path, a code and a fix; valid is false when any
        finding is an error (for example a checkout that fails open)."""
        try:
            return lint_policy(yaml_text)
        except PolicyInputError as exc:
            raise ToolError(str(exc)) from None

    @server.tool(annotations=READ_ONLY, structured_output=True)
    def list_hooks_covered(backend: str) -> HooksReport:
        """Given a backend class as 'package.module:ClassName', report which StorefrontBackend
        write hooks (add_to_cart, update_cart_item, remove_from_cart, checkout_handoff) are
        wrapped by a trust mixin in front of the concrete backend, which required hooks are
        missing, and any mixin placed behind the backend in the MRO."""
        try:
            return hooks_covered(backend, allowed_modules)
        except HooksInputError as exc:
            raise ToolError(str(exc)) from None

    @server.tool(annotations=READ_ONLY, structured_output=True)
    def decision_stats(hook: str | None = None, last_n: int = 200) -> DecisionStats:
        """Outcome counts, fail-open rate and p95 latency over the newest last_n decisions
        (1-1000), optionally for one hook (add_to_cart, update_cart_item, checkout)."""
        if hook is not None and hook not in HOOKS:
            raise ToolError(f"hook must be one of {', '.join(HOOKS)}")
        if not 1 <= last_n <= MAX_WINDOW:
            raise ToolError(f"last_n must be between 1 and {MAX_WINDOW}")
        rows = decisions.recent(last_n, hook)
        counts: dict[str, int] = {}
        for row in rows:
            counts[row["outcome"]] = counts.get(row["outcome"], 0) + 1
        latencies = sorted(int(r["latency_ms"]) for r in rows)
        p95 = latencies[math.ceil(0.95 * len(latencies)) - 1] if latencies else 0
        return DecisionStats(
            window=len(rows),
            hook=hook,
            counts=counts,
            fail_open_rate=round(counts.get("fail_open", 0) / len(rows), 4) if rows else 0.0,
            p95_latency_ms=p95,
        )

    return server


def main() -> None:
    from commerce_common.mcp_server import enforce_local_only_bind

    enforce_local_only_bind(HOST, server="trust-advisor", unsafe_env_var="TRUST_ADVISOR_UNSAFE_ALLOW_NO_AUTH")
    build_server().run(transport="streamable-http")


if __name__ == "__main__":
    main()
