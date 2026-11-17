import sqlite3

from keystone_import.recon import build_report


def test_import_runs_and_rejects_nameless_accounts(imported):
    export, db = imported
    con = sqlite3.connect(db)
    rejected = con.execute("SELECT count(*) FROM rejects WHERE object = 'Account' AND reason LIKE '%Name%'").fetchone()[0]
    assert rejected == 3


def test_reconciliation_has_no_unexplained_mismatches(imported):
    export, db = imported
    report = build_report(export, db)
    assert report["objects"]["Account"]["count_match"], report["objects"]["Account"]
    assert report["unexplained"] == 0
