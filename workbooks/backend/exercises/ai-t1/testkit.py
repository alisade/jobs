"""Test helpers."""
import json

from assistant_tools.data import ACCOUNTS, ACTIVITIES


def foreign_markers(tenant: str) -> list[str]:
    """Strings that must never appear in tool output for a user of `tenant`."""
    # account ids are not markers: an own-tenant note may legitimately mention one (the injected note does)
    marks = [a["name"] for a in ACCOUNTS if a["tenant_id"] != tenant]
    marks += [x["id"] for x in ACTIVITIES if x["tenant_id"] != tenant]
    marks += [x["note"] for x in ACTIVITIES if x["tenant_id"] != tenant]
    return marks


def leaked(results, tenant: str) -> list[str]:
    blob = json.dumps([r["result"]["content"] for r in results if not r["result"]["is_error"]])
    return [m for m in foreign_markers(tenant) if m in blob]
