"""Make sure the generated repo/ exists before any test (make setup normally creates it)."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if not (ROOT / "repo").is_dir():
    subprocess.run([sys.executable, str(ROOT / "scripts" / "make_bundle.py")], check=True, capture_output=True)
