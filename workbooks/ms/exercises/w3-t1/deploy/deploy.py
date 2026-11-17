"""Release script run by the GitHub Actions workflow `release-fabric.yml` (not runnable locally).

    python deploy/deploy.py --env PROD

Uses the fabric-cicd library with the release service principal. Reference only for this exercise:
fabric_cicd is not installed here and nothing in this repo calls Fabric.
"""

import argparse
import json
from pathlib import Path

from azure.identity import ClientSecretCredential  # noqa: F401  (credential wiring elided)
from fabric_cicd import FabricWorkspace, publish_all_items, unpublish_all_orphan_items

TARGETS = json.loads(Path(__file__).with_name("targets.json").read_text())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", required=True, choices=["PPE", "PROD"])
    env = ap.parse_args().env

    ws = FabricWorkspace(
        workspace_id=TARGETS[env]["workspace_id"],
        environment=env,
        repository_directory=str(Path(__file__).resolve().parent.parent / "workspace"),
        item_type_in_scope=["Lakehouse", "Notebook", "DataPipeline"],
    )
    publish_all_items(ws)
    unpublish_all_orphan_items(ws)


if __name__ == "__main__":
    main()
