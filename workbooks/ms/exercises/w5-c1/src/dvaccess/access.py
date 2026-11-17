"""Dataverse record-access evaluator.

Implement the rules in README.md ("The security model you must implement").
Keep the public signatures: the tests import Grant, bu_in_subtree, explain, can, can_associate.
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import (  # noqa: F401  (you will need most of these)
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
    depth: str | None  # depth that matched ("Basic".."Global"), None for shares
    scope_bu: str | None  # BU the depth was evaluated against, None for shares
    detail: str  # human readable one-liner for the support engineer


def bu_in_subtree(model: SecurityModel, bu: str, root: str) -> bool:
    """True when `bu` is `root` or any descendant of `root`."""
    # TODO
    raise NotImplementedError


def explain(model: SecurityModel, user_id: str, privilege: str, record_id: str) -> list[Grant]:
    """Every path that grants `privilege` on `record_id` to `user_id`.

    An empty list means access is denied. Raise ValueError for an unknown privilege and
    UnknownEntityError for an unknown user or record.
    """
    # TODO: 1) roles assigned to the user, 2) roles of owner teams the user is in,
    #       3) shares to the user or to a team the user is in.
    raise NotImplementedError


def can(model: SecurityModel, user_id: str, privilege: str, record_id: str) -> bool:
    # TODO
    raise NotImplementedError


def can_associate(model: SecurityModel, user_id: str, child_id: str, parent_id: str) -> bool:
    """Attach child to parent, e.g. a note (annotation) to a work order."""
    # TODO
    raise NotImplementedError
