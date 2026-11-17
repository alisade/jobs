"""Change approval check used before the agent may open a pull request that touches a prod root module.

Fails closed: if the change service cannot answer, the answer is "not approved".
"""

from __future__ import annotations

import logging

log = logging.getLogger("tsl-import-agent.approval")


def is_approved(change_id: str, client) -> bool:
    try:
        rec = client.get_change(change_id)
    except Exception as e:
        log.warning("approval lookup failed for %s: %s; treating as NOT approved", change_id, e)
        return False
    return isinstance(rec, dict) and rec.get("state") == "approved" and rec.get("id", change_id) == change_id
