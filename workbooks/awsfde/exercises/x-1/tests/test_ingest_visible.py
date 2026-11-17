"""Visible checks for x-1 (happy path). The grader runs more."""

from x1_support import batch, job_response, jobs, s3_event, sqs_record

from ingest.handler import handler


def test_one_upload_starts_one_job(table, agent):
    agent.stub.add_response("start_ingestion_job", job_response())
    out = handler(batch(sqs_record("m-1", s3_event("tenants/acme-foods/docs/returns-policy.pdf"))), table=table, agent=agent.client)
    assert out == {"batchItemFailures": []}
    js = jobs(table)
    assert len(js) == 1 and js[0]["status"] == "STARTED" and js[0]["pk"] == "TENANT#acme-foods"


def test_same_event_three_times_one_job(table, agent):
    agent.stub.add_response("start_ingestion_job", job_response())
    ev = s3_event("tenants/acme-foods/docs/returns-policy.pdf")
    for i in range(3):
        handler(batch(sqs_record(f"m-{i}", ev)), table=table, agent=agent.client)
    assert len(jobs(table)) == 1
    agent.stub.assert_no_pending_responses()
