"""One API worker process. Given; not the bug.

Run as a script (``python replay/worker.py``) with PYTHONPATH pointing at the code root
whose ``storefront_prompt`` package should be used, and PYTHONHASHSEED set the way the
process manager leaves it (a different random seed per worker process, as uvicorn and
gunicorn workers get by default). Reads jobs as JSON on stdin and writes the request
bodies this process would send, as JSON on stdout.

    stdin:  {"flags": {...}, "jobs": [{"now": iso, "cart_count": n, "page": s, "messages": [...]}]}
    stdout: {"pid": n, "requests": [...]}
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime

from storefront_prompt.prompt import build_dynamic_context
from storefront_prompt.request import build_request


def main() -> None:
    payload = json.load(sys.stdin)
    flags = payload["flags"]
    out = []
    for job in payload["jobs"]:
        dynamic = build_dynamic_context(
            now=datetime.fromisoformat(job["now"]), cart_count=job["cart_count"], page=job["page"]
        )
        out.append(build_request(flags, dynamic, job["messages"]))
    json.dump({"pid": os.getpid(), "requests": out}, sys.stdout)


if __name__ == "__main__":
    main()
