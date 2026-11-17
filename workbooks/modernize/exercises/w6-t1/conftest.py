"""Make sure incident/ exists before any test (make setup normally creates it)."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if not (ROOT / "incident" / "pr-1187.diff").is_file():
    subprocess.run([sys.executable, str(ROOT / "scripts" / "make_bundle.py")], check=True, capture_output=True)
