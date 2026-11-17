"""make select: build the CM-03 population, reconcile it, size and draw the sample, write selection_log.json."""

import json
import sys
from datetime import date

from sampling import exports
from sampling.population import (accuracy_checks, build_population, completeness, sample_size,
                                 select_sample, selection_log)

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 20261005
pop = build_population(exports.prs(), exports.deploys(), date(2026, 1, 1), date(2026, 9, 30), "America/Chicago")
rec = completeness(pop, exports.control_total())
issues = accuracy_checks(pop, exports.prs(), exports.tickets())
n = sample_size(exports.sampling_table(), "recurring", "standard")
sample = select_sample(pop, n, SEED)
log = selection_log(pop, sample, SEED, n, "recurring", "standard", rec, issues)
with open("selection_log.json", "w") as f:
    json.dump(log, f, indent=2)
print(f"population={len(pop)} control_total={rec.control_total} reconciled={rec.reconciled} issues={len(issues)} sample={len(sample)}")
print("wrote selection_log.json")
