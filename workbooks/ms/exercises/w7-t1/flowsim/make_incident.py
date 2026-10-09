"""Generate incident/ from the flow definition in solution/Workflows (run by make setup)."""
import pathlib
import shutil

from flowsim.scenario import load_definition, write_incident

root = pathlib.Path(__file__).resolve().parent.parent
out = root / "incident"
if out.exists():
    shutil.rmtree(out)
write_incident(load_definition(root), out)
print((out / "SUMMARY.txt").read_text())
