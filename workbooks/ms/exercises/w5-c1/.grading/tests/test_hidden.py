"""Hidden tests for ms/w5-c1: depths, teams, shares, modern BUs, append, explain, validation."""

import copy
from pathlib import Path

import pytest

from dvaccess import SecurityModel, UnknownEntityError, bu_in_subtree, can, can_associate, explain

DATA = Path(__file__).resolve().parents[2] / "data" / "tailspin.json"


@pytest.fixture(scope="module")
def model():
    return SecurityModel.load(DATA)


def base():
    return {
        "business_units": [
            {"id": "root", "parent": None},
            {"id": "a", "parent": "root"},
            {"id": "a1", "parent": "a"},
            {"id": "a11", "parent": "a1"},
            {"id": "b", "parent": "root"},
        ],
        "users": [
            {"id": "u1", "bu": "a"},
            {"id": "u2", "bu": "a"},
            {"id": "u3", "bu": "b"},
        ],
        "teams": [],
        "roles": [],
        "assignments": [],
        "records": [],
        "shares": [],
    }


# ---------- business unit tree ----------

def test_bu_in_subtree(model):
    assert bu_in_subtree(model, "west-seattle", "field-ops")
    assert bu_in_subtree(model, "west", "west")
    assert not bu_in_subtree(model, "west", "west-seattle")
    assert not bu_in_subtree(model, "finance", "field-ops")


def test_deep_reaches_grandchild_but_not_sibling():
    d = base()
    d["roles"] = [{"name": "Mgr", "privileges": {"t": {"Read": "Deep"}}}]
    d["assignments"] = [{"principal": "u1", "role": "Mgr"}]
    d["records"] = [
        {"id": "r-a11", "table": "t", "owner": "u2", "owning_bu": "a11"},
        {"id": "r-b", "table": "t", "owner": "u3"},
        {"id": "r-root", "table": "t", "owner": "u3", "owning_bu": "root"},
    ]
    m = SecurityModel.from_dict(d)
    assert can(m, "u1", "Read", "r-a11")
    assert not can(m, "u1", "Read", "r-b")
    assert not can(m, "u1", "Read", "r-root"), "Deep never reaches the PARENT business unit"


def test_depth_aliases_from_role_editor():
    d = base()
    d["roles"] = [{"name": "R", "privileges": {"t": {"Read": "Business Unit", "Write": "User"}}}]
    d["assignments"] = [{"principal": "u1", "role": "R"}]
    d["records"] = [{"id": "r", "table": "t", "owner": "u2"}]
    m = SecurityModel.from_dict(d)
    assert can(m, "u1", "Read", "r")
    assert not can(m, "u1", "Write", "r")


def test_owning_bu_not_owner_bu_decides_local():
    # Record owned by u2 (BU a) but owning BU explicitly a1 (record ownership across BUs).
    d = base()
    d["roles"] = [{"name": "R", "privileges": {"t": {"Read": "Local"}}}]
    d["assignments"] = [{"principal": "u1", "role": "R"}]
    d["records"] = [{"id": "r", "table": "t", "owner": "u2", "owning_bu": "a1"}]
    m = SecurityModel.from_dict(d)
    assert not can(m, "u1", "Read", "r")


def test_privileges_are_per_table(model):
    # maria's Dispatcher role grants Local read on work orders but only Basic read on notes
    assert not can(model, "maria.dispatch", "Write", "wo-1006")
    assert can(model, "maria.dispatch", "Read", "note-77")


def test_roles_are_cumulative():
    d = base()
    d["roles"] = [
        {"name": "Narrow", "privileges": {"t": {"Read": "Basic"}}},
        {"name": "Wide", "privileges": {"t": {"Read": "Global"}}},
    ]
    d["assignments"] = [{"principal": "u1", "role": "Narrow"}, {"principal": "u1", "role": "Wide"}]
    d["records"] = [{"id": "r", "table": "t", "owner": "u3"}]
    m = SecurityModel.from_dict(d)
    assert can(m, "u1", "Read", "r")
    roles = {g.role for g in explain(m, "u1", "Read", "r")}
    assert roles == {"Wide"}


# ---------- modern business units ----------

def test_modern_bu_role_applies_relative_to_assigned_bu(model):
    # priya sits in finance but holds Dispatcher assigned FROM east (Local read)
    assert can(model, "priya.finance", "Read", "wo-1002")
    assert not can(model, "priya.finance", "Read", "wo-1001")
    g = explain(model, "priya.finance", "Read", "wo-1002")
    assert any(x.scope_bu == "east" and x.depth == "Local" for x in g)


def test_modern_bu_basic_still_means_own_records():
    d = base()
    d["roles"] = [{"name": "R", "privileges": {"t": {"Read": "Basic"}}}]
    d["assignments"] = [{"principal": "u3", "role": "R", "bu": "a"}]
    d["records"] = [
        {"id": "mine", "table": "t", "owner": "u3", "owning_bu": "a"},
        {"id": "theirs", "table": "t", "owner": "u1"},
    ]
    m = SecurityModel.from_dict(d)
    assert can(m, "u3", "Read", "mine")
    assert not can(m, "u3", "Read", "theirs")


# ---------- owner teams ----------

def test_team_owned_record_via_team_role(model):
    # tomas is in west-dispatch-pool, which owns wo-1003 and has Basic read
    assert can(model, "tomas.tech", "Read", "wo-1003")
    g = explain(model, "tomas.tech", "Read", "wo-1003")
    assert any(x.kind == "team-role" and x.team == "west-dispatch-pool" and x.role == "Dispatch Pool" for x in g)


def test_users_own_basic_role_does_not_cover_team_records():
    d = base()
    d["teams"] = [{"id": "T", "bu": "a", "type": "owner", "members": ["u1"]}]
    d["roles"] = [{"name": "Own", "privileges": {"t": {"Read": "Basic"}}}]
    d["assignments"] = [{"principal": "u1", "role": "Own"}]
    d["records"] = [{"id": "r", "table": "t", "owner": "T"}]
    m = SecurityModel.from_dict(d)
    assert not can(m, "u1", "Read", "r")


def test_team_only_inheritance_does_not_cover_members_own_records():
    d = base()
    d["teams"] = [{"id": "T", "bu": "a", "type": "owner", "members": ["u1"]}]
    d["roles"] = [{"name": "TeamRole", "inheritance": "team_only", "privileges": {"t": {"Read": "Basic"}}}]
    d["assignments"] = [{"principal": "T", "role": "TeamRole"}]
    d["records"] = [
        {"id": "team-rec", "table": "t", "owner": "T"},
        {"id": "own-rec", "table": "t", "owner": "u1"},
    ]
    m = SecurityModel.from_dict(d)
    assert can(m, "u1", "Read", "team-rec")
    assert not can(m, "u1", "Read", "own-rec")


def test_direct_inheritance_covers_members_own_records():
    d = base()
    d["teams"] = [{"id": "T", "bu": "a", "type": "owner", "members": ["u1"]}]
    d["roles"] = [{"name": "TeamRole", "inheritance": "direct", "privileges": {"t": {"Read": "Basic"}}}]
    d["assignments"] = [{"principal": "T", "role": "TeamRole"}]
    d["records"] = [
        {"id": "team-rec", "table": "t", "owner": "T"},
        {"id": "own-rec", "table": "t", "owner": "u1"},
        {"id": "other-rec", "table": "t", "owner": "u2"},
    ]
    m = SecurityModel.from_dict(d)
    assert can(m, "u1", "Read", "team-rec")
    assert can(m, "u1", "Read", "own-rec")
    assert not can(m, "u1", "Read", "other-rec")


def test_team_local_role_uses_team_bu_not_member_bu():
    d = base()
    d["teams"] = [{"id": "T", "bu": "b", "type": "owner", "members": ["u1"]}]
    d["roles"] = [{"name": "TeamLocal", "privileges": {"t": {"Read": "Local"}}}]
    d["assignments"] = [{"principal": "T", "role": "TeamLocal"}]
    d["records"] = [
        {"id": "in-b", "table": "t", "owner": "u3"},
        {"id": "in-a", "table": "t", "owner": "u2"},
    ]
    m = SecurityModel.from_dict(d)
    assert can(m, "u1", "Read", "in-b")
    assert not can(m, "u1", "Read", "in-a")


def test_non_member_gets_nothing_from_team(model):
    assert not can(model, "lena.tech", "Read", "wo-1003")


# ---------- sharing ----------

def test_share_to_user_grants_only_shared_rights(model):
    # wo-1005 (east, lena) shared with maria for Read only
    assert can(model, "maria.dispatch", "Read", "wo-1005")
    assert not can(model, "maria.dispatch", "Write", "wo-1005")
    g = explain(model, "maria.dispatch", "Read", "wo-1005")
    assert [x.kind for x in g] == ["share"]


def test_share_to_access_team_reaches_members(model):
    # sam is in the access team wo-1005-collab (Read, Write) and has Technician Basic read/write
    assert can(model, "sam.tech", "Write", "wo-1005")
    g = explain(model, "sam.tech", "Write", "wo-1005")
    assert any(x.kind == "team-share" and x.team == "wo-1005-collab" for x in g)


def test_share_needs_at_least_basic_privilege():
    d = base()
    d["roles"] = [{"name": "ReadOnly", "privileges": {"t": {"Read": "Basic"}}}]
    d["assignments"] = [{"principal": "u3", "role": "ReadOnly"}]
    d["records"] = [{"id": "r", "table": "t", "owner": "u1"}]
    d["shares"] = [{"record": "r", "principal": "u3", "rights": ["Read", "Write"]}]
    m = SecurityModel.from_dict(d)
    assert can(m, "u3", "Read", "r")
    assert not can(m, "u3", "Write", "r"), "share of Write is ineffective without a Write privilege"


def test_share_to_other_record_does_not_leak():
    d = base()
    d["roles"] = [{"name": "R", "privileges": {"t": {"Read": "Basic"}}}]
    d["assignments"] = [{"principal": "u3", "role": "R"}]
    d["records"] = [
        {"id": "r1", "table": "t", "owner": "u1"},
        {"id": "r2", "table": "t", "owner": "u1"},
    ]
    d["shares"] = [{"record": "r1", "principal": "u3", "rights": ["Read"]}]
    m = SecurityModel.from_dict(d)
    assert can(m, "u3", "Read", "r1")
    assert not can(m, "u3", "Read", "r2")


# ---------- append / append to ----------

def test_can_associate_needs_append_on_child_and_append_to_on_parent(model):
    # maria: Append (Basic) on her note, AppendTo (Local) on west work orders
    assert can_associate(model, "maria.dispatch", "note-77", "wo-1006")
    # wo-1002 is in east: no AppendTo there
    assert not can_associate(model, "maria.dispatch", "note-77", "wo-1002")


def test_append_to_alone_is_not_enough():
    d = base()
    d["roles"] = [{"name": "R", "privileges": {"t": {"AppendTo": "Global"}, "annotation": {"Read": "Basic"}}}]
    d["assignments"] = [{"principal": "u1", "role": "R"}]
    d["records"] = [
        {"id": "parent", "table": "t", "owner": "u2"},
        {"id": "note", "table": "annotation", "owner": "u1"},
    ]
    m = SecurityModel.from_dict(d)
    assert not can_associate(m, "u1", "note", "parent")
    assert can(m, "u1", "AppendTo", "parent")
    assert not can(m, "u1", "Append", "note")


# ---------- explain ----------

def test_explain_lists_every_granting_path():
    d = base()
    d["teams"] = [{"id": "T", "bu": "a", "type": "owner", "members": ["u1"]}]
    d["roles"] = [
        {"name": "Own", "privileges": {"t": {"Read": "Local"}}},
        {"name": "TeamRole", "privileges": {"t": {"Read": "Basic"}}},
    ]
    d["assignments"] = [{"principal": "u1", "role": "Own"}, {"principal": "T", "role": "TeamRole"}]
    d["records"] = [{"id": "r", "table": "t", "owner": "T"}]
    d["shares"] = [{"record": "r", "principal": "u1", "rights": ["Read"]}]
    m = SecurityModel.from_dict(d)
    kinds = sorted(g.kind for g in explain(m, "u1", "Read", "r"))
    assert kinds == ["role", "share", "team-role"]


def test_explain_empty_when_denied(model):
    assert explain(model, "lena.tech", "Read", "wo-1001") == []


def test_explain_detail_is_human_readable(model):
    g = explain(model, "raj.manager", "Read", "wo-1004")
    assert g and all(isinstance(x.detail, str) and len(x.detail) > 10 for x in g)
    assert g[0].scope_bu == "field-ops" and g[0].depth == "Deep"


# ---------- errors and validation ----------

def test_unknown_user_record_privilege(model):
    with pytest.raises(UnknownEntityError):
        can(model, "nobody", "Read", "wo-1001")
    with pytest.raises(UnknownEntityError):
        can(model, "maria.dispatch", "Read", "wo-9999")
    with pytest.raises(ValueError):
        can(model, "maria.dispatch", "Approve", "wo-1001")


def test_create_cannot_be_shared():
    d = base()
    d["records"] = [{"id": "r", "table": "t", "owner": "u1"}]
    d["shares"] = [{"record": "r", "principal": "u2", "rights": ["Create"]}]
    with pytest.raises(ValueError):
        SecurityModel.from_dict(d)


def test_access_team_cannot_hold_roles_or_own_records():
    d = base()
    d["teams"] = [{"id": "AT", "bu": "a", "type": "access", "members": ["u1"]}]
    d["roles"] = [{"name": "R", "privileges": {}}]
    d1 = copy.deepcopy(d)
    d1["assignments"] = [{"principal": "AT", "role": "R"}]
    with pytest.raises(ValueError):
        SecurityModel.from_dict(d1)
    d2 = copy.deepcopy(d)
    d2["records"] = [{"id": "r", "table": "t", "owner": "AT"}]
    with pytest.raises(ValueError):
        SecurityModel.from_dict(d2)


def test_dangling_references_rejected():
    d = base()
    d["assignments"] = [{"principal": "u1", "role": "Ghost"}]
    with pytest.raises(UnknownEntityError):
        SecurityModel.from_dict(d)
    d = base()
    d["users"].append({"id": "u9", "bu": "nowhere"})
    with pytest.raises(UnknownEntityError):
        SecurityModel.from_dict(d)
    d = base()
    d["teams"] = [{"id": "T", "bu": "a", "members": ["ghost"]}]
    with pytest.raises(UnknownEntityError):
        SecurityModel.from_dict(d)


def test_bu_hierarchy_must_have_one_root_and_no_cycles():
    d = base()
    d["business_units"].append({"id": "root2", "parent": None})
    with pytest.raises(ValueError):
        SecurityModel.from_dict(d)
    d = base()
    d["business_units"] = [
        {"id": "root", "parent": None},
        {"id": "x", "parent": "y"},
        {"id": "y", "parent": "x"},
    ]
    d["users"] = []
    with pytest.raises(ValueError):
        SecurityModel.from_dict(d)
