import csv
import pathlib
import re
import sqlite3

import pytest

from keystone_import.ids import canonical_id
from keystone_import.importer import import_export
from keystone_import.recon import build_report

SUFFIX = "ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"


def ref18(id15):
    out = ""
    for c in range(3):
        bits = sum(1 << i for i, ch in enumerate(id15[c * 5:c * 5 + 5]) if "A" <= ch <= "Z")
        out += SUFFIX[bits]
    return id15 + out


def rows(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.mark.parametrize("id15", ["001Hs0000001abc", "001Hs0000001ABC", "003HsQqQqQ12345", "a0D30000001n7Pi", "00THsaaaaaaaaaa"])
def test_canonical_id_converts_15_to_18(id15):
    assert canonical_id(id15) == ref18(id15)
    assert canonical_id(ref18(id15)) == ref18(id15)
    assert canonical_id("  " + id15 + " ") == ref18(id15)


def test_case_distinct_15_char_ids_stay_distinct():
    assert canonical_id("001Hs0000001abc") != canonical_id("001Hs0000001abC")


def test_invalid_length_is_rejected():
    with pytest.raises(ValueError):
        canonical_id("001Hs00")


def test_every_account_imported_once(imported):
    export, db = imported
    con = sqlite3.connect(db)
    n = con.execute("SELECT count(*) FROM accounts").fetchone()[0]
    assert n == 1197
    ids = {r[0] for r in con.execute("SELECT sf_id18 FROM accounts")}
    src = {r["Id"] for r in rows(export / "Account.csv") if r["Name"].strip()}
    assert ids == src


def test_contacts_link_to_the_exact_account(imported):
    export, db = imported
    con = sqlite3.connect(db)
    got = dict(con.execute("SELECT c.sf_id18, a.sf_id18 FROM contacts c JOIN accounts a ON a.pk = c.account_pk"))
    wrong = 0
    checked = 0
    for path in (export / "Contact.csv", export / "partner_portal" / "Contact.csv"):
        for r in rows(path):
            want = ref18(r["AccountId"]) if len(r["AccountId"]) == 15 else r["AccountId"]
            if r["Id"] in got:
                checked += 1
                wrong += got[r["Id"]] != want
    assert checked > 3400 and wrong == 0


def test_partner_portal_contacts_imported(imported):
    export, db = imported
    con = sqlite3.connect(db)
    n = con.execute("SELECT count(*) FROM contacts WHERE source = 'partner_portal'").fetchone()[0]
    assert n >= 395


def test_recon_is_clean_and_lists_rejects(imported):
    export, db = imported
    rep = build_report(export, db)
    assert rep["unexplained"] == 0
    assert all(o["count_match"] and o["checksum_match"] for o in rep["objects"].values())
    reasons = {r["reason"] for r in rep["rejects"] if r["object"] == "Account"}
    assert any("Name" in x for x in reasons)


def test_rerun_is_idempotent(bundle, tmp_path):
    db = tmp_path / "k.sqlite"
    import_export(bundle / "export", db)
    import_export(bundle / "export", db)
    con = sqlite3.connect(db)
    assert con.execute("SELECT count(*) FROM accounts").fetchone()[0] == 1197
    assert build_report(bundle / "export", db)["unexplained"] == 0


def test_answer_names_the_case_sensitive_collision():
    text = (pathlib.Path(__file__).resolve().parent.parent / "ANSWER.md").read_text().lower()
    assert re.search(r"case[- ]?(in)?sensitiv", text)
    assert re.search(r"collid|collision|merg", text)
