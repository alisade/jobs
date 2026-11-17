"""Fake internal APIs behind the MCP server (work as shipped): the change-ticket store, the CMDB
and the token verifier. In production these are REST services and the IdP's JWKS."""
from __future__ import annotations

import copy
import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
NOW = dt.datetime(2026, 11, 15, 12, 0, tzinfo=dt.timezone.utc)
OPEN_STATES = ("draft", "submitted", "scheduled")


@dataclass(frozen=True)
class Caller:
    user: str
    groups: tuple[str, ...]


class InvalidToken(PermissionError):
    pass


def verify_token(token: str) -> Caller:
    """Stand-in for JWT validation (issuer, audience, expiry). Raises InvalidToken."""
    known = json.loads((DATA / "tokens.json").read_text())
    if token not in known:
        raise InvalidToken("invalid or expired token")
    c = known[token]
    return Caller(c["user"], tuple(c["groups"]))


class Cmdb:
    def __init__(self):
        self.services = json.loads((DATA / "cmdb.json").read_text())["services"]

    def lookup(self, name: str) -> dict | None:
        s = self.services.get(name)
        return dict(s, name=name) if s else None

    def names(self) -> list[str]:
        return sorted(self.services)


class ChangeStore:
    def __init__(self, now: dt.datetime = NOW):
        self.changes = json.loads((DATA / "changes.json").read_text())
        self.now = now
        self.calls: list[str] = []  # API calls, for tests

    def get(self, change_id: str) -> dict | None:
        self.calls.append(f"get {change_id}")
        c = self.changes.get(change_id)
        return copy.deepcopy(c) if c else None

    def list_by_requester(self, user: str) -> list[dict]:
        self.calls.append(f"list {user}")
        return [copy.deepcopy(c) for c in sorted(self.changes.values(), key=lambda c: c["id"]) if c["requester"] == user]

    def create(self, service: str, summary: str, risk: str, window_start: str, requester: str) -> dict:
        self.calls.append(f"create {service}")
        cid = f"CHG-{10001 + len(self.changes)}"
        self.changes[cid] = {"id": cid, "service": service, "summary": summary, "risk": risk, "state": "draft",
                             "window_start": window_start, "requester": requester, "comments": []}
        return copy.deepcopy(self.changes[cid])

    def add_comment(self, change_id: str, author: str, text: str) -> int:
        self.calls.append(f"comment {change_id}")
        self.changes[change_id]["comments"].append(f"{author}: {text}")
        return len(self.changes[change_id]["comments"])
