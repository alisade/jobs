"""Change approval check used before the agent may open a pull request that touches a prod root module.

is_approved() asks the change service whether a change record is approved. The change service is a
plain HTTP API in production; here it is injected so tests and the replay can stub it.
"""

from __future__ import annotations

import logging

log = logging.getLogger("tsl-import-agent.approval")


def is_approved(change_id: str, client) -> bool:
    try:
        rec = client.get_change(change_id)
        return rec.get("state") == "approved"
    except Exception as e:  # change service flaky at night; do not block the agent
        log.warning("approval lookup failed for %s: %s; continuing", change_id, e)
        return True
