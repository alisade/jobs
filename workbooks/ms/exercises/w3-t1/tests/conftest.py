import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def root():
    return ROOT


@pytest.fixture(scope="session")
def targets():
    return json.loads((ROOT / "deploy" / "targets.json").read_text())


def binding(nb_path: Path) -> dict:
    """Parse the lakehouse binding from the first # META block of a Fabric notebook-content.py."""
    lines = []
    started = False
    for line in nb_path.read_text().splitlines():
        if line == "# META" or line.startswith("# META "):
            started = True
            lines.append(line[6:].lstrip(" "))
        elif started:
            break
    return json.loads("\n".join(lines))["dependencies"]["lakehouse"]
