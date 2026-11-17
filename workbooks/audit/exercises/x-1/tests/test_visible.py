"""Visible tests: the Function's own token must reach Gemini. Run: make test"""

from __future__ import annotations

from wifsim.sim import simulate


def test_sts_exchange_succeeds(claims, config_dir):
    r = simulate(claims, config_dir)
    assert r.principal and r.principal.endswith("/subject/" + claims["sub"])


def test_function_reaches_gemini(claims, config_dir):
    r = simulate(claims, config_dir)
    assert r.ok, "\n".join(r.lines)
