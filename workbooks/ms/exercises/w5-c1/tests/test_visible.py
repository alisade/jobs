"""Visible tests: the four access levels on the Tailspin production model."""

from pathlib import Path

import pytest

from dvaccess import SecurityModel, can, explain

DATA = Path(__file__).resolve().parent.parent / "data" / "tailspin.json"


@pytest.fixture(scope="module")
def model():
    return SecurityModel.load(DATA)


def test_basic_depth_reads_own_record(model):
    assert can(model, "lena.tech", "Read", "wo-1002")


def test_basic_depth_cannot_read_colleague_record(model):
    # lena (Technician, Basic read) does not own wo-1006
    assert not can(model, "lena.tech", "Read", "wo-1006")


def test_local_depth_reads_records_in_own_bu(model):
    # maria (Dispatcher, Local read, BU west) reads tomas's west work order
    assert can(model, "maria.dispatch", "Read", "wo-1006")


def test_local_depth_does_not_reach_child_bu(model):
    # wo-1004 is owned by sam in west-seattle, a CHILD of west
    assert not can(model, "maria.dispatch", "Read", "wo-1004")


def test_deep_depth_reaches_child_bus(model):
    # raj (Regional Manager, Deep, BU field-ops) reads west-seattle and east
    assert can(model, "raj.manager", "Read", "wo-1004")
    assert can(model, "raj.manager", "Read", "wo-1002")


def test_global_depth_reads_everything(model):
    for rec in ("wo-1001", "wo-1002", "wo-1003", "wo-1004"):
        assert can(model, "olga.audit", "Read", rec)


def test_privilege_without_role_is_denied(model):
    # olga can read everything but has no Write at all
    assert not can(model, "olga.audit", "Write", "wo-1001")


def test_explain_names_the_role(model):
    grants = explain(model, "maria.dispatch", "Read", "wo-1006")
    assert any(g.kind == "role" and g.role == "Dispatcher" and g.depth == "Local" for g in grants)
