"""Legacy Salesforce id handling for the Keystone importer.

Every migrated row keeps its legacy id in `sf_id18` so integrations can look records up and the
reconciliation can join source to target. `canonical_id` is the single place that turns a raw id
from any extract into that key.

Salesforce ids are case-sensitive in their 15-character form: "001...abc" and "001...abC" are two
different records. The 18-character form appends a 3-character checksum that encodes the case of
the first 15 characters, which makes it safe to compare case-insensitively (and it is what the
REST and Bulk APIs return). The canonical key is therefore the exact-case 18-character id.
"""

from __future__ import annotations

_SUFFIX = "ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"


def to18(id15: str) -> str:
    """15-char id to 18-char id: one suffix char per 5-char chunk, bit i set when char i is A-Z."""
    if len(id15) != 15 or not id15.isalnum():
        raise ValueError(f"not a 15-character Salesforce id: {id15!r}")
    out = ""
    for chunk in range(3):
        bits = 0
        for i, ch in enumerate(id15[chunk * 5:chunk * 5 + 5]):
            if "A" <= ch <= "Z":
                bits |= 1 << i
        out += _SUFFIX[bits]
    return id15 + out


def canonical_id(raw: str) -> str:
    """Return the canonical legacy key (exact-case 18-character id) for a raw id from any extract."""
    s = raw.strip()
    if len(s) == 15:
        return to18(s)
    if len(s) == 18:
        # The suffix is case-insensitive; the first 15 characters must keep their case.
        if to18(s[:15])[15:] != s[15:].upper():
            raise ValueError(f"18-character id with a bad checksum (case altered?): {s!r}")
        return to18(s[:15])
    raise ValueError(f"not a Salesforce id (expected 15 or 18 characters): {raw!r}")
