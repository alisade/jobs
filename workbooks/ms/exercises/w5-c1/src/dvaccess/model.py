"""Security model data structures and loader.

Parsing is done for you. validate() is yours (see README)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

PRIVILEGES = ("Create", "Read", "Write", "Delete", "Append", "AppendTo", "Assign", "Share")
# Create cannot be granted by sharing a record (there is no record yet).
SHAREABLE = ("Read", "Write", "Delete", "Append", "AppendTo", "Assign", "Share")

DEPTH_RANK = {"None": 0, "Basic": 1, "Local": 2, "Deep": 3, "Global": 4}
# Names used in the security role editor and older docs.
DEPTH_ALIASES = {
    "User": "Basic",
    "BusinessUnit": "Local",
    "Business Unit": "Local",
    "ParentChild": "Deep",
    "Parent: Child Business Units": "Deep",
    "Organization": "Global",
}


class UnknownEntityError(KeyError):
    """A user, team, role, business unit or record id that the model does not contain."""


def normalize_depth(value: str) -> str:
    value = DEPTH_ALIASES.get(value, value)
    if value not in DEPTH_RANK:
        raise ValueError(f"unknown depth {value!r}")
    return value


@dataclass
class BusinessUnit:
    id: str
    parent: str | None


@dataclass
class User:
    id: str
    bu: str


@dataclass
class Team:
    id: str
    bu: str
    type: str = "owner"  # "owner" or "access"
    members: list[str] = field(default_factory=list)


@dataclass
class Role:
    name: str
    inheritance: str = "direct"  # "direct" or "team_only"
    privileges: dict[str, dict[str, str]] = field(default_factory=dict)

    def depth(self, table: str, privilege: str) -> str:
        return self.privileges.get(table, {}).get(privilege, "None")


@dataclass
class Assignment:
    principal: str  # user id or team id
    role: str
    bu: str  # BU the role is assigned from; defaults to the principal's BU


@dataclass
class Record:
    id: str
    table: str
    owner: str  # user id or owner-team id
    owning_bu: str


@dataclass
class Share:
    record: str
    principal: str
    rights: list[str]


@dataclass
class SecurityModel:
    business_units: dict[str, BusinessUnit]
    users: dict[str, User]
    teams: dict[str, Team]
    roles: dict[str, Role]
    assignments: list[Assignment]
    records: dict[str, Record]
    shares: list[Share]

    @classmethod
    def from_dict(cls, data: dict) -> "SecurityModel":
        bus = {b["id"]: BusinessUnit(b["id"], b.get("parent")) for b in data.get("business_units", [])}
        users = {u["id"]: User(u["id"], u["bu"]) for u in data.get("users", [])}
        teams = {
            t["id"]: Team(t["id"], t["bu"], t.get("type", "owner"), list(t.get("members", [])))
            for t in data.get("teams", [])
        }
        roles = {}
        for r in data.get("roles", []):
            privs = {
                table: {p: normalize_depth(d) for p, d in per.items()}
                for table, per in r.get("privileges", {}).items()
            }
            roles[r["name"]] = Role(r["name"], r.get("inheritance", "direct"), privs)

        def principal_bu(pid: str) -> str:
            if pid in users:
                return users[pid].bu
            if pid in teams:
                return teams[pid].bu
            raise UnknownEntityError(f"unknown principal {pid!r}")

        assignments = [
            Assignment(a["principal"], a["role"], a.get("bu") or principal_bu(a["principal"]))
            for a in data.get("assignments", [])
        ]
        records = {
            r["id"]: Record(r["id"], r["table"], r["owner"], r.get("owning_bu") or principal_bu(r["owner"]))
            for r in data.get("records", [])
        }
        shares = [Share(s["record"], s["principal"], list(s["rights"])) for s in data.get("shares", [])]
        model = cls(bus, users, teams, roles, assignments, records, shares)
        model.validate()
        return model

    @classmethod
    def load(cls, path: str | Path) -> "SecurityModel":
        return cls.from_dict(json.loads(Path(path).read_text()))

    def validate(self) -> None:
        """Reject models Dataverse would never contain. See README "Validation rules".

        TODO: implement every rule in the README table. Raise UnknownEntityError for a
        dangling reference and ValueError for a structurally impossible model.
        """
        return None
