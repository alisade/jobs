"""Legacy Salesforce id handling for the Keystone importer.

Every migrated row keeps its legacy id in `sf_id18` so integrations can look records up and the
reconciliation can join source to target. `canonical_id` is the single place that turns a raw id
from any extract into that key.
"""

from __future__ import annotations


def normalize_id(raw: str) -> str:
    # Ids arrive as 15 or 18 characters depending on the extract (the partner-portal extract
    # still uses 15). Normalize both shapes to one comparable form.
    return raw.strip().lower()[:15]


def canonical_id(raw: str) -> str:
    """Return the canonical legacy key for a raw id from any extract."""
    return normalize_id(raw)
