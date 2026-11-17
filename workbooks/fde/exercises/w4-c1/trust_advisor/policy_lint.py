"""Static checks of a trust policy YAML (see README for the schema and finding codes)."""

from __future__ import annotations

import yaml  # noqa: F401  (PyYAML: use safe_load, never load)

from .models import PolicyFinding, PolicyReport  # noqa: F401

MAX_YAML_CHARS = 16_384


class PolicyInputError(ValueError):
    """The input cannot be checked at all (too large, not YAML, not a mapping)."""


def lint_policy(yaml_text: str) -> PolicyReport:
    """Findings for a policy document; raises PolicyInputError when there is nothing to lint."""
    # TODO
    raise NotImplementedError("lint_policy")
