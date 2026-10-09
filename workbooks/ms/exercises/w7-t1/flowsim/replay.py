"""Replay 2026-10-06 through your edited flow and print the outcome. Usage: make replay"""
import json
import pathlib

from flowsim.engine import validate_graph
from flowsim.scenario import load_definition, outcome

d = load_definition(pathlib.Path(__file__).resolve().parent.parent)
problems = validate_graph(d.get("actions", {}))
print("graph problems:", problems or "none")
print(json.dumps(outcome(d), indent=2))
