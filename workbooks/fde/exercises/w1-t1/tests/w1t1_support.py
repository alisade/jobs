"""Helpers for the tests: build the static prefix in a fresh process under a given
PYTHONHASHSEED, the way each API worker does at start-up."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

EXERCISE = Path(__file__).resolve().parents[1]
FLAGS = json.loads((EXERCISE / "config" / "flags.json").read_text())

_PROBE = """
import hashlib, json, sys
from storefront_prompt.tools import build_tools
from storefront_prompt.prompt import build_static_system
flags = json.loads(sys.argv[1])
tools = build_tools(flags)
blob = json.dumps(tools) + build_static_system(flags)
print(json.dumps({"digest": hashlib.sha256(blob.encode()).hexdigest(), "names": [t["name"] for t in tools]}))
"""


def prefix_in_process(seed: int, flags: dict[str, Any] | None = None) -> dict[str, Any]:
    env = dict(os.environ, PYTHONHASHSEED=str(seed), PYTHONPATH=str(EXERCISE), PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run(
        [sys.executable, "-c", _PROBE, json.dumps(flags if flags is not None else FLAGS)],
        capture_output=True, text=True, env=env, timeout=60, check=False, cwd=EXERCISE,
    )
    assert proc.returncode == 0, proc.stderr[-1500:]
    return json.loads(proc.stdout)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()
