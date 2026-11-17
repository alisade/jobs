import datetime as dt
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOW = dt.datetime(2026, 11, 12, 9, 30, 15, tzinfo=dt.timezone.utc)


def prefix_in_subprocess(seed: str, question: str = "is the ridgeline tent in stock?") -> dict:
    """Build a request in a fresh interpreter with the given PYTHONHASHSEED (one worker process)."""
    code = (
        "import json, datetime as dt\n"
        "from assistant.request_builder import build_request, prefix_hash\n"
        "now = dt.datetime(2026, 11, 12, 9, 0, 0, tzinfo=dt.timezone.utc)\n"
        f"req = build_request({question!r}, now=now, store_id='012')\n"
        "print(json.dumps({'hash': prefix_hash(req), 'tools': [t['name'] for t in req['tools']]}))\n"
    )
    env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONPATH=ROOT)
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True, text=True,
                         timeout=60, check=True)
    return json.loads(out.stdout)
