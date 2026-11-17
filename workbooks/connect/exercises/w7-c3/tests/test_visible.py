"""Visible tests for connect/w7-c3. The grader adds more."""
from helpers import decoded_rows, duck, firehose_event, load_module, sample_ctrs


def test_every_record_id_is_echoed_with_a_result():
    t = load_module()
    ev = firehose_event(sample_ctrs()[:10])
    out = t.lambda_handler(ev, None)
    assert [r["recordId"] for r in out["records"]] == [r["recordId"] for r in ev["records"]]
    assert all(r["result"] in ("Ok", "Dropped", "ProcessingFailed") for r in out["records"])


def test_rows_are_newline_delimited_json():
    import base64

    t = load_module()
    out = t.lambda_handler(firehose_event(sample_ctrs()[:3]), None)
    for r in out["records"]:
        assert base64.b64decode(r["data"]).decode().endswith("\n")


def test_queue_daily_view_exists_and_counts_offered():
    t = load_module()
    rows = decoded_rows(t.lambda_handler(firehose_event(sample_ctrs()), None))
    con = duck(rows)
    total = con.execute("SELECT SUM(offered) FROM queue_daily").fetchone()[0]
    assert total == sum(1 for r in rows if r["queue_name"])
