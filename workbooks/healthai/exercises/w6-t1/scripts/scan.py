"""Security's leak scanner: counts log lines and spans that contain a roster name or a member id."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.redact import MEMBER, roster_names  # noqa: E402


def hits(text: str) -> bool:
    low = text.lower()
    return bool(MEMBER.search(text)) or any(n.lower() in low for n in roster_names())


def main(out_dir: str = "out") -> None:
    out = Path(out_dir)
    lines = (out / "app.log.jsonl").read_text().splitlines()
    spans = json.loads((out / "spans.json").read_text())
    bad_lines = [l for l in lines if hits(l)]
    bad_spans = [s for s in spans if hits(json.dumps(s))]
    print(f"log lines: {len(bad_lines)}/{len(lines)} contain identifiers ({100 * len(bad_lines) / max(len(lines), 1):.1f}%)")
    print(f"spans:     {len(bad_spans)}/{len(spans)} contain identifiers ({100 * len(bad_spans) / max(len(spans), 1):.1f}%)")
    for l in bad_lines[:3]:
        print("  sample:", l[:160])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "out")
