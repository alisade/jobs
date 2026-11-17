"""Security model data structures and loader (reference solution, validate() completed)."""

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
        """Reject models Dataverse would never contain. See README "Validation rules"."""
        roots = [b for b in self.business_units.values() if b.parent is None]
        if len(roots) != 1:
            raise ValueError(f"expected exactly one root business unit, found {len(roots)}")
        for b in self.business_units.values():
            if b.parent is not None and b.parent not in self.business_units:
                raise UnknownEntityError(f"business unit {b.id!r} has unknown parent {b.parent!r}")
        for b in self.business_units.values():
            seen = set()
            cur = b.id
            while cur is not None:
                if cur in seen:
                    raise ValueError(f"business unit hierarchy has a cycle at {cur!r}")
                seen.add(cur)
                cur = self.business_units[cur].parent
        for u in self.users.values():
            if u.bu not in self.business_units:
                raise UnknownEntityError(f"user {u.id!r} is in unknown business unit {u.bu!r}")
        for t in self.teams.values():
            if t.bu not in self.business_units:
                raise UnknownEntityError(f"team {t.id!r} is in unknown business unit {t.bu!r}")
            if t.type not in ("owner", "access"):
                raise ValueError(f"team {t.id!r} has unknown type {t.type!r}")
            for m in t.members:
                if m not in self.users:
                    raise UnknownEntityError(f"team {t.id!r} has unknown member {m!r}")
        for r in self.roles.values():
            if r.inheritance not in ("direct", "team_only"):
                raise ValueError(f"role {r.name!r} has unknown inheritance {r.inheritance!r}")
            for table, per in r.privileges.items():
                for p in per:
                    if p not in PRIVILEGES:
                        raise ValueError(f"role {r.name!r} table {table!r} has unknown privilege {p!r}")
        for a in self.assignments:
            if a.role not in self.roles:
                raise UnknownEntityError(f"assignment references unknown role {a.role!r}")
            if a.bu not in self.business_units:
                raise UnknownEntityError(f"assignment of {a.role!r} references unknown business unit {a.bu!r}")
            if a.principal in self.teams and self.teams[a.principal].type == "access":
                raise ValueError(f"access team {a.principal!r} cannot be assigned security roles")
            if a.principal not in self.users and a.principal not in self.teams:
                raise UnknownEntityError(f"assignment references unknown principal {a.principal!r}")
        for rec in self.records.values():
            if rec.owner in self.teams:
                if self.teams[rec.owner].type == "access":
                    raise ValueError(f"record {rec.id!r} is owned by access team {rec.owner!r}")
            elif rec.owner not in self.users:
                raise UnknownEntityError(f"record {rec.id!r} has unknown owner {rec.owner!r}")
            if rec.owning_bu not in self.business_units:
                raise UnknownEntityError(f"record {rec.id!r} has unknown owning BU {rec.owning_bu!r}")
        for s in self.shares:
            if s.record not in self.records:
                raise UnknownEntityError(f"share references unknown record {s.record!r}")
            if s.principal not in self.users and s.principal not in self.teams:
                raise UnknownEntityError(f"share references unknown principal {s.principal!r}")
            for right in s.rights:
                if right not in SHAREABLE:
                    raise ValueError(f"share on {s.record!r} grants non-shareable right {right!r}")
