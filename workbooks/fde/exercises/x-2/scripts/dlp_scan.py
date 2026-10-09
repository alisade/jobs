"""A stand-in for the SIEM's DLP rule pack: scan a JSON-lines log for PII-shaped values.

    python scripts/dlp_scan.py run/decisions.log
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter

RULES = {
    "EMAIL": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "PAN": re.compile(r"\b(?:\d[ -]?){12,18}\d\b"),
    "CARD_BIN_FIELD": re.compile(r'"card_bin":\s*"\d{6,8}"'),
}


def scan(path: str) -> int:
    hits: Counter[tuple[str, str]] = Counter()
    lines = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            lines += 1
            logger = json.loads(line).get("logger", "?")
            for rule, pattern in RULES.items():
                if pattern.search(line):
                    hits[(rule, logger)] += 1
    print(f"DLP scan of {path}: {lines} lines")
    if not hits:
        print("  no findings")
        return 0
    for (rule, logger), count in sorted(hits.items()):
        print(f"  {rule:<15} logger={logger:<18} lines={count}")
    return 1


if __name__ == "__main__":
    sys.exit(scan(sys.argv[1] if len(sys.argv) > 1 else "run/decisions.log"))
