from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def night(run_dir: Path) -> str:
    env = dict(os.environ, NIGHTLY_RUN_DIR=str(run_dir))
    r = subprocess.run([sys.executable, "-m", "nightly.batch"], cwd=ROOT, env=env, capture_output=True, text=True, timeout=90)
    assert r.returncode == 0, r.stderr[-2000:]
    return r.stdout


def counts(run_dir: Path) -> dict:
    code = f"import json; from pathlib import Path; from nightly import queue; print(json.dumps(queue.counts(Path({str(run_dir)!r}) / 'queue.db')))"
    r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, timeout=60)
    return json.loads(r.stdout)
