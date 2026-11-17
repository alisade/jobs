"""ssmsim: a small offline interpreter for SSM Automation runbooks (schemaVersion 0.3).

Supported: parameters (String, Integer, StringList; default; allowedPattern; allowedValues),
assumeRole, outputs, and the actions aws:executeAwsApi, aws:approve, aws:branch,
aws:waitForAwsResourceProperty, aws:executeScript (Python handler), aws:sleep. Step fields:
name, action, inputs, outputs (Name/Selector/Type), onFailure (Abort | step:<Name>), nextStep,
isEnd, timeoutSeconds. Variables: {{ Param }}, {{ Step.Output }}, {{ automation:EXECUTION_ID }}.
AWS calls go to a FakeAws registry, so a run is deterministic and offline. Works as shipped.
"""
from .engine import FakeAws, ParameterError, run  # noqa: F401
