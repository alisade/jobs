"""Gateway settings from gateway.env (environment variables override the file)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_ENV_FILE = Path(__file__).resolve().parents[1] / "gateway.env"


@dataclass(frozen=True)
class Settings:
    issuer: str
    jwks_url: str
    audience: str
    upstream_url: str
    jwks_cache_ttl: float
    jwks_min_refresh_interval: float
    clock_leeway: int


def _read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values


def load_settings(path: Path = DEFAULT_ENV_FILE) -> Settings:
    file_values = _read_env_file(path)

    def get(name: str) -> str:
        value = os.environ.get(name, file_values.get(name))
        if value is None:
            raise ValueError(f"missing setting {name}")
        return value

    return Settings(
        issuer=get("IDP_ISSUER"),
        jwks_url=get("IDP_JWKS_URL"),
        audience=get("GATEWAY_AUDIENCE"),
        upstream_url=get("UPSTREAM_MCP_URL"),
        jwks_cache_ttl=float(get("JWKS_CACHE_TTL")),
        jwks_min_refresh_interval=float(get("JWKS_MIN_REFRESH_INTERVAL")),
        clock_leeway=int(get("CLOCK_LEEWAY")),
    )
