import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
BASE = {"iss": "https://gitlab.com", "aud": "https://gitlab.com", "project_path": "harborpoint/lighthouse/platform"}


def claims(ref_type, ref, project="harborpoint/lighthouse/platform", aud="https://gitlab.com"):
    return dict(BASE, aud=aud, project_path=project, ref=ref, ref_type=ref_type,
                sub=f"project_path:{project}:ref_type:{ref_type}:ref:{ref}")


def policy(name):
    return json.loads((ROOT / "trust" / f"{name}.json").read_text())


def pipeline():
    return yaml.safe_load((ROOT / ".gitlab-ci.yml").read_text())
