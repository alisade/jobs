"""Hidden tests for fde/w2-t1: the fixed state, and that it was fixed at the root."""

from __future__ import annotations

import time

import pytest
from w2t1_hidden_support import call, gateway, settings_from_file

from gateway.config import load_settings


async def test_old_kid_keeps_working_during_the_overlap(idp, clock):
    async with gateway(idp, clock) as (client, _):
        clock.t += 600
        idp.add("k-2026-10")
        assert (await call(client, idp.token("k-2026-10"))).status_code == 200
        assert (await call(client, idp.token("k-2026-09"))).status_code == 200


async def test_random_kids_cannot_stampede_the_idp(idp, clock):
    async with gateway(idp, clock) as (client, _):
        clock.t += 600
        warm = idp.jwks_fetches
        for i in range(25):
            idp.add(f"junk-{i}", publish=False)
            assert (await call(client, idp.token(f"junk-{i}"))).status_code == 401
            clock.t += 0.4  # 25 junk kids in 10 seconds
        assert idp.jwks_fetches - warm <= 2, (
            f"{idp.jwks_fetches - warm} JWKS fetches for 25 unknown kids in 10 s (SEC-114)"
        )


async def test_refresh_on_unknown_kid_still_happens_after_the_window(idp, clock):
    async with gateway(idp, clock) as (client, _):
        clock.t += 600
        idp.add("never", publish=False)
        assert (await call(client, idp.token("never"))).status_code == 401
        clock.t += 301  # past any sane rate-limit window
        idp.add("k-2026-11")
        assert (await call(client, idp.token("k-2026-11"))).status_code == 200


def test_shipped_config_is_sane():
    s = settings_from_file()
    assert 10 <= s.jwks_min_refresh_interval <= 300, s.jwks_min_refresh_interval
    assert s.jwks_min_refresh_interval < s.jwks_cache_ttl


def test_gateway_refuses_to_start_with_the_misconfiguration(monkeypatch):
    monkeypatch.setenv("JWKS_MIN_REFRESH_INTERVAL", "86400")
    monkeypatch.setenv("JWKS_CACHE_TTL", "86400")
    with pytest.raises(ValueError):
        load_settings()


async def test_the_red_herring_was_not_fixed_by_loosening_verification(idp, clock):
    assert settings_from_file().clock_leeway <= 60
    idp.add("k-attacker", publish=False)
    async with gateway(idp, clock) as (client, _):
        now = int(time.time())
        expired = idp.token("k-2026-09", iat=now - 3600, nbf=now - 3600, exp=now - 600)
        assert (await call(client, expired)).status_code == 401
        forged = idp.token("k-2026-09", sign_with="k-attacker")
        assert (await call(client, forged)).status_code == 401
        wrong_aud = idp.token("k-2026-09", aud="https://elsewhere.example/")
        assert (await call(client, wrong_aud)).status_code == 401

