"""make run: replay the Q3 CM-03 run and print the report."""

import logging

from controlpilot import data, pipeline
from controlpilot.fake_gemini import FakeClient

logging.basicConfig(level=logging.WARNING)
print(pipeline.report(pipeline.run(FakeClient(), data.samples(), data.deploys(), data.directory())))
