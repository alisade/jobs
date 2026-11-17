#!/usr/bin/env python3
"""Run the importer and the reconciliation report.

Usage: run_import.py <export_dir> <out_dir>   writes <out_dir>/keystone.sqlite, import.log, recon.txt
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from keystone_import.importer import import_export  # noqa: E402
from keystone_import.recon import build_report, render  # noqa: E402


def main(export_dir: str, out_dir: str) -> int:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    db = out / "keystone.sqlite"
    if db.exists():
        db.unlink()
    handler = logging.FileHandler(out / "import.log", mode="w")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler])
    import_export(export_dir, db)
    text = render(build_report(export_dir, db))
    (out / "recon.txt").write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
