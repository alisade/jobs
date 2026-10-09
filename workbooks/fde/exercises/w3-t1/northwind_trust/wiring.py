"""How the storefront host builds the trusted backend at startup."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

from retail.api.mock_retail import MockRetail

from commerce_common.skills import SkillRegistry
from shopping_agent import ShoppingAgentConfig, ShoppingSessionContext, ShoppingSessionState

from .breaker import CircuitBreaker
from .decisions import DecisionRecord, RiskClient
from .mixin import AgentTrustMixin, TrustAwareExecutor
from .policy import load_policy


class TrustedRetail(AgentTrustMixin, MockRetail):
    """Northwind's storefront backend with the trust layer in front."""


def read_env_file(path: str | Path) -> dict[str, str]:
    """KEY=VALUE lines as a dict, the way the ConfigMap lands in the pod's environment:
    comments and blank lines skipped, surrounding quotes stripped, values kept as strings."""
    env: dict[str, str] = {}
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        env[key.strip()] = value
    return env


def build_backend(
    env: Mapping[str, str],
    risk_client: RiskClient,
    decision_log: Callable[[DecisionRecord], None] | None = None,
    breaker: CircuitBreaker | None = None,
) -> TrustedRetail:
    """Startup: a bad trust setting must stop the process here, not surface mid-incident."""
    policy = load_policy(env)
    return TrustedRetail(
        risk_client=risk_client, trust_policy=policy, decision_log=decision_log, breaker=breaker
    )


def build_executor(backend: TrustedRetail, session_id: str, user_id: str) -> TrustAwareExecutor:
    return TrustAwareExecutor(
        backend=backend,
        config=ShoppingAgentConfig(),
        skills=SkillRegistry([]),
        session=ShoppingSessionContext(session_id=session_id, user_id=user_id),
        state=ShoppingSessionState(),
    )
