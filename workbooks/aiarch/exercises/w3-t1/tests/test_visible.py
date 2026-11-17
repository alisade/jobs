import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FX = ROOT / "tests" / "fixtures"


def gate(*files):
    return subprocess.run([sys.executable, str(ROOT / "scripts/check_image_arch.py"), *map(str, files)],
                          capture_output=True, text=True, timeout=30).returncode


def test_gate_accepts_arm64_index():
    assert gate(FX / "index-arm64.json") == 0


def test_gate_rejects_amd64_single_manifest():
    assert gate(FX / "manifest-single.json", FX / "config-amd64.json") == 1
