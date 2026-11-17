"""Visible checks: shape, honest evidence, and a few facts anyone would find in an hour."""

import json

import jsonschema
import pytest

import inventory_check as ic


@pytest.fixture(scope="module")
def inv():
    return ic.load()


def test_matches_schema(inv):
    jsonschema.validate(inv, json.loads(ic.SCHEMA.read_text()))


@pytest.mark.parametrize("section", ic.SECTIONS)
def test_section_not_empty(inv, section):
    assert inv[section], f"{section} is empty"


def test_every_evidence_reference_resolves(inv):
    problems = ic.evidence_problems(inv)
    assert not problems, "\n".join(problems[:15])


def test_claim_table_found(inv):
    assert "CLAIM" in {ic.db_key(i) for i in inv["db_objects"]}


def test_admin_constraint_found(inv):
    roles = {a["role"].upper(): a for a in inv["auth_checks"]}
    assert "CLAIMS_ADMIN" in roles
    assert "web.xml" in ic.files_of(roles["CLAIMS_ADMIN"])
