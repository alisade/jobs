"""Dataverse record-access evaluator (reference solution).

Rules implemented are the ones stated in README.md ("The security model you must implement").
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import (
    DEPTH_RANK,
    PRIVILEGES,
    SHAREABLE,
    Assignment,
    Record,
    Role,
    SecurityModel,
    UnknownEntityError,
)


@dataclass(frozen=True)
class Grant:
    """One reason a principal holds a privilege on a record."""

    kind: str  # "role" | "team-role" | "share" | "team-share"
    role: str | None  # role name, None for shares
    team: str | None  # team id when the grant comes through a team
    depth: str | None  # depth that matched, None for shares
    scope_bu: str | None  # BU the depth was evaluated against
    detail: str  # human readable one-liner


def _check_privilege(privilege: str) -> None:
    if privilege not in PRIVILEGES:
        raise ValueError(f"unknown privilege {privilege!r}; expected one of {', '.join(PRIVILEGES)}")


def bu_in_subtree(model: SecurityModel, bu: str, root: str) -> bool:
    """True when `bu` is `root` or a descendant of `root`."""
    seen = set()
    cur: str | None = bu
    while cur is not None:
        if cur == root:
            return True
        if cur in seen:  # defensive: cycles are rejected by validate()
            return False
        seen.add(cur)
        cur = model.business_units[cur].parent
    return False


def _depth_covers(
    model: SecurityModel,
    depth: str,
    scope_bu: str,
    record: Record,
    basic_owners: set[str],
) -> bool:
    """Does a privilege at `depth`, evaluated relative to `scope_bu`, reach `record`?

    basic_owners: owner ids that count as "own records" for Basic depth.
    """
    if depth == "Global":
        return True
    if depth == "Deep":
        return bu_in_subtree(model, record.owning_bu, scope_bu)
    if depth == "Local":
        return record.owning_bu == scope_bu
    if depth == "Basic":
        return record.owner in basic_owners
    return False


def _assignments_for(model: SecurityModel, principal: str) -> list[Assignment]:
    return [a for a in model.assignments if a.principal == principal]


def _user_teams(model: SecurityModel, user_id: str) -> list[str]:
    return sorted(t.id for t in model.teams.values() if user_id in t.members)


def _max_depth(model: SecurityModel, user_id: str, table: str, privilege: str) -> int:
    """Highest depth rank the user holds for (table, privilege) from any role path."""
    best = 0
    for a in _assignments_for(model, user_id):
        best = max(best, DEPTH_RANK[model.roles[a.role].depth(table, privilege)])
    for team_id in _user_teams(model, user_id):
        for a in _assignments_for(model, team_id):
            best = max(best, DEPTH_RANK[model.roles[a.role].depth(table, privilege)])
    return best


def explain(model: SecurityModel, user_id: str, privilege: str, record_id: str) -> list[Grant]:
    """Every path that grants `privilege` on `record_id` to `user_id` (empty list = denied)."""
    _check_privilege(privilege)
    if user_id not in model.users:
        raise UnknownEntityError(f"unknown user {user_id!r}")
    if record_id not in model.records:
        raise UnknownEntityError(f"unknown record {record_id!r}")
    record = model.records[record_id]
    table = record.table
    grants: list[Grant] = []

    # 1. Roles assigned directly to the user.
    for a in _assignments_for(model, user_id):
        role: Role = model.roles[a.role]
        depth = role.depth(table, privilege)
        if DEPTH_RANK[depth] == 0:
            continue
        if _depth_covers(model, depth, a.bu, record, {user_id}):
            grants.append(
                Grant("role", role.name, None, depth, a.bu,
                      f"role {role.name} ({depth}) assigned in BU {a.bu}")
            )

    # 2. Roles assigned to owner teams the user belongs to.
    for team_id in _user_teams(model, user_id):
        for a in _assignments_for(model, team_id):
            role = model.roles[a.role]
            depth = role.depth(table, privilege)
            if DEPTH_RANK[depth] == 0:
                continue
            owners = {team_id}
            if role.inheritance == "direct":
                owners.add(user_id)
            if _depth_covers(model, depth, a.bu, record, owners):
                grants.append(
                    Grant("team-role", role.name, team_id, depth, a.bu,
                          f"team {team_id} role {role.name} ({depth}) assigned in BU {a.bu}")
                )

    # 3. Shares. Effective only when the user holds the privilege at Basic or deeper.
    if privilege in SHAREABLE and _max_depth(model, user_id, table, privilege) >= DEPTH_RANK["Basic"]:
        for s in model.shares:
            if s.record != record_id or privilege not in s.rights:
                continue
            if s.principal == user_id:
                grants.append(Grant("share", None, None, None, None,
                                    f"record shared with user {user_id} ({', '.join(s.rights)})"))
            elif s.principal in model.teams and user_id in model.teams[s.principal].members:
                grants.append(Grant("team-share", None, s.principal, None, None,
                                    f"record shared with team {s.principal} ({', '.join(s.rights)})"))
    return grants


def can(model: SecurityModel, user_id: str, privilege: str, record_id: str) -> bool:
    return bool(explain(model, user_id, privilege, record_id))


def can_associate(model: SecurityModel, user_id: str, child_id: str, parent_id: str) -> bool:
    """Attach child to parent (e.g. a note to a work order): Append on child, Append To on parent."""
    return can(model, user_id, "Append", child_id) and can(model, user_id, "AppendTo", parent_id)
