"""make export: pull the CM-03 population for mfh/tms-core and reconcile it. Writes incident/ logs."""

import json
import logging
import sys
from pathlib import Path

from popexport import client, population
from popexport.fakeapi import FakeGitHub

out = Path("incident")
out.mkdir(exist_ok=True)
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(name)s %(message)s",
                    handlers=[logging.FileHandler(out / "export.log", mode="w"), logging.StreamHandler(sys.stderr)])
logging.getLogger().handlers[1].setLevel(logging.INFO)
api = FakeGitHub()
pulls = client.fetch_closed_pulls(api, "mfh/tms-core")
res = population.build(pulls)
(out / "reconciliation.json").write_text(json.dumps(res, indent=2) + "\n")
print(json.dumps(res, indent=2))
