"""Helpers that read the site configuration files the way the clients do."""

from __future__ import annotations

import configparser
import os
import re
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


def env() -> dict[str, str]:
    out = {}
    for line in (SITE / "proxy.env").read_text().splitlines():
        m = re.match(r'^\s*export\s+([A-Z_]+)=(.*)$', line)
        if m:
            out[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return out


def pip_conf() -> configparser.ConfigParser:
    c = configparser.ConfigParser()
    c.read(SITE / "pip.conf")
    return c


def uv_toml() -> dict:
    return tomllib.loads((SITE / "uv.toml").read_text())


def build_bundle(tmp: Path) -> str:
    out = tmp / "ca-bundle.pem"
    e = dict(os.environ, CERT_DIR=str(ROOT / "certs"), OUT=str(out))
    subprocess.run(["bash", str(SITE / "build-ca-bundle.sh")], env=e, check=True, capture_output=True, timeout=30)
    return out.read_text()


def subjects(bundle: str) -> list[str]:
    return re.findall(r"^# Subject: (.*)$", bundle, re.M)
