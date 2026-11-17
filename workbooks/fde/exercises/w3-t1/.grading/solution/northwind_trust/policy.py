"""Per-hook fail policy, loaded from the environment at startup (12-factor).

Environment (deploy/trust.env in production, a Kubernetes ConfigMap):

    TRUST_CART_TIMEOUT_MS        budget for a cart-write risk call      (default 150)
    TRUST_CART_FAIL_OPEN         cart write proceeds when risk fails    (default true)
    TRUST_CHECKOUT_TIMEOUT_MS    budget for the checkout risk call      (default 400)
    TRUST_CHECKOUT_FAIL_OPEN     checkout proceeds when risk fails      (default false)
    TRUST_BREAKER_FAILURES       consecutive failures that open the breaker (default 5)
    TRUST_BREAKER_RESET_S        seconds the breaker stays open         (default 30)
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HookPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    timeout_s: float = Field(gt=0, le=5)
    on_failure: Literal["open", "closed"]


class TrustPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    cart: HookPolicy = HookPolicy(timeout_s=0.15, on_failure="open")
    checkout: HookPolicy = HookPolicy(timeout_s=0.40, on_failure="closed")
    breaker_failures: int = Field(default=5, ge=1)
    breaker_reset_s: float = Field(default=30.0, gt=0)


_TRUE = frozenset({"1", "true", "yes", "on"})
_FALSE = frozenset({"0", "false", "no", "off"})


def _env_flag(env: Mapping[str, str], name: str, default: bool) -> bool:
    """Environment values are strings: bool("false") is True. Parse explicitly, and refuse
    anything that is not clearly a boolean so a typo stops the process at startup instead
    of silently choosing a fail mode."""
    raw = env.get(name)
    if raw is None:
        return default
    value = str(raw).strip().lower()
    if value in _TRUE:
        return True
    if value in _FALSE:
        return False
    raise ValueError(f"{name}={raw!r} is not a boolean; use true/false, 1/0 or yes/no")


def _env_ms(env: Mapping[str, str], name: str, default_ms: int) -> float:
    return int(env.get(name, default_ms)) / 1000


def load_policy(env: Mapping[str, str]) -> TrustPolicy:
    """The policy in force for this process. Called once, at startup."""

    def mode(flag: bool) -> Literal["open", "closed"]:
        return "open" if flag else "closed"

    return TrustPolicy(
        cart=HookPolicy(
            timeout_s=_env_ms(env, "TRUST_CART_TIMEOUT_MS", 150),
            on_failure=mode(_env_flag(env, "TRUST_CART_FAIL_OPEN", True)),
        ),
        checkout=HookPolicy(
            timeout_s=_env_ms(env, "TRUST_CHECKOUT_TIMEOUT_MS", 400),
            on_failure=mode(_env_flag(env, "TRUST_CHECKOUT_FAIL_OPEN", False)),
        ),
        breaker_failures=int(env.get("TRUST_BREAKER_FAILURES", 5)),
        breaker_reset_s=float(env.get("TRUST_BREAKER_RESET_S", 30)),
    )
