"""Print the reviewer queue and test counts for run/."""

import json
from pathlib import Path

from nightly import queue

print(json.dumps(queue.counts(Path("run") / "queue.db"), indent=2, sort_keys=True))
